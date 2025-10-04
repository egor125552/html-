# -*- coding: utf-8 -*-

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Common objects and functions which are not platform specific."""

from __future__ import division

import collections
import contextlib
import errno
import functools
import os
import stat
import sys
import threading
import time
import warnings
from ._compat import long
from ._compat import PY3
from ._compat import basestring
from ._compat import FileNotFoundError
from ._compat import PermissionError
from ._compat import ProcessLookupError
from ._compat import InterruptedError
from ._compat import ChildProcessError

# =====================================================================
# --- constants
# =====================================================================

# Platform constants.
# These are determined at import time.
# POSIX = 'posix'
# WINDOWS = 'nt'
# LINUX = 'linux'
# OSX = 'darwin'
# FREEBSD = 'freebsd'
# OPENBSD = 'openbsd'
# NETBSD = 'netbsd'
# BSD = FREEBSD or OPENBSD or NETBSD
# SUNOS = 'sunos'
# AIX = 'aix'

POSIX = os.name == "posix"
WINDOWS = os.name == "nt"
LINUX = sys.platform.startswith("linux")
MACOS = sys.platform.startswith("darwin")
FREEBSD = sys.platform.startswith("freebsd")
OPENBSD = sys.platform.startswith("openbsd")
NETBSD = sys.platform.startswith("netbsd")
BSD = FREEBSD or OPENBSD or NETBSD
SUNOS = sys.platform.startswith("sunos")
AIX = sys.platform.startswith("aix")

# whether we are running in a big endian platform (e.g. SPARC)
IS_BIG_ENDIAN = sys.byteorder == 'big'

# The maximum value for a PID.
# It is used for PID rollover detection.
if LINUX:
    # See https://github.com/giampaolo/psutil/issues/1812
    try:
        with open("/proc/sys/kernel/pid_max", "rb") as f:
            PID_MAX = int(f.read())
    except (IOError, ValueError):
        PID_MAX = 32768
else:
    # For other platforms a default reasonable value is used.
    PID_MAX = 32768

# The lowest value for a PID.
if FREEBSD:
    # See https://github.com/giampaolo/psutil/issues/1814
    PID_MIN = 10
else:
    PID_MIN = 0

# psutil-specific exceptions.
# See http://goo.gl/DGzRj for a list of all exceptions raised
# by C implementations.
# We are not using a fake OSError class anymore, which was
# originally introduced to overcome this:
# http://bugs.python.org/issue5490
# The official Python 2 -> 3 porting guide suggests to use
# built-in OSError and distinguish by errno.
# Let's do that also for psutil custom exceptions.

class Error(Exception):
    """Base exception class. All other psutil exceptions inherit
    from this one.
    """

    def __init__(self, pid=None, name=None, msg=""):
        self.pid = pid
        self.name = name
        self.msg = msg
        if pid is not None and name is not None:
            details = "(pid=%s, name=%s)" % (self.pid, repr(self.name))
            self.msg = "%s %s" % (self.msg, details)
        elif pid is not None:
            details = "(pid=%s)" % self.pid
            self.msg = "%s %s" % (self.msg, details)
        super(Error, self).__init__(self.msg)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.msg)


class NoSuchProcess(Error):
    """Exception raised when a process with a certain PID doesn't
    or no longer exists (zombie processes are still processes).
    The 'pid' and 'name' attributes are available.
    'name' is the name the process had before disappearing and it's
    retrieved from the internal cache.
    """

    def __init__(self, pid, name=None, msg=None):
        Error.__init__(self, pid, name, msg=msg or "process no longer exists")


class ZombieProcess(NoSuchProcess):
    """Special subclass of NoSuchProcess raised when given PID belongs
    to a zombie process.
    The 'pid', 'name' and 'ppid' attributes are available.
    'ppid' is the parent PID.
    'name' is the name the process had before turning zombie and it's
    retrieved from the internal cache.
    """

    def __init__(self, pid, name=None, ppid=None, msg=None):
        Error.__init__(self, pid, name, msg=msg or "process is a zombie")
        self.ppid = ppid


class AccessDenied(Error):
    """Exception raised when permission to perform an action is denied.
    The 'pid' and 'name' attributes are available.
    """

    def __init__(self, pid=None, name=None, msg=""):
        Error.__init__(self, pid, name, msg=msg or "")


class TimeoutExpired(Error):
    """This is raised on timeout producing functions, when the
    timeout is expired and the function is not able to return
    a result in time.
    The 'seconds' attribute is available.
    """

    def __init__(self, seconds, pid=None, name=None):
        Error.__init__(self, pid, name, msg="timeout after %s seconds" % seconds)
        self.seconds = seconds


# --- namedtuples

# --- system
nt_sys_cputimes = collections.namedtuple(
    'scputimes',
    ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal',
     'guest', 'guest_nice'])
nt_sys_cputimes.user.__doc__ = \
    "time spent by normal processes executing in user mode"
nt_sys_cputimes.nice.__doc__ = \
    "time spent by niced processes executing in user mode"
nt_sys_cputimes.system.__doc__ = \
    "time spent by processes executing in kernel mode"
nt_sys_cputimes.idle.__doc__ = "time spent in the idle task"
nt_sys_cputimes.iowait.__doc__ = \
    "time spent waiting for I/O to complete (Linux)"
nt_sys_cputimes.irq.__doc__ = "time spent servicing hardware interrupts (Linux, BSD)"
nt_sys_cputimes.softirq.__doc__ = \
    "time spent servicing software interrupts (Linux)"
nt_sys_cputimes.steal.__doc__ = \
    "time spent in other operating systems when running in a " \
    "virtualized environment (Linux)"
nt_sys_cputimes.guest.__doc__ = \
    "time spent running a virtual CPU for guest " \
    "operating systems (Linux)"
nt_sys_cputimes.guest_nice.__doc__ = \
    "time spent running a niced guest virtual CPU for " \
    "guest operating systems (Linux)"

nt_sys_cpufreq = collections.namedtuple(
    'scpufreq', ['current', 'min', 'max'])
nt_sys_cpufreq.current.__doc__ = "current CPU frequency in Mhz"
nt_sys_cpufreq.min.__doc__ = "minimum CPU frequency in Mhz"
nt_sys_cpufreq.max.__doc__ = "maximum CPU frequency in Mhz"

nt_sys_cpupercent = collections.namedtuple(
    'scpupercent', ['user', 'nice', 'system', 'idle', 'iowait',
                    'irq', 'softirq', 'steal', 'guest', 'guest_nice'])

nt_sys_cpustats = collections.namedtuple(
    'scpustats', ['ctx_switches', 'interrupts', 'soft_interrupts', 'syscalls'])
nt_sys_cpustats.ctx_switches.__doc__ = \
    "number of context switches (voluntary + involuntary) since boot"
nt_sys_cpustats.interrupts.__doc__ = "number of interrupts since boot"
nt_sys_cpustats.soft_interrupts.__doc__ = \
    "number of software interrupts since boot"
nt_sys_cpustats.syscalls.__doc__ = \
    "number of system calls since boot (Linux only)"

nt_sys_diskpart = collections.namedtuple(
    'sdiskpart', ['device', 'mountpoint', 'fstype', 'opts'])
nt_sys_diskpart.device.__doc__ = \
    "device path (e.g. '/dev/sda1'). " \
    "May be a dummy name on some platforms (e.g. 'C:\\')."
nt_sys_diskpart.mountpoint.__doc__ = \
    "mount point path (e.g. '/')."
nt_sys_diskpart.fstype.__doc__ = \
    "file system type (e.g. 'ext4' on Linux, 'NTFS' on Windows)"
nt_sys_diskpart.opts.__doc__ = \
    "a comma-separated string of mount options (e.g. 'rw,nouse'). " \
    "This is a platform-specific string; may be an empty string " \
    "on some platforms."

nt_sys_diskusage = collections.namedtuple(
    'sdiskusage', ['total', 'used', 'free', 'percent'])
nt_sys_diskusage.total.__doc__ = "total space in bytes"
nt_sys_diskusage.used.__doc__ = "used space in bytes"
nt_sys_diskusage.free.__doc__ = "free space in bytes"
nt_sys_diskusage.percent.__doc__ = "usage percentage"

nt_sys_disk_io_counter = collections.namedtuple(
    'sdiskio',
    ['read_count', 'write_count', 'read_bytes', 'write_bytes',
     'read_time', 'write_time', 'read_merged_count', 'write_merged_count',
     'busy_time'])
nt_sys_disk_io_counter.read_count.__doc__ = "number of reads"
nt_sys_disk_io_counter.write_count.__doc__ = "number of writes"
nt_sys_disk_io_counter.read_bytes.__doc__ = "number of bytes read"
nt_sys_disk_io_counter.write_bytes.__doc__ = "number of bytes written"
nt_sys_disk_io_counter.read_time.__doc__ = "time spent reading from disk (in ms)"
nt_sys_disk_io_counter.write_time.__doc__ = \
    "time spent writing to disk (in ms)"
nt_sys_disk_io_counter.read_merged_count.__doc__ = \
    "number of merged reads (see iostats doc)"
nt_sys_disk_io_counter.write_merged_count.__doc__ = \
    "number of merged writes (see iostats doc)"
nt_sys_disk_io_counter.busy_time.__doc__ = \
    "time spent doing actual I/Os (in ms)"

nt_sys_net_io_counter = collections.namedtuple(
    'snetio',
    ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv',
     'errin', 'errout', 'dropin', 'dropout'])
nt_sys_net_io_counter.bytes_sent.__doc__ = "number of bytes sent"
nt_sys_net_io_counter.bytes_recv.__doc__ = "number of bytes received"
nt_sys_net_io_counter.packets_sent.__doc__ = "number of packets sent"
nt_sys_net_io_counter.packets_recv.__doc__ = "number of packets received"
nt_sys_net_io_counter.errin.__doc__ = \
    "total number of errors while receiving"
nt_sys_net_io_counter.errout.__doc__ = \
    "total number of errors while sending"
nt_sys_net_io_counter.dropin.__doc__ = \
    "total number of incoming packets which were dropped"
nt_sys_net_io_counter.dropout.__doc__ = \
    "total number of outgoing packets which were dropped " \
    "(always 0 on OSX and BSD)"

nt_sys_addr = collections.namedtuple(
    'saddr', ['family', 'address', 'netmask', 'broadcast', 'ptp'])
nt_sys_addr.family.__doc__ = \
    "the address family, either AF_INET, AF_INET6 or psutil.AF_LINK"
nt_sys_addr.address.__doc__ = "the primary address"
nt_sys_addr.netmask.__doc__ = "the netmask"
nt_sys_addr.broadcast.__doc__ = \
    "the broadcast address (only set for AF_INET and AF_INET6)"
nt_sys_addr.ptp.__doc__ = \
    "“point to point” address (only set for AF_INET and AF_INET6), " \
    "e.g. on TUN/TAP interfaces"

nt_sys_if_stats = collections.namedtuple(
    'snicstats', ['isup', 'duplex', 'speed', 'mtu'])
nt_sys_if_stats.isup.__doc__ = \
    "a bool indicating whether the interface is up " \
    "(meaning it has an IP address assigned)"
nt_sys_if_stats.duplex.__doc__ = \
    "the duplex communication type; can be NIC_DUPLEX_FULL, " \
    "NIC_DUPLEX_HALF or NIC_DUPLEX_UNKNOWN"
nt_sys_if_stats.speed.__doc__ = "the NIC speed in megabits (MB)"
nt_sys_if_stats.mtu.__doc__ = \
    "the maximum transmission unit, in bytes"

nt_sys_user = collections.namedtuple(
    'suser', ['name', 'terminal', 'host', 'started', 'pid'])
nt_sys_user.name.__doc__ = "the user name"
nt_sys_user.terminal.__doc__ = "the tty or pseudo-tty"
nt_sys_user.host.__doc__ = "the host name"
nt_sys_user.started.__doc__ = "the creation time as a floating point number"
nt_sys_user.pid.__doc__ = \
    "the process ID, if available (always None on Windows)"

nt_sys_swap = collections.namedtuple(
    'sswap', ['total', 'used', 'free', 'percent', 'sin', 'sout'])
nt_sys_swap.total.__doc__ = "total swap memory in bytes"
nt_sys_swap.used.__doc__ = "used swap memory in bytes"
nt_sys_swap.free.__doc__ = "free swap memory in bytes"
nt_sys_swap.percent.__doc__ = "the percentage usage"
nt_sys_swap.sin.__doc__ = "the number of bytes the system has swapped in " \
                          "from disk (cumulative)"
nt_sys_swap.sout.__doc__ = "the number of bytes the system has swapped out " \
                           "from disk (cumulative)"

nt_sys_vmem = collections.namedtuple(
    'svmem',
    ['total', 'available', 'percent', 'used', 'free',
     'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'])
nt_sys_vmem.total.__doc__ = "total physical memory (exclusive of swap)"
nt_sys_vmem.available.__doc__ = \
    "the memory that can be given instantly to processes without the " \
    "system going into swap. This is calculated by summing different " \
    "memory values depending on the platform and it is supposed to be " \
    "used to monitor actual memory usage in a cross platform fashion."
nt_sys_vmem.percent.__doc__ = "the percentage usage calculated as (total - available) / total * 100"
nt_sys_vmem.used.__doc__ = \
    "memory used, calculated differently depending on the platform and " \
    "designed for informational purposes only. " \
    "total - free does not necessarily match used."
nt_sys_vmem.free.__doc__ = \
    "memory not being used at all (zeroed) that is readily available; " \
    "note that this doesn't reflect the actual memory available " \
    "(use 'available' instead)"
nt_sys_vmem.active.__doc__ = "memory currently in use or very recently used, " \
                             "and so it is in RAM (Linux, macOS, FreeBSD)"
nt_sys_vmem.inactive.__doc__ = "memory that is marked as not used (Linux, macOS, FreeBSD)"
nt_sys_vmem.buffers.__doc__ = "cache for things like file system metadata (Linux, BSD)"
nt_sys_vmem.cached.__doc__ = "cache for various things (Linux, BSD)"
nt_sys_vmem.shared.__doc__ = "memory that may be simultaneously accessed by " \
                             "multiple processes (Linux)"
nt_sys_vmem.slab.__doc__ = "in-kernel data structures cache (Linux)"


# --- sensors
nt_sys_sens_temp = collections.namedtuple(
    'shwtemp', ['label', 'current', 'high', 'critical'])
nt_sys_sens_temp.label.__doc__ = "a label for the sensor (e.g. 'CPU')"
nt_sys_sens_temp.current.__doc__ = "current temperature in Celsius"
nt_sys_sens_temp.high.__doc__ = "high temperature in Celsius"
nt_sys_sens_temp.critical.__doc__ = "critical temperature in Celsius"

nt_sys_sens_fan = collections.namedtuple('sfan', ['label', 'current'])
nt_sys_sens_fan.label.__doc__ = "a label for the fan (e.g. 'CPU Fan')"
nt_sys_sens_fan.current.__doc__ = "fan speed in RPM"

nt_sys_sens_bat = collections.namedtuple(
    'sbattery', ['percent', 'secsleft', 'power_plugged'])
nt_sys_sens_bat.percent.__doc__ = "battery power left as a percentage"
nt_sys_sens_bat.secsleft.__doc__ = \
    "a rough approximation of how many seconds are left before the " \
    "battery runs out of power. May be POWER_TIME_UNLIMITED or " \
    "POWER_TIME_UNKNOWN."
nt_sys_sens_bat.power_plugged.__doc__ = \
    "True if the AC power source is online, False if it's on battery" \
    "power, None if it's unknown."


# --- process
nt_proc_cpu = collections.namedtuple(
    'pcputimes', ['user', 'system', 'children_user', 'children_system'])
nt_proc_cpu.user.__doc__ = "user time"
nt_proc_cpu.system.__doc__ = "system time"
nt_proc_cpu.children_user.__doc__ = "children user time"
nt_proc_cpu.children_system.__doc__ = "children system time"

nt_proc_meminfo = collections.namedtuple(
    'pmem', ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty'])
nt_proc_meminfo.rss.__doc__ = "aka “Resident Set Size”, this is the " \
                              "non-swapped physical memory a process " \
                              "has used. On UNIX it matches “top“‘s RES " \
                              "column). On Windows this is an alias for " \
                              "wset field of PROCESS_MEMORY_COUNTERS " \
                              "structure."
nt_proc_meminfo.vms.__doc__ = "aka “Virtual Memory Size”, this is the " \
                              "total amount of virtual memory used by the " \
                              "process. On UNIX it matches “top“‘s VIRT " \
                              "column. On Windows this is an alias for " \
                              "pagefile field of PROCESS_MEMORY_COUNTERS " \
                              "structure."
nt_proc_meminfo.shared.__doc__ = "memory that could be simultaneously " \
                                 "accessed by multiple processes"
nt_proc_meminfo.text.__doc__ = "aka TRS (text resident set) the amount of " \
                               "memory devoted to executable code"
nt_proc_meminfo.lib.__doc__ = "the memory used by shared libraries"
nt_proc_meminfo.data.__doc__ = "aka DRS (data resident set) the amount of " \
                               "memory devoted to other than executable code"
nt_proc_meminfo.dirty.__doc__ = "the number of dirty pages"

nt_proc_mem_ext = collections.namedtuple(
    'pextmem',
    ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty',
     'uss', 'pss', 'swap'])
nt_proc_mem_ext.rss.__doc__ = nt_proc_meminfo.rss
nt_proc_mem_ext.vms.__doc__ = nt_proc_meminfo.vms
nt_proc_mem_ext.shared.__doc__ = nt_proc_meminfo.shared
nt_proc_mem_ext.text.__doc__ = nt_proc_meminfo.text
nt_proc_mem_ext.lib.__doc__ = nt_proc_meminfo.lib
nt_proc_mem_ext.data.__doc__ = nt_proc_meminfo.data
nt_proc_mem_ext.dirty.__doc__ = nt_proc_meminfo.dirty
nt_proc_mem_ext.uss.__doc__ = \
    "aka “Unique Set Size”, this is the memory which is unique to a process" \
    " and which would be freed if the process was terminated right now."
nt_proc_mem_ext.pss.__doc__ = \
    "aka “Proportional Set Size”, is the amount of memory shared with " \
    "other processes, accounted in a way that the amount is divided evenly" \
    " between the processes that share it."
nt_proc_mem_ext.swap.__doc__ = "amount of memory that has been swapped out to disk."

nt_proc_mem_map = collections.namedtuple(
    'pmmap_grouped', ['path', 'rss', 'size', 'pss', 'shared_clean',
                      'shared_dirty', 'private_clean', 'private_dirty',
                      'referenced', 'anonymous', 'swap'])
nt_proc_mem_map.path.__doc__ = "the path of the mapped file"
nt_proc_mem_map.rss.__doc__ = \
    "the resident set size, which is the portion of the mapping that is " \
    "currently in RAM"
nt_proc_mem_map.size.__doc__ = "the total size of the mapping"
nt_proc_mem_map.pss.__doc__ = "the proportional set size"
nt_proc_mem_map.shared_clean.__doc__ = \
    "the part of the mapping that is shared with other processes and has " \
    "not been modified"
nt_proc_mem_map.shared_dirty.__doc__ = \
    "the part of the mapping that is shared with other processes and has " \
    "been modified"
nt_proc_mem_map.private_clean.__doc__ = \
    "the part of the mapping that is private to the process and has not " \
    "been modified"
nt_proc_mem_map.private_dirty.__doc__ = \
    "the part of the mapping that is private to the process and has been " \
    "modified"
nt_proc_mem_map.referenced.__doc__ = \
    "the amount of memory currently marked as referenced or accessed"
nt_proc_mem_map.anonymous.__doc__ = \
    "the amount of memory that does not correspond to any file"
nt_proc_mem_map.swap.__doc__ = \
    "the amount of memory that has been swapped out to disk"

nt_proc_mem_map_ext = collections.namedtuple(
    'pmmap_ext', ['addr', 'perms'] + nt_proc_mem_map._fields)
nt_proc_mem_map_ext.addr.__doc__ = "the memory address where the mapping begins"
nt_proc_mem_map_ext.perms.__doc__ = "a string representing the mapping's permissions"

nt_proc_io = collections.namedtuple(
    'pio', ['read_count', 'write_count', 'read_bytes', 'write_bytes',
            'read_chars', 'write_chars'])
nt_proc_io.read_count.__doc__ = \
    "the number of read operations performed (cumulative)"
nt_proc_io.write_count.__doc__ = \
    "the number of write operations performed (cumulative)"
nt_proc_io.read_bytes.__doc__ = "the number of bytes read (cumulative)"
nt_proc_io.write_bytes.__doc__ = "the number of bytes written (cumulative)"
nt_proc_io.read_chars.__doc__ = "the number of chars read (cumulative)"
nt_proc_io.write_chars.__doc__ = "the number of chars written (cumulative)"

nt_proc_ctxsw = collections.namedtuple(
    'pctxsw', ['voluntary', 'involuntary'])
nt_proc_ctxsw.voluntary.__doc__ = "number of voluntary context switches"
nt_proc_ctxsw.involuntary.__doc__ = "number of involuntary context switches"

nt_proc_uids = collections.namedtuple('puids', ['real', 'effective', 'saved'])
nt_proc_uids.real.__doc__ = "real user id"
nt_proc_uids.effective.__doc__ = "effective user id"
nt_proc_uids.saved.__doc__ = "saved user id"

nt_proc_gids = collections.namedtuple('pgids', ['real', 'effective', 'saved'])
nt_proc_gids.real.__doc__ = "real group id"
nt_proc_gids.effective.__doc__ = "effective group id"
nt_proc_gids.saved.__doc__ = "saved group id"

nt_proc_conn = collections.namedtuple(
    'pconn', ['fd', 'family', 'type', 'laddr', 'raddr', 'status'])
nt_proc_conn.fd.__doc__ = \
    "the socket file descriptor. If the connection refers to the " \
    "current process this may be passed to socket.fromfd() to for " \
    "further operations. If -1, this information is not retrievable."
nt_proc_conn.family.__doc__ = "the address family, either AF_INET, AF_INET6 or AF_UNIX"
nt_proc_conn.type.__doc__ = "the address type, either SOCK_STREAM, SOCK_DGRAM or SOCK_SEQPACKET"
nt_proc_conn.laddr.__doc__ = \
    "the local address as a (ip, port) tuple or a path in case of AF_UNIX " \
    "sockets. For AF_INET and AF_INET6 sockets, if the connection is in " \
    "listening state this is set to ('', 0) for all addresses."
nt_proc_conn.raddr.__doc__ = \
    "the remote address as a (ip, port) tuple or an absolute path in case " \
    "of UNIX sockets. When the socket is in a listening state raddr is " \
    "set to ()"
nt_proc_conn.status.__doc__ = \
    "represents the status of a TCP connection. The return value is one " \
    "of the psutil.CONN_* constants."

nt_proc_openfile = collections.namedtuple('popenfile', ['path', 'fd'])
nt_proc_openfile.path.__doc__ = "the absolute path of the opened file"
nt_proc_openfile.fd.__doc__ = \
    "the file descriptor number; on Windows this is not available and " \
    "is always set to -1"

nt_proc_thread = collections.namedtuple(
    'pthread', ['id', 'user_time', 'system_time'])
nt_proc_thread.id.__doc__ = "the thread unique ID"
nt_proc_thread.user_time.__doc__ = "the thread user time"
nt_proc_thread.system_time.__doc__ = "the thread system time"

# a dict which maps a C signal to a pretty string (e.g. "SIGKILL")
# The C signals are determined at import time by the platform C module.
signal_map = {}

# a dict which maps a C term signal to a pretty string (e.g. "SIGTERM")
term_signal_map = {}


# =====================================================================
# --- utility functions
# =====================================================================


def _assert_pid_not_reused(fun):
    """A decorator which raises NoSuchProcess in case a process is gone
    and its PID has been reused.
    This is used to decorate Process methods.
    """
    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        if self._pid is None:
            # This is a special case. It means we were not able to
            # determine the PID of the process, which can happen if it
            # terminates very quickly.
            # In this case we can't do much, so we just raise a generic
            # NoSuchProcess exception.
            # See: https://github.com/giampaolo/psutil/issues/33
            raise NoSuchProcess(pid=None, name=None)
        if not self.is_running():
            raise NoSuchProcess(self.pid, self._name, msg=fun.__name__)
        return fun(self, *args, **kwargs)
    return wrapper


def usage_percent(used, total, _round=1):
    """Calculate percentage usage of 'used' against 'total'."""
    try:
        ret = (float(used) / total) * 100
    except ZeroDivisionError:
        return 0.0
    if _round is not None:
        return round(ret, _round)
    else:
        return ret


def memoize(fun):
    """A simple memoize decorator for functions supporting (hashable)
    positional and keyword arguments.
    It also provides a cache_clear() function for clearing the cache.
    """
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            return cache[key]
        except KeyError:
            ret = fun(*args, **kwargs)
            cache[key] = ret
            return ret

    def cache_clear():
        """Clear cache."""
        cache.clear()

    cache = {}
    wrapper.cache_clear = cache_clear
    return wrapper


def memoize_when_activated(fun):
    """A memoize decorator which is disabled by default. It can be
    activated and deactivated on the fly.
    For efficiency reasons it can be used only against class methods
    accepting no arguments.
    """
    @functools.wraps(fun)
    def wrapper(self):
        if not wrapper.cache_activated:
            return fun(self)
        try:
            # Use function name as key, so we can have different caches
            # for different methods.
            return self._cache[fun]
        except KeyError:
            ret = self._cache[fun] = fun(self)
            return ret

    def cache_activate(self):
        """Activate cache."""
        wrapper.cache_activated = True

    def cache_deactivate(self):
        """Deactivate cache."""
        wrapper.cache_activated = False

    wrapper.cache_activated = False
    wrapper.cache_activate = cache_activate
    wrapper.cache_deactivate = cache_deactivate
    return wrapper


def ppid_map():
    """Return a {pid: ppid, ...} dict for all running processes."""
    ret = {}
    for pid in pids():
        try:
            ret[pid] = Process(pid).ppid()
        except (NoSuchProcess, ZombieProcess):
            pass
    return ret


def supports_ipv6():
    """Return True if IPv6 is supported on this platform, False otherwise."""
    if not os.path.exists('/proc/net/if_inet6'):
        return False
    # With IPv6 disabled, this file contains an empty list.
    with open("/proc/net/if_inet6", "r") as f:
        if f.read().strip():
            return True
    # Let's try to create a socket.
    import socket
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        with contextlib.closing(sock):
            return True
    except (socket.error, socket.gaierror):
        return False


def parse_environ_block(data):
    """Parse a C-style environ block (a list of null-terminated
    strings, with a final empty string) into a Python dict.
    """
    ret = {}
    if not data:
        return ret
    # The block is a list of null-terminated strings, with a final
    # empty string.
    # We can split by '\x00' and the last item will be an empty string.
    for part in data.strip('\x00').split('\x00'):
        try:
            key, value = part.split('=', 1)
        except ValueError:
            # Some names do not have a value.
            ret[part] = ''
        else:
            ret[key] = value
    return ret


def conn_to_ntuple(fd, fam, type, laddr, raddr, status, pid):
    """Convert a raw connection tuple to a proper ntuple.
    On some platforms some fields may be missing and need to be
    filled with dummy values.
    """
    if fam not in (socket.AF_INET, socket.AF_INET6, socket.AF_UNIX):
        fam = -1  # See issue #1293
    if type not in (socket.SOCK_STREAM, socket.SOCK_DGRAM, socket.SOCK_SEQPACKET):
        type = -1  # See issue #1293
    if laddr is None:
        laddr = ()
    if raddr is None:
        raddr = ()
    return nt_proc_conn(fd, fam, type, laddr, raddr, status)


def sockfam_to_enum(num):
    """Convert a numeric socket family value to an enum."""
    if num == socket.AF_INET:
        return socket.AF_INET
    if num == socket.AF_INET6:
        return socket.AF_INET6
    if POSIX and num == socket.AF_UNIX:
        return socket.AF_UNIX
    return num


def socktype_to_enum(num):
    """Convert a numeric socket type value to an enum."""
    if num == socket.SOCK_STREAM:
        return socket.SOCK_STREAM
    if num == socket.SOCK_DGRAM:
        return socket.SOCK_DGRAM
    if LINUX and num == socket.SOCK_SEQPACKET:
        return socket.SOCK_SEQPACKET
    return num


# =====================================================================
# --- deprecated APIs
# =====================================================================

# In case we'll ever need to deprecate something.
# The `warn` function is defined in _psutil_windows or _psutil_posix
# and is platform specific.

DEPRECATION_MSG = "%s is deprecated and will be removed in a future version. " \
                  "Use %s instead."


def deprecated_method(replacement):
    """A decorator for deprecated methods."""
    def outer(fun):
        @functools.wraps(fun)
        def inner(self, *args, **kwargs):
            msg = DEPRECATION_MSG % (
                self.__class__.__name__ + '.' + fun.__name__ + '()',
                self.__class__.__name__ + '.' + replacement + '()')
            warn(msg, DeprecationWarning)
            return fun(self, *args, **kwargs)
        return inner
    return outer


def deprecated_function(replacement):
    """A decorator for deprecated functions."""
    def outer(fun):
        @functools.wraps(fun)
        def inner(*args, **kwargs):
            msg = DEPRECATION_MSG % (fun.__name__ + '()', replacement + '()')
            warn(msg, DeprecationWarning)
            return fun(*args, **kwargs)
        return inner
    return outer