# -*- coding: utf-8 -*-

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Windows platform implementation."""

from __future__ import division

import collections
import ctypes
import errno
import functools
import os
import platform
import socket
import sys
import time

from . import _common
from . import _psutil_windows as cext
from ._common import AccessDenied
from ._common import conn_to_ntuple
from ._common import deprecated_method
from ._common import FREEBSD
from ._common import LINUX
from ._common import MACOS
from ._common import NoSuchProcess
from ._common import nt_proc_conn
from ._common import nt_proc_ctxsw
from ._common import nt_proc_gids
from ._common import nt_proc_io
from ._common import nt_proc_mem_ext
from ._common import nt_proc_meminfo
from ._common import nt_proc_openfile
from ._common import nt_proc_thread
from ._common import nt_proc_uids
from ._common import nt_sys_addr
from ._common import nt_sys_disk_io_counter
from ._common import nt_sys_diskpart
from ._common import nt_sys_if_stats
from ._common import nt_sys_net_io_counter
from ._common import nt_sys_swap
from ._common import nt_sys_user
from ._common import nt_sys_vmem
from ._common import OPENBSD
from ._common import usage_percent
from ._common import ZombieProcess
from ._compat import long
from ._compat import PY3
from ._compat import range

try:
    from socket import AF_LINK
except ImportError:
    AF_LINK = -1


__extra__all__ = [
    # process class
    "ABOVE_NORMAL_PRIORITY_CLASS", "BELOW_NORMAL_PRIORITY_CLASS",
    "HIGH_PRIORITY_CLASS", "IDLE_PRIORITY_CLASS", "NORMAL_PRIORITY_CLASS",
    "REALTIME_PRIORITY_CLASS", "CONN_DELETE_TCB",
    # functions
    "win_service_iter", "win_service_get",
    # classes
    "WindowsService",
]

# --- module level constants

CONN_DELETE_TCB = "DELETE_TCB"
POWER_TIME_UNLIMITED = -1
POWER_TIME_UNKNOWN = -2

# --- named tuples

nt_sys_cputimes = collections.namedtuple(
    'scputimes', ['user', 'system', 'idle', 'interrupt', 'dpc'])
nt_sys_cputimes.user.__doc__ = \
    "time spent by normal processes executing in user mode"
nt_sys_cputimes.system.__doc__ = \
    "time spent by processes executing in kernel mode"
nt_sys_cputimes.idle.__doc__ = "time spent in the idle task"
nt_sys_cputimes.interrupt.__doc__ = \
    "time spent servicing hardware interrupts"
nt_sys_cputimes.dpc.__doc__ = \
    "time spent servicing deferred procedure calls"

nt_sys_cpu_stats = collections.namedtuple(
    'scpustats', ['ctx_switches', 'interrupts', 'dpc', 'syscalls'])
nt_sys_cpu_stats.ctx_switches.__doc__ = \
    "number of context switches (voluntary + involuntary) since boot"
nt_sys_cpu_stats.interrupts.__doc__ = "number of interrupts since boot"
nt_sys_cpu_stats.dpc.__doc__ = "number of DPCs since boot"
nt_sys_cpu_stats.syscalls.__doc__ = "number of system calls since boot"

nt_sys_cpu_freq = collections.namedtuple(
    'scpufreq', ['current', 'min', 'max'])
nt_sys_cpu_freq.current.__doc__ = "current CPU frequency in Mhz"
nt_sys_cpu_freq.min.__doc__ = "minimum CPU frequency in Mhz"
nt_sys_cpu_freq.max.__doc__ = "maximum CPU frequency in Mhz"

nt_sys_battery = collections.namedtuple(
    'sbattery', ['percent', 'secsleft', 'power_plugged'])
nt_sys_battery.percent.__doc__ = "battery power left as a percentage"
nt_sys_battery.secsleft.__doc__ = \
    "a rough approximation of how many seconds are left before the " \
    "battery runs out of power. May be POWER_TIME_UNLIMITED or " \
    "POWER_TIME_UNKNOWN."
nt_sys_battery.power_plugged.__doc__ = \
    "True if the AC power source is online, False if it's on battery" \
    "power, None if it's unknown."

nt_proc_cpu = collections.namedtuple(
    'pcputimes', ['user', 'system'])
nt_proc_cpu.user.__doc__ = "user time"
nt_proc_cpu.system.__doc__ = "system time"

# --- internal utils

# A map between socket status constants and a human readable string.
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa394071(v=vs.85).aspx
TCP_STATUSES = {
    cext.MIB_TCP_STATE_CLOSED: _common.CONN_CLOSE,
    cext.MIB_TCP_STATE_LISTEN: _common.CONN_LISTEN,
    cext.MIB_TCP_STATE_SYN_SENT: _common.CONN_SYN_SENT,
    cext.MIB_TCP_STATE_SYN_RCVD: _common.CONN_SYN_RECV,
    cext.MIB_TCP_STATE_ESTAB: _common.CONN_ESTABLISHED,
    cext.MIB_TCP_STATE_FIN_WAIT1: _common.CONN_FIN_WAIT1,
    cext.MIB_TCP_STATE_FIN_WAIT2: _common.CONN_FIN_WAIT2,
    cext.MIB_TCP_STATE_CLOSE_WAIT: _common.CONN_CLOSE_WAIT,
    cext.MIB_TCP_STATE_CLOSING: _common.CONN_CLOSING,
    cext.MIB_TCP_STATE_LAST_ACK: _common.CONN_LAST_ACK,
    cext.MIB_TCP_STATE_TIME_WAIT: _common.CONN_TIME_WAIT,
    cext.MIB_TCP_STATE_DELETE_TCB: CONN_DELETE_TCB,
    cext.MIB_TCP_STATE_RESERVED: _common.CONN_NONE,
}


def _win32_QueryDosDevice(s):
    """A wrapper around QueryDosDevice C function."""
    if not isinstance(s, bytes):
        s = s.encode('utf8')
    n = 260
    while True:
        buf = ctypes.create_string_buffer(n)
        if cext.win32_QueryDosDevice(s, buf, n) != 0:
            return buf.value.decode('utf8')
        else:
            err = ctypes.GetLastError()
            if err == cext.ERROR_INSUFFICIENT_BUFFER:
                n *= 2
            else:
                raise ctypes.WinError(err)


def _convert_cpu_times(procs, cpus):
    """Convert a list of raw CPU times into a list of Process instances.
    'procs' is a list of (pid, user_time, system_time) tuples.
    'cpus' is a list of (user_time, system_time, idle_time,
    interrupt_time, dpc_time) tuples.
    """
    ret = []
    for proc in procs:
        pid, user, system = proc
        p = Process(pid)
        p._user_time = user
        p._system_time = system
        ret.append(p)
    return ret


def _set_proc_cpu_times(procs):
    """Set user and system CPU times for a list of processes."""
    for p in procs:
        try:
            p.cpu_times()
        except NoSuchProcess:
            pass


def _is_zombie(pid):
    """Return True if a process is a zombie, False otherwise."""
    # See:
    # https://github.com/giampaolo/psutil/issues/411
    # https://github.com/giampaolo/psutil/issues/595
    # https://github.com/giampaolo/psutil/issues/1020
    if pid == 0:
        return False
    try:
        proc = cext.open_process(pid, cext.PROCESS_QUERY_LIMITED_INFORMATION)
    except OSError as err:
        if err.winerror == cext.ERROR_INVALID_PARAMETER:
            # This is the error code we get when the process is gone.
            return False
        elif err.winerror == cext.ERROR_ACCESS_DENIED:
            # We can't determine the exit code so we assume it's not a zombie.
            return False
        else:
            raise
    else:
        with contextlib.closing(proc):
            code = cext.get_exit_code_process(proc)
            if code == cext.STILL_ACTIVE:
                return False
            return True


# =====================================================================
# --- system APIs
# =====================================================================


def virtual_memory():
    """System virtual memory as a namedtuple."""
    mem = cext.virtual_memory()
    # 'available' is what other platforms use and it's a better concept
    # than 'free' (see GHI #581), so we want to provide it also on
    # Windows.
    # It's a bit of a guess, see:
    # http://stackoverflow.com/questions/11333741
    # It must be noted that on Windows 'free' memory is almost
    # always 0, see:
    # http://stackoverflow.com/questions/8777322
    # For this reason on Windows we return available and free memory
    # as the same value.
    # For what other tools do, see:
    # - taskmgr: "Available"
    # - perfmon: "Available MBytes"
    # - process explorer: "Available"
    # All of them match this value.
    # For a deeper discussion see:
    # https://github.com/giampaolo/psutil/issues/581
    # https://github.com/giampaolo/psutil/issues/849
    # https://github.com/giampaolo/psutil/issues/1083
    # https://github.com/giampaolo/psutil/pull/1088
    total, available, percent, used, free = mem
    return nt_sys_vmem(
        total, available, percent, used, free,
        active=0, inactive=0, buffers=0, cached=0, shared=0, slab=0)


def swap_memory():
    """Swap system memory as a namedtuple."""
    return nt_sys_swap(*cext.swap_memory())


def cpu_times(percpu=False):
    """Return system-wide CPU times as a named tuple."""
    if not percpu:
        user, system, idle, interrupt, dpc = cext.cpu_times()
        return nt_sys_cputimes(user, system, idle, interrupt, dpc)
    else:
        ret = []
        for cpu_t in cext.per_cpu_times():
            user, system, idle, interrupt, dpc = cpu_t
            item = nt_sys_cputimes(user, system, idle, interrupt, dpc)
            ret.append(item)
        return ret


def cpu_percent(interval=None, percpu=False):
    """Return a float representing the current system-wide CPU
    utilization as a percentage.
    """
    if percpu:
        # Note: when percpu is True, the first call returns a list of
        # 0.0 values.
        # This is not ideal but it's what other platforms do.
        # See: https://github.com/giampaolo/psutil/issues/1040
        def get_stat(cpu_num):
            return cext.cpu_times_percent(cpu_num)
        return [get_stat(i) for i in range(cpu_count())]
    else:
        # Note: the first call returns 0.0.
        # This is not ideal but it's what other platforms do.
        # See: https://github.com/giampaolo/psutil/issues/1040
        return cext.cpu_times_percent(-1)


def cpu_times_percent(interval=None, percpu=False):
    """Return system-wide CPU times as a named tuple."""
    if percpu:
        # Note: when percpu is True, the first call returns a list of
        # 0.0 values.
        # This is not ideal but it's what other platforms do.
        # See: https://github.com/giampaolo/psutil/issues/1040
        def get_stat(cpu_num):
            user, system, idle, interrupt, dpc = cext.cpu_times_percent(cpu_num)
            return nt_sys_cputimes(user, system, idle, interrupt, dpc)
        return [get_stat(i) for i in range(cpu_count())]
    else:
        # Note: the first call returns 0.0.
        # This is not ideal but it's what other platforms do.
        # See: https://github.com/giampaolo/psutil/issues/1040
        user, system, idle, interrupt, dpc = cext.cpu_times_percent(-1)
        return nt_sys_cputimes(user, system, idle, interrupt, dpc)


def cpu_count(logical=True):
    """Return the number of CPUs on the system."""
    if logical:
        return cext.cpu_count_logical()
    else:
        return cext.cpu_count_physical()


def cpu_stats():
    """Return CPU statistics."""
    ctx, inter, dpcs, sysc = cext.cpu_stats()
    return nt_sys_cpu_stats(ctx, inter, dpcs, sysc)


def cpu_freq():
    """Return CPU frequency as a named tuple."""
    ret = []
    for curr, min_f, max_f in cext.cpu_freq():
        item = nt_sys_cpu_freq(curr, min_f, max_f)
        ret.append(item)
    return ret


def getloadavg():
    """Not available on Windows."""
    raise NotImplementedError("getloadavg is not available on this platform")


def net_io_counters(pernic=False, nowrap=True):
    """Return network I/O statistics for every network interface
    installed on the system as a dict.
    """
    if not pernic:
        return nt_sys_net_io_counter(*cext.net_io_counters(-1))
    else:
        ret = {}
        for nic, stats in cext.net_io_counters_per_nic():
            ret[nic] = nt_sys_net_io_counter(*stats)
        return ret


def disk_io_counters(perdisk=False, nowrap=True):
    """Return disk I/O statistics for every disk installed on the
    system as a dict.
    """
    if not perdisk:
        return nt_sys_disk_io_counter(*cext.disk_io_counters(-1))
    else:
        ret = {}
        for disk, stats in cext.disk_io_counters_per_disk():
            ret[disk] = nt_sys_disk_io_counter(*stats)
        return ret


def disk_partitions(all=False):
    """Return a list of disk partitions."""
    ret = []
    for part in cext.disk_partitions(all):
        device, mountp, fstype, opts = part
        item = nt_sys_diskpart(device, mountp, fstype, opts)
        ret.append(item)
    return ret


def disk_usage(path):
    """Return disk usage statistics about the given path."""
    total, free = cext.disk_usage(path)
    used = total - free
    percent = usage_percent(used, total, _round=1)
    return nt_sys_disk_usage(total, used, free, percent)


def net_if_addrs():
    """Return the addresses associated to each NIC."""
    ret = collections.defaultdict(list)
    for name, items in cext.net_if_addrs().items():
        for item in items:
            family, addr, netmask, bcast, ptp = item
            if PY3:
                # On py3, cext.net_if_addrs() returns bytes, which need
                # to be decoded.
                # The NIC name is decoded with utf-8 which is the
                # default for unicode strings.
                # For addresses, we assume they are ASCII, which is
                # a safe assumption.
                addr = addr.decode('ascii')
                if netmask is not None:
                    netmask = netmask.decode('ascii')
                if bcast is not None:
                    bcast = bcast.decode('ascii')
                if ptp is not None:
                    ptp = ptp.decode('ascii')
            ret[name].append(nt_sys_addr(family, addr, netmask, bcast, ptp))
    return dict(ret)


def net_if_stats():
    """Get NIC stats (isup, duplex, speed, mtu)."""
    ret = {}
    for name, items in cext.net_if_stats().items():
        isup, duplex, speed, mtu = items
        ret[name] = nt_sys_if_stats(isup, duplex, speed, mtu)
    return ret


def net_connections(kind='inet'):
    """Return system-wide connections."""
    if kind not in _common.conn_tmap:
        raise ValueError("invalid %r kind argument; choose between %s"
                         % (kind, ', '.join([repr(x) for x in _common.conn_tmap])))
    families, types = _common.conn_tmap[kind]
    raw_conns = cext.net_connections(cext.AF_INET, cext.SOCK_STREAM)
    ret = []
    for item in raw_conns:
        fd, fam, type, laddr, raddr, status, pid = item
        if fam not in families:
            continue
        if type not in types:
            continue
        if status in TCP_STATUSES:
            status = TCP_STATUSES[status]
        else:
            status = _common.CONN_NONE
        nt = conn_to_ntuple(fd, fam, type, laddr, raddr, status, pid)
        ret.append(nt)
    return ret


def sensors_battery():
    """Return battery information."""
    info = cext.sensors_battery()
    if info is None:
        return None
    percent, secsleft, power_plugged = info
    return nt_sys_battery(percent, secsleft, power_plugged)


def boot_time():
    """The system boot time expressed in seconds since the epoch."""
    return cext.boot_time()


def users():
    """Return users currently connected on the system."""
    ret = []
    for name, terminal, host, started, pid in cext.users():
        user = nt_sys_user(name, terminal, host, started, pid)
        ret.append(user)
    return ret


def pids():
    """Returns a list of PIDs currently running on the system."""
    return cext.pids()


def pid_exists(pid):
    """Return True if a process with the given PID exists."""
    if pid < 0:
        return False
    elif pid == 0:
        # On Windows, PID 0 is the "System Idle Process" and it's
        # always running.
        return True
    try:
        proc = cext.open_process(pid, cext.PROCESS_QUERY_LIMITED_INFORMATION)
    except OSError as err:
        if err.winerror == cext.ERROR_INVALID_PARAMETER:
            # This is the error code we get when the process is gone.
            return False
        # The process exists but we don't have enough privileges
        # to open it.
        elif err.winerror == cext.ERROR_ACCESS_DENIED:
            return True
        else:
            raise
    else:
        with contextlib.closing(proc):
            return True


def wrap_exceptions(fun):
    """Decorator which translates bare OSError exceptions into
    NoSuchProcess, AccessDenied and ZombieProcess exceptions.
    """
    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        try:
            return fun(self, *args, **kwargs)
        except OSError as err:
            # ERROR_INVALID_PARAMETER (87) is what we get when a process
            # is gone.
            if err.winerror == cext.ERROR_INVALID_PARAMETER:
                if self.is_running():
                    # This is a race condition. The process is gone
                    # but is_running() still returns True.
                    # This can happen because of a time-of-check
                    # to-time-of-use (TOCTOU) race condition.
                    # We just raise NoSuchProcess here.
                    raise NoSuchProcess(self.pid, self._name)
                else:
                    # The process is gone and is_running() returns False.
                    # We check if it's a zombie.
                    if _is_zombie(self.pid):
                        raise ZombieProcess(self.pid, self._name)
                    else:
                        raise NoSuchProcess(self.pid, self._name)
            elif err.winerror == cext.ERROR_ACCESS_DENIED:
                # We are not allowed to access the process.
                raise AccessDenied(self.pid, self._name)
            else:
                raise
    return wrapper


# =====================================================================
# --- Process class
# =====================================================================

class Process(object):
    """Represents an OS process with the given PID."""

    __slots__ = ["pid", "_name", "_ppid", "_cache"]

    def __init__(self, pid):
        self.pid = pid
        self._name = None
        self._ppid = None
        # used for caching purposes
        self._cache = {}

    def __str__(self):
        try:
            name = self.name()
            pid = self.pid
            return "psutil.Process(pid=%s, name=%r)" % (pid, name)
        except (NoSuchProcess, AccessDenied):
            details = "(pid=%s)" % self.pid
            if self._name:
                details += " name=%r" % self._name
            return "psutil.Process(%s)" % details

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, Process):
            return NotImplemented
        return self.pid == other.pid

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.pid)

    # --- utilities

    def as_dict(self, attrs=None, ad_value=None):
        """Return a dictionary of process information."""
        if attrs is None:
            attrs = self.__class__._get_public_methods()
        ret = {}
        for name in attrs:
            try:
                meth = getattr(self, name)
                if callable(meth):
                    ret[name] = meth()
                else:
                    ret[name] = meth
            except AccessDenied:
                ret[name] = ad_value
            except NoSuchProcess:
                # This is a race condition. The process is gone.
                # We can't do much about it.
                # We just return the dictionary with what we have.
                break
        return ret

    def parent(self):
        """Return the parent process as a Process object."""
        ppid = self.ppid()
        if ppid is None:
            return None
        return Process(ppid)

    def is_running(self):
        """Return True if the process is running, False otherwise."""
        if self.pid < 0:
            return False
        if self.pid == 0:
            # On Windows, PID 0 is the "System Idle Process" and it's
            # always running.
            return True
        try:
            proc = cext.open_process(
                self.pid, cext.PROCESS_QUERY_LIMITED_INFORMATION)
        except OSError as err:
            if err.winerror == cext.ERROR_INVALID_PARAMETER:
                # This is the error code we get when the process is gone.
                return False
            elif err.winerror == cext.ERROR_ACCESS_DENIED:
                # We are not allowed to access the process, but it's
                # running.
                return True
            else:
                raise
        else:
            with contextlib.closing(proc):
                return True

    # --- process identification

    @wrap_exceptions
    def name(self):
        """The process name."""
        # This is taken from the internal cache if available.
        # It's faster than calling the C extension.
        if self._name is not None:
            return self._name
        self._name = cext.proc_name(self.pid)
        return self._name

    @wrap_exceptions
    def exe(self):
        """The process executable as an absolute path."""
        # Note: this is a case where we can't use the internal cache
        # because the executable path can change.
        return cext.proc_exe(self.pid)

    @wrap_exceptions
    def cmdline(self):
        """The command line this process has been called with."""
        return cext.proc_cmdline(self.pid)

    @wrap_exceptions
    def ppid(self):
        """The process parent PID."""
        if self._ppid is not None:
            return self._ppid
        self._ppid = cext.proc_ppid(self.pid)
        return self._ppid

    @wrap_exceptions
    def status(self):
        """The process status as a string."""
        if _is_zombie(self.pid):
            return _common.STATUS_ZOMBIE
        else:
            return _common.STATUS_RUNNING

    @wrap_exceptions
    def username(self):
        """The name of the user that owns the process."""
        return cext.proc_username(self.pid)

    @wrap_exceptions
    def create_time(self):
        """The process creation time as a float expressed in seconds
        since the epoch.
        """
        return cext.proc_create_time(self.pid)

    @wrap_exceptions
    def cwd(self):
        """Return process current working directory."""
        return cext.proc_cwd(self.pid)

    @wrap_exceptions
    def environ(self):
        """The environment variables of the process as a dictionary."""
        return cext.proc_environ(self.pid)

    # --- process manipulation

    @wrap_exceptions
    def send_signal(self, sig):
        """Send a signal to the process."""
        if sig in (signal.SIGTERM, signal.CTRL_C_EVENT,
                   signal.CTRL_BREAK_EVENT):
            cext.proc_send_signal(self.pid, sig)
        else:
            raise ValueError("signal %s is not supported on this platform" % sig)

    @wrap_exceptions
    def suspend(self):
        """Suspend process execution."""
        cext.proc_suspend(self.pid)

    @wrap_exceptions
    def resume(self):
        """Resume process execution."""
        cext.proc_resume(self.pid)

    @wrap_exceptions
    def terminate(self):
        """Terminate the process."""
        cext.proc_terminate(self.pid)

    @wrap_exceptions
    def kill(self):
        """Kill the process."""
        cext.proc_kill(self.pid)

    @wrap_exceptions
    def wait(self, timeout=None):
        """Wait for process termination."""
        return cext.proc_wait(self.pid, timeout)

    # --- CPU

    @wrap_exceptions
    def cpu_times(self):
        """Return a (user, system) tuple of process CPU times."""
        user, system = cext.proc_cpu_times(self.pid)
        return nt_proc_cpu(user, system)

    @wrap_exceptions
    def cpu_percent(self, interval=None):
        """Return a float representing the current process CPU
        utilization as a percentage.
        """
        user, system = cext.proc_cpu_times(self.pid)
        now = time.time()
        if interval is None or interval == 0.0:
            # The first time this is called, we return 0.0.
            # This is not ideal but it's what other platforms do.
            # See: https://github.com/giampaolo/psutil/issues/1040
            if not hasattr(self, '_last_cpu_times'):
                self._last_cpu_times = (user, system)
                self._last_time = now
                return 0.0
            total_time = (user - self._last_cpu_times[0]) + \
                         (system - self._last_cpu_times[1])
            time_delta = now - self._last_time
            if time_delta == 0:
                return 0.0
            percent = (total_time / time_delta) * 100
            self._last_cpu_times = (user, system)
            self._last_time = now
            return percent
        else:
            time.sleep(interval)
            user2, system2 = cext.proc_cpu_times(self.pid)
            total_time = (user2 - user) + (system2 - system)
            return (total_time / interval) * 100

    @wrap_exceptions
    def cpu_affinity(self, cpus=None):
        """Get or set process CPU affinity."""
        if cpus is None:
            return cext.proc_cpu_affinity_get(self.pid)
        else:
            cext.proc_cpu_affinity_set(self.pid, cpus)

    @wrap_exceptions
    def nice(self, value=None):
        """Get or set process nice priority."""
        if value is None:
            return cext.proc_nice_get(self.pid)
        else:
            cext.proc_nice_set(self.pid, value)

    # --- memory

    @wrap_exceptions
    def memory_info(self):
        """Return a tuple of process memory information."""
        # wset, paged, nonpaged, pagefile = cext.proc_memory_info(self.pid)
        # return nt_proc_meminfo(wset, pagefile, 0, 0, 0, 0, 0)
        # For the sake of consistency with other platforms, we return
        # a named tuple with the same fields.
        # Also, we want to provide a more detailed memory information
        # on Windows.
        # See: https://github.com/giampaolo/psutil/issues/1083
        # In here we just call the C extension and return the result.
        rss, vms, num_page_faults, peak_wset, wset, peak_paged, paged, \
            peak_nonpaged, nonpaged, pagefile, peak_pagefile, \
            private = cext.proc_memory_info(self.pid)
        return nt_proc_meminfo(
            rss, vms, 0, 0, 0, 0, 0)

    @wrap_exceptions
    def memory_info_ex(self):
        """Return extended memory information for the process."""
        # See comments in memory_info().
        rss, vms, num_page_faults, peak_wset, wset, peak_paged, paged, \
            peak_nonpaged, nonpaged, pagefile, peak_pagefile, \
            private = cext.proc_memory_info(self.pid)
        return nt_proc_mem_ext(
            rss, vms, 0, 0, 0, 0, 0, 0, 0, 0)

    @wrap_exceptions
    def memory_percent(self, memtype="vms"):
        """Return the process memory utilization as a percentage of
        total physical memory.
        """
        if memtype not in ("rss", "vms"):
            raise ValueError("invalid %r memtype; choose between 'rss' "
                             "and 'vms'" % memtype)
        total = virtual_memory().total
        if memtype == "rss":
            rss = self.memory_info().rss
            return (rss / total) * 100
        else:
            vms = self.memory_info().vms
            return (vms / total) * 100

    @wrap_exceptions
    def memory_maps(self, grouped=True):
        """Return the process's memory maps."""
        if grouped:
            return cext.proc_memory_maps_grouped(self.pid)
        else:
            return cext.proc_memory_maps(self.pid)

    # --- IO

    @wrap_exceptions
    def io_counters(self):
        """Return process I/O statistics."""
        rc, wc, rb, wb, other_rc, other_wc = cext.proc_io_counters(self.pid)
        return nt_proc_io(rc, wc, rb, wb, other_rc, other_wc)

    # --- files & connections

    @wrap_exceptions
    def open_files(self):
        """Return files opened by process."""
        ret = []
        for path, fd in cext.proc_open_files(self.pid):
            item = nt_proc_openfile(path, fd)
            ret.append(item)
        return ret

    @wrap_exceptions
    def connections(self, kind='inet'):
        """Return connections opened by process."""
        if kind not in _common.conn_tmap:
            raise ValueError("invalid %r kind argument; choose between %s"
                             % (kind, ', '.join([repr(x) for x in _common.conn_tmap])))
        families, types = _common.conn_tmap[kind]
        raw_conns = cext.proc_connections(self.pid, cext.AF_INET, cext.SOCK_STREAM)
        ret = []
        for item in raw_conns:
            fd, fam, type, laddr, raddr, status = item
            if fam not in families:
                continue
            if type not in types:
                continue
            if status in TCP_STATUSES:
                status = TCP_STATUSES[status]
            else:
                status = _common.CONN_NONE
            nt = conn_to_ntuple(fd, fam, type, laddr, raddr, status, self.pid)
            ret.append(nt)
        return ret

    # --- threads

    @wrap_exceptions
    def num_threads(self):
        """Return the number of threads used by this process."""
        return cext.proc_num_threads(self.pid)

    @wrap_exceptions
    def threads(self):
        """Return threads opened by process."""
        ret = []
        for tid, user, system in cext.proc_threads(self.pid):
            item = nt_proc_thread(tid, user, system)
            ret.append(item)
        return ret

    # --- other

    @wrap_exceptions
    def num_handles(self):
        """Return the number of handles used by this process."""
        return cext.proc_num_handles(self.pid)

    @wrap_exceptions
    def num_ctx_switches(self):
        """Return the number of context switches performed by process."""
        vol, invol = cext.proc_num_ctx_switches(self.pid)
        return nt_proc_ctxsw(vol, invol)

    @wrap_exceptions
    def uids(self):
        """Return user IDs of this process."""
        # Note: on Windows we can't get the real, effective and saved
        # UIDs so we just return the current user UID.
        user = self.username()
        return nt_proc_uids(user, user, user)

    @wrap_exceptions
    def gids(self):
        """Return group IDs of this process."""
        # Note: on Windows we can't get the real, effective and saved
        # GIDs so we just return the current user GID.
        group = self.username()
        return nt_proc_gids(group, group, group)

    @classmethod
    def _get_public_methods(cls):
        """Return a list of public methods of this class."""
        return [
            name for name in dir(cls)
            if not name.startswith('_') and callable(getattr(cls, name))]


# =====================================================================
# --- Windows services
# =====================================================================

class WindowsService(object):
    """Represents a Windows service."""

    def __init__(self, name, display_name):
        self.name = name
        self.display_name = display_name

    def __str__(self):
        return "psutil.WindowsService(name=%r, display_name=%r)" % (
            self.name, self.display_name)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, WindowsService):
            return NotImplemented
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.name)

    # --- public methods

    def as_dict(self):
        """Return a dictionary of service information."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'binpath': self.binpath(),
            'username': self.username(),
            'start_type': self.start_type(),
            'status': self.status(),
            'pid': self.pid(),
            'description': self.description(),
        }

    def binpath(self):
        """The path to the service binary file."""
        return cext.win_service_get_config(self.name)['binpath']

    def username(self):
        """The name of the user that owns the service."""
        return cext.win_service_get_config(self.name)['username']

    def start_type(self):
        """The service start type."""
        return cext.win_service_get_config(self.name)['start_type']

    def description(self):
        """The service description."""
        return cext.win_service_get_description(self.name)

    def status(self):
        """The service status."""
        return cext.win_service_get_status(self.name)['status']

    def pid(self):
        """The service process identifier.
        If the service is not running this is None.
        """
        return cext.win_service_get_status(self.name)['pid']

    def start(self, timeout=None):
        """Start the service."""
        cext.win_service_start(self.name, timeout)

    def stop(self, timeout=None):
        """Stop the service."""
        cext.win_service_stop(self.name, timeout)


def win_service_iter():
    """Return an iterator yielding a WindowsService instance for all
    Windows services installed.
    """
    for name, display_name in cext.win_service_iter():
        yield WindowsService(name, display_name)


def win_service_get(name):
    """Get a Windows service by name."""
    for service in win_service_iter():
        if service.name == name:
            return service
    raise NoSuchProcess(pid=None, name=name, msg="no such service")