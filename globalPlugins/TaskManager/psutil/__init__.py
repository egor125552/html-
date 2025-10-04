# -*- coding: utf-8 -*-

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""psutil is a cross-platform library for retrieving information on
running processes and system utilization (CPU, memory, disks, network,
sensors) in Python.
"""

from __future__ import division

import collections
import contextlib
import functools
import os
import signal
import stat
import sys
import threading
import time
from . import _common
from ._common import AIX
from ._common import BSD
from ._common import FREEBSD
from ._common import LINUX
from ._common import MACOS
from ._common import NETBSD
from ._common import OPENBSD
from ._common import POSIX
from ._common import SUNOS
from ._common import WINDOWS
from ._common import AccessDenied
from ._common import Error
from ._common import ZombieProcess
from ._common import memoize
from ._common import memoize_when_activated
from ._common import parse_environ_block
from ._common import ppid_map
from ._common import supports_ipv6
from ._common import term_signal_map
from ._common import usage_percent
from ._common import warn
from ._compat import long
from ._compat import PY3
from ._compat import range
from ._compat import super
from ._compat import callable

# fmt: off
__version__ = "5.9.8"
__author__ = "Giampaolo Rodola'"
__author_email__ = "g.rodola@gmail.com"
__url__ = "https://github.com/giampaolo/psutil"
version_info = tuple([int(num) for num in __version__.split('.')])
# fmt: on

# =====================================================================
# --- constants
# =====================================================================

# --- Process priority constants, to be used with Process.nice()
if POSIX:
    # These constants are not available on Windows.
    # Re-defined here to avoid platform-specific code.
    # https://github.com/giampaolo/psutil/issues/1025
    try:
        from os import PRIO_PROCESS
        from os import PRIO_PGRP
        from os import PRIO_USER
    except ImportError:
        # They are not available on all POSIX systems.
        # https://github.com/giampaolo/psutil/pull/1413
        PRIO_PROCESS = 0
        PRIO_PGRP = 1
        PRIO_USER = 2

# --- Process status constants
# These are returned by Process.status().
STATUS_RUNNING = "running"
STATUS_SLEEPING = "sleeping"
STATUS_DISK_SLEEP = "disk-sleep"
STATUS_STOPPED = "stopped"
STATUS_TRACING_STOP = "tracing-stop"
STATUS_ZOMBIE = "zombie"
STATUS_DEAD = "dead"
STATUS_WAKING = "waking"
STATUS_IDLE = "idle"  # BSD
STATUS_LOCKED = "locked"  # FreeBSD
STATUS_WAITING = "waiting"  # FreeBSD
STATUS_SUSPENDED = "suspended"  # NetBSD

# --- Process "nice" constants
if WINDOWS:
    # https://docs.microsoft.com/en-us/windows/win32/procthread/scheduling-priorities
    # Used with Process.nice() and Process.ionice()
    ABOVE_NORMAL_PRIORITY_CLASS = 32768
    BELOW_NORMAL_PRIORITY_CLASS = 16384
    HIGH_PRIORITY_CLASS = 128
    IDLE_PRIORITY_CLASS = 64
    NORMAL_PRIORITY_CLASS = 32
    REALTIME_PRIORITY_CLASS = 256

# --- Connection constants
# These are returned by Process.connections()
CONN_ESTABLISHED = "ESTABLISHED"
CONN_SYN_SENT = "SYN_SENT"
CONN_SYN_RECV = "SYN_RECV"
CONN_FIN_WAIT1 = "FIN_WAIT1"
CONN_FIN_WAIT2 = "FIN_WAIT2"
CONN_TIME_WAIT = "TIME_WAIT"
CONN_CLOSE = "CLOSE"
CONN_CLOSE_WAIT = "CLOSE_WAIT"
CONN_LAST_ACK = "LAST_ACK"
CONN_LISTEN = "LISTEN"
CONN_CLOSING = "CLOSING"
CONN_NONE = "NONE"

# --- Other constants
# Used to determine whether a process is running with
# limited permissions.
if POSIX:
    # See: https://github.com/giampaolo/psutil/issues/1025
    #      https://github.com/giampaolo/psutil/issues/1233
    #      https://github.com/giampaolo/psutil/pull/1413
    try:
        from os import REXIST  # noqa: F401
        from os import WEXIST
        from os import XEXIST
    except ImportError:
        F_OK = 0
        X_OK = 1
        W_OK = 2
        R_OK = 4
else:
    F_OK = 0
    X_OK = 1
    W_OK = 2
    R_OK = 4

# --- IO priority constants
# IO priority constants, to be used with Process.ionice()
if LINUX:
    # linux only
    IOPRIO_CLASS_NONE = 0
    IOPRIO_CLASS_RT = 1
    IOPRIO_CLASS_BE = 2
    IOPRIO_CLASS_IDLE = 3

# --- sensors
if LINUX:
    # https://www.kernel.org/doc/Documentation/hwmon/sysfs-interface
    # The word "input" is used for the current value of the sensor,
    # "crit" for the critical high value, and "max" for the high value.
    # The sensor names are not in a standard, but the labels are.
    # AFAICT these are the most common labels.
    # Source: https://github.com/giampaolo/psutil/issues/1249
    SENSORS_LABELS = {
        # CPUs
        'coretemp': "CPU",
        'zenpower': "CPU",
        'k10temp': "CPU",
        # Motherboard
        'acpitz': "Motherboard",
        'it8728-isa-0228': "Motherboard",
        # GPUs
        'amdgpu': "GPU",
        'nouveau': "GPU",
        # Disks
        'drivetemp': "Disk",
        # Other
        'generic_cpu': "CPU",
    }

# =====================================================================
# --- import platform specific modules
# =====================================================================

if sys.platform.startswith("linux"):
    from . import _pslinux as _psplatform
    from ._pslinux import disk_partitions
    from ._pslinux import sensors_temperatures
    from ._pslinux import sensors_fans
    from ._pslinux import sensors_battery
    from ._pslinux import cpu_stats
    from ._pslinux import cpu_times
    from ._pslinux import cpu_count
    from ._pslinux import cpu_times_percent
    from ._pslinux import cpu_freq
    from ._pslinux import getloadavg
    from ._pslinux import virtual_memory
    from ._pslinux import swap_memory
    from ._pslinux import disk_usage
    from ._pslinux import disk_io_counters
    from ._pslinux import net_io_counters
    from ._pslinux import net_connections
    from ._pslinux import net_if_addrs
    from ._pslinux import net_if_stats
    from ._pslinux import boot_time
    from ._pslinux import users
    from ._pslinux import pids
    from ._pslinux import pid_exists
    from ._pslinux import wrap_exceptions
    from ._pslinux import Process
    from ._pslinux import cpu_count as cpu_count_physical
    # ...so that we can use "from psutil import _pslinux" etc.
    _pslinux = _pslinux

elif sys.platform.startswith(("win32", "cygwin")):
    from . import _pswindows as _psplatform
    from ._pswindows import disk_partitions
    from ._pswindows import sensors_battery
    from ._pswindows import cpu_stats
    from ._pswindows import cpu_times
    from ._pswindows import cpu_count
    from ._pswindows import cpu_times_percent
    from ._pswindows import cpu_freq
    from ._pswindows import virtual_memory
    from ._pswindows import swap_memory
    from ._pswindows import disk_usage
    from ._pswindows import disk_io_counters
    from ._pswindows import net_io_counters
    from ._pswindows import net_connections
    from ._pswindows import net_if_addrs
    from ._pswindows import net_if_stats
    from ._pswindows import boot_time
    from ._pswindows import users
    from ._pswindows import pids
    from ._pswindows import pid_exists
    from ._pswindows import wrap_exceptions
    from ._pswindows import Process
    from ._pswindows import cpu_count_logical as cpu_count_physical
    _pswindows = _pswindows
    # some functions which are not available on Windows are defined
    # differently
    getloadavg = None
    sensors_temperatures = None
    sensors_fans = None

elif sys.platform.startswith("darwin"):
    from . import _psosx as _psplatform
    from ._psosx import disk_partitions
    from ._psosx import sensors_battery
    from ._psosx import sensors_temperatures
    from ._psosx import cpu_stats
    from ._psosx import cpu_times
    from ._psosx import cpu_count
    from ._psosx import cpu_times_percent
    from ._psosx import cpu_freq
    from ._psosx import getloadavg
    from ._psosx import virtual_memory
    from ._psosx import swap_memory
    from ._psosx import disk_usage
    from ._psosx import disk_io_counters
    from ._psosx import net_io_counters
    from ._psosx import net_connections
    from ._psosx import net_if_addrs
    from ._psosx import net_if_stats
    from ._psosx import boot_time
    from ._psosx import users
    from ._psosx import pids
    from ._psosx import pid_exists
    from ._psosx import wrap_exceptions
    from ._psosx import Process
    from ._psosx import cpu_count_physical
    _psosx = _psosx
    sensors_fans = None

elif sys.platform.startswith(("freebsd", "openbsd", "netbsd")):
    if FREEBSD:
        from . import _psbsd as _psplatform
        from ._psbsd import disk_partitions
        from ._psbsd import sensors_battery
        from ._psbsd import sensors_temperatures
        from ._psbsd import sensors_fans
        from ._psbsd import cpu_stats
        from ._psbsd import cpu_times
        from ._psbsd import cpu_count
        from ._psbsd import cpu_times_percent
        from ._psbsd import cpu_freq
        from ._psbsd import getloadavg
        from ._psbsd import virtual_memory
        from ._psbsd import swap_memory
        from ._psbsd import disk_usage
        from ._psbsd import disk_io_counters
        from ._psbsd import net_io_counters
        from ._psbsd import net_connections
        from ._psbsd import net_if_addrs
        from ._psbsd import net_if_stats
        from ._psbsd import boot_time
        from ._psbsd import users
        from ._psbsd import pids
        from ._psbsd import pid_exists
        from ._psbsd import wrap_exceptions
        from ._psbsd import Process
        from ._psbsd import cpu_count_physical
        _psbsd = _psplatform
    elif OPENBSD or NETBSD:
        from . import _psposix as _psplatform
        from ._psbsd import disk_partitions
        from ._psbsd import sensors_battery
        from ._psbsd import cpu_stats
        from ._psbsd import cpu_times
        from ._psbsd import cpu_count
        from ._psbsd import cpu_times_percent
        from ._psbsd import getloadavg
        from ._psbsd import virtual_memory
        from ._psbsd import swap_memory
        from ._psbsd import disk_usage
        from ._psbsd import disk_io_counters
        from ._psbsd import net_io_counters
        from ._psbsd import net_connections
        from ._psbsd import net_if_addrs
        from ._psbsd import net_if_stats
        from ._psbsd import boot_time
        from ._psbsd import users
        from ._psbsd import pids
        from ._psbsd import pid_exists
        from ._psbsd import wrap_exceptions
        from ._psbsd import Process
        from ._psbsd import cpu_count_physical
        _psbsd = _psplatform
        # not supported
        cpu_freq = None
        sensors_temperatures = None
        sensors_fans = None

elif sys.platform.startswith("sunos"):
    from . import _pssunos as _psplatform
    from ._pssunos import disk_partitions
    from ._pssunos import cpu_stats
    from ._pssunos import cpu_times
    from ._pssunos import cpu_count
    from ._pssunos import cpu_times_percent
    from ._pssunos import cpu_freq
    from ._pssunos import getloadavg
    from ._pssunos import virtual_memory
    from ._pssunos import swap_memory
    from ._pssunos import disk_usage
    from ._pssunos import disk_io_counters
    from ._pssunos import net_io_counters
    from ._pssunos import net_connections
    from ._pssunos import net_if_addrs
    from ._pssunos import net_if_stats
    from ._pssunos import boot_time
    from ._pssunos import users
    from ._pssunos import pids
    from ._pssunos import pid_exists
    from ._pssunos import wrap_exceptions
    from ._pssunos import Process
    from ._pssunos import cpu_count_physical
    _pssunos = _psplatform
    # not supported
    sensors_battery = None
    sensors_temperatures = None
    sensors_fans = None

elif sys.platform.startswith("aix"):
    from . import _psaix as _psplatform
    from ._psaix import disk_partitions
    from ._psaix import cpu_stats
    from ._psaix import cpu_times
    from ._psaix import cpu_count
    from ._psaix import cpu_times_percent
    from ._psaix import getloadavg
    from ._psaix import virtual_memory
    from ._psaix import swap_memory
    from ._psaix import disk_usage
    from ._psaix import disk_io_counters
    from ._psaix import net_io_counters
    from ._psaix import net_connections
    from ._psaix import net_if_addrs
    from ._psaix import net_if_stats
    from ._psaix import boot_time
    from ._psaix import users
    from ._psaix import pids
    from ._psaix import pid_exists
    from ._psaix import wrap_exceptions
    from ._psaix import Process
    from ._psaix import cpu_count_physical
    _psaix = _psplatform
    # not supported
    cpu_freq = None
    sensors_battery = None
    sensors_temperatures = None
    sensors_fans = None

else:
    # Some platforms like Android are not officially supported but we
    # try to import the POSIX module as a fallback.
    # See: https://github.com/giampaolo/psutil/issues/1367
    try:
        from . import _psposix as _psplatform
        from ._psposix import disk_io_counters
        from ._psposix import net_io_counters
        from ._psposix import users
        from ._psposix import pids
        from ._psposix import pid_exists
        from ._psposix import wrap_exceptions
        from ._psposix import Process
    except ImportError:
        raise ImportError(
            "platform %s is not supported" % repr(sys.platform))

    # not supported
    disk_partitions = None
    sensors_battery = None
    cpu_stats = None
    cpu_times = None
    cpu_count = None
    cpu_times_percent = None
    cpu_freq = None
    getloadavg = None
    virtual_memory = None
    swap_memory = None
    disk_usage = None
    net_connections = None
    net_if_addrs = None
    net_if_stats = None
    boot_time = None
    cpu_count_physical = None
    sensors_temperatures = None
    sensors_fans = None


# =====================================================================
# --- public functions
# =====================================================================

__all__ = [
    # constants
    "AIX", "BSD", "FREEBSD", "LINUX", "MACOS", "NETBSD", "OPENBSD",
    "POSIX", "SUNOS", "WINDOWS",
    "STATUS_RUNNING", "STATUS_SLEEPING", "STATUS_DISK_SLEEP",
    "STATUS_STOPPED", "STATUS_TRACING_STOP", "STATUS_ZOMBIE", "STATUS_DEAD",
    "STATUS_WAKING", "STATUS_IDLE", "STATUS_LOCKED", "STATUS_WAITING",
    "STATUS_SUSPENDED",
    "CONN_ESTABLISHED", "CONN_SYN_SENT", "CONN_SYN_RECV", "CONN_FIN_WAIT1",
    "CONN_FIN_WAIT2", "CONN_TIME_WAIT", "CONN_CLOSE", "CONN_CLOSE_WAIT",
    "CONN_LAST_ACK", "CONN_LISTEN", "CONN_CLOSING", "CONN_NONE",
    "ABOVE_NORMAL_PRIORITY_CLASS", "BELOW_NORMAL_PRIORITY_CLASS",
    "HIGH_PRIORITY_CLASS", "IDLE_PRIORITY_CLASS", "NORMAL_PRIORITY_CLASS",
    "REALTIME_PRIORITY_CLASS",
    "IOPRIO_CLASS_NONE", "IOPRIO_CLASS_RT", "IOPRIO_CLASS_BE",
    "IOPRIO_CLASS_IDLE",
    "PRIO_PROCESS", "PRIO_PGRP", "PRIO_USER",
    "version_info", "__version__",
    # classes
    "Process", "Popen",
    # exceptions
    "Error", "NoSuchProcess", "ZombieProcess", "AccessDenied", "TimeoutExpired",
    # functions
    "pid_exists", "pids", "process_iter", "wait_procs",
    "virtual_memory", "swap_memory", "cpu_times", "cpu_percent",
    "cpu_times_percent", "cpu_count", "cpu_stats", "cpu_freq", "getloadavg",
    "net_io_counters", "net_connections", "net_if_addrs", "net_if_stats",
    "disk_partitions", "disk_usage", "disk_io_counters",
    "sensors_temperatures", "sensors_fans", "sensors_battery",
    "boot_time", "users",
    "cpu_count_physical",
]

# Add platform-specific functions to __all__
if LINUX:
    __all__.extend(["PROCFS_PATH"])
if MACOS:
    __all__.extend(["MACOS_ ዋና"])


# =====================================================================
# --- CPU
# =====================================================================

_last_cpu_times = None
_last_cpu_times_per_cpu = None


@memoize
def _get_cpu_times_user_time():
    """Return the default 'user' time to be used by cpu_percent()."""
    if LINUX:
        # on Linux we can get a much more precise sleep()
        return time.time()
    else:
        # otherwise there's no other way to get a time with a
        # sub-millisecond resolution, so we get the total process
        # time.
        # time.clock() is the most precise on Windows, time.time()
        # on other platforms.
        try:
            return time.clock() if WINDOWS else time.time()
        except AttributeError:  # time.clock() was removed in py 3.8
            return time.time()


def cpu_percent(interval=None, percpu=False):
    """Return a float representing the current system-wide CPU utilization as a
    percentage.

    When interval is > 0.0, compares system CPU times elapsed before
    and after the interval (blocking).

    When interval is 0.0 or None, compares system CPU times elapsed
    since last call or module import, returning immediately.
    In this case is recommended for accuracy that this function be
    called with a sensible interval (e.g. 0.1) in a loop.
    E.g.

    >>> # blocking
    >>> psutil.cpu_percent(interval=1)
    2.0
    >>> # non-blocking (percentage since last call)
    >>> psutil.cpu_percent(interval=None)
    2.9
    >>> time.sleep(1)
    >>> psutil.cpu_percent(interval=None)
    3.6
    >>>

    When percpu is True returns a list of floats representing the
    utilization as a percentage for each CPU.
    First call with percpu=True should be ignored just like for
    cpu_percent().

    Note: the returned value can be > 100.0 in case of a machine
    with multiple CPUs.
    """
    global _last_cpu_times
    global _last_cpu_times_per_cpu

    def calculate(t1, t2):
        # The following formulas are stolen from great top-like
        # tool htop:
        # https://github.com/hishamhm/htop/blob/master/CPUMeter.c
        #
        # Note: on transactional memory systems and virtualization
        # environments, "steal" and "guest" CPU times are not
        # accounted for by the kernel, so we must ignore them.
        #
        # See:
        # - https://github.com/giampaolo/psutil/issues/1007
        # - https://github.com/torvalds/linux/blob/
        #   34567909a819586196238a0b3f46f32587792fa6/fs/proc/stat.c#L114
        t1_total = sum(t1)
        t2_total = sum(t2)

        # guest and guest_nice are already included in user and nice,
        # so we must subtract them to avoid double counting.
        if LINUX:
            t1_total -= (t1.guest + t1.guest_nice)
            t2_total -= (t2.guest + t2.guest_nice)

        # Note: we need to subtract steal and guest times from t1_busy
        # and t2_busy.
        t1_busy = t1_total - t1.idle
        t2_busy = t2_total - t2.idle

        if LINUX:
            # Guest time is already accounted in "user" time so subtract
            # it to avoid double counting.
            t1_busy -= t1.guest
            t2_busy -= t2.guest

        if t2_busy > t1_busy:
            busy_delta = t2_busy - t1_busy
            total_delta = t2_total - t1_total
            if total_delta:
                # final percentage is a value between 0 and 100
                return (busy_delta / total_delta) * 100
        return 0.0

    blocking = interval is not None and interval > 0.0

    # system-wide usage
    if not percpu:
        if blocking:
            t1 = cpu_times()
            time.sleep(interval)
        else:
            t1 = _last_cpu_times
        _last_cpu_times = cpu_times()
        if t1 is None:
            return 0.0
        return calculate(t1, _last_cpu_times)

    # per-cpu usage
    else:
        if blocking:
            tot1 = cpu_times(percpu=True)
            time.sleep(interval)
        else:
            tot1 = _last_cpu_times_per_cpu
        _last_cpu_times_per_cpu = cpu_times(percpu=True)
        if tot1 is None:
            return [0.0] * cpu_count()
        ret = []
        for i in range(len(_last_cpu_times_per_cpu)):
            t1 = tot1[i]
            t2 = _last_cpu_times_per_cpu[i]
            ret.append(calculate(t1, t2))
        return ret


# =====================================================================
# --- processes
# =====================================================================


class TimeoutExpired(Error):
    """Raised by Process.wait(timeout) and wait_procs(timeout) if
    the timeout expires and the process(es) are still alive.
    """

    def __init__(self, timeout, pid=None, name=None):
        super(TimeoutExpired, self).__init__(pid=pid, name=name)
        self.timeout = timeout

    def __str__(self):
        msg = "timeout %s" % self.timeout
        if self.pid is not None:
            msg += " expired"
            if self.name:
                msg += " on process %s (pid=%s)" % (self.name, self.pid)
            else:
                msg += " on process pid=%s" % self.pid
        return msg


def process_iter(attrs=None, ad_value=None):
    """Return an iterator yielding a Process class instance for all
    running processes on the local machine.

    Every new Process instance is only created once and then cached
    into an internal table which is updated every time this is called.

    Cached Process instances are checked for PID uniqueness and
    create time in order to be sure they are still running, otherwise
    a NoSuchProcess exception is raised.

    The sorting order of the processes is based on their PID.

    'attrs' is an optional list of strings specifying what
    Process methods should be called in advance and cached.
    It can be used for performance reasons in order to avoid
    multiple method calls later on.
    The following methods are supported:
    'cmdline', 'connections', 'cpu_affinity', 'cpu_percent', 'cpu_times',
    'create_time', 'cwd', 'environ', 'exe', 'gids', 'io_counters',
    'ionice', 'memory_full_info', 'memory_info', 'memory_maps',
    'memory_percent', 'name', 'nice', 'num_ctx_switches', 'num_fds',
    'num_threads', 'open_files', 'ppid', 'status', 'threads', 'uids',
    'username'.

    'ad_value' is the value to be returned by the cached methods
    in case AccessDenied is raised when retrieving a process
    property. It can be used for performance reasons in order to
    avoid try-except blocks later on.

    Examples:

    >>> import psutil
    >>> for p in psutil.process_iter():
    ...     print(p)
    ...
    psutil.Process(pid=0, name='System Idle Process')
    psutil.Process(pid=4, name='System')
    ...

    >>> for p in psutil.process_iter(attrs=['pid', 'name']):
    ...    print(p.info)
    ...
    {'pid': 0, 'name': 'System Idle Process'}
    {'pid': 4, 'name': 'System'}
    ...

    >>> for p in psutil.process_iter(attrs=['pid', 'name', 'username'],
    ...                             ad_value=None):
    ...    print(p.info)
    ...
    {'pid': 0, 'name': 'System Idle Process', 'username': 'NT AUTHORITY\\SYSTEM'}
    {'pid': 4, 'name': 'System', 'username': 'NT AUTHORITY\\SYSTEM'}
    ...
    """
    def add(pid):
        proc = Process(pid)
        if attrs is not None:
            try:
                proc.info = proc.as_dict(attrs=attrs, ad_value=ad_value)
            except NoSuchProcess:
                # The process may have disappeared in the meantime.
                # In this case we just ignore it.
                return
        process_iter._cache[pid] = proc

    def on_process_disappeared(proc):
        # We get here in case a Process instance was cached but the
        # process is gone in the meantime.
        try:
            del process_iter._cache[proc.pid]
        except KeyError:
            # In case of a race condition this may have already been
            # removed.
            pass

    new_pids = set(pids())
    old_pids = set(process_iter._cache.keys())
    new_procs = []

    # Add new processes.
    for pid in new_pids - old_pids:
        add(pid)

    # Check existent processes.
    # This is the slowest part.
    # We needed to create a new list because we may remove elements
    # from the cache dict while iterating.
    for proc in list(process_iter._cache.values()):
        try:
            if proc.is_running():
                if attrs is not None:
                    proc.info = proc.as_dict(attrs=attrs, ad_value=ad_value)
            else:
                on_process_disappeared(proc)
        except (NoSuchProcess, ZombieProcess):
            on_process_disappeared(proc)
        except AccessDenied:
            # We should not get here as is_running() is supposed to
            # swallow it, but you never know.
            if attrs is not None:
                proc.info = {
                    attr: ad_value for attr in attrs
                }

    # Prepare the list of processes to be returned.
    # This is yet another slow part.
    for pid in sorted(new_pids):
        try:
            new_procs.append(process_iter._cache[pid])
        except KeyError:
            # Process can be gone in the meantime.
            pass

    return new_procs


# The cache used by process_iter().
process_iter._cache = {}


def wait_procs(procs, timeout=None, callback=None):
    """Wait for an iterable of Process instances to terminate.
    Return a (gone, alive) tuple of lists indicating which processes
    are gone and which ones are still alive.
    The gone ones will be Process instances whereas the alive ones
    will be Popen instances.

    'procs' is a list of Process instances.

    The 'timeout' parameter is expressed in seconds.
    If specified and the process is still alive after timeout
    TimeoutExpired is raised.

    'callback' is a function which gets called every time a process
    terminates (a process is passed as callback argument).

    Example which terminates and waits for a list of processes:

    >>> for p in procs:
    ...    p.terminate()
    ...
    >>> gone, alive = wait_procs(procs)

    Note: if you're terminating another process you may want to
    use Popen.wait() instead.
    """
    if not procs:
        return ([], [])
    gone = []
    alive = list(procs)
    if timeout is not None:
        deadline = time.time() + timeout
    interval = 0.001

    def check(p):
        try:
            return not p.is_running()
        except NoSuchProcess:
            return True
        except Exception:
            # For "weird" cases like getting EPERM on OSX.
            # see: https://github.com/giampaolo/psutil/issues/1359
            return False

    while alive:
        for p in alive[:]:  # iterate on a copy
            if check(p):
                gone.append(p)
                alive.remove(p)
                if callback:
                    callback(p)
        if not alive:
            break
        if timeout is not None and time.time() >= deadline:
            raise TimeoutExpired(timeout)
        interval = min(interval * 2, 0.04)
        time.sleep(interval)

    return (gone, alive)


# =====================================================================
# --- Popen
# =====================================================================


class Popen(Process):
    """A more convenient subprocess.Popen class.
    It starts a sub process and deals with it as a Process instance.
    For constructor and methods arguments see:
    https://docs.python.org/3/library/subprocess.html#popen-constructor

    It also provides all psutil.Process methods.
    For a list of methods see:
    https://psutil.readthedocs.io/en/latest/#psutil.Process

    Example:

    >>> import psutil
    >>> p = psutil.Popen(["python", "-c", "print('hello')"],
    ...                  stdout=subprocess.PIPE)
    >>> p.name()
    'python'
    >>> p.username()
    'giampaolo'
    >>> p.communicate()
    (b'hello\n', None)
    >>> p.wait(timeout=2)
    0
    >>>
    """

    def __init__(self, *args, **kwargs):
        # This is not cheap, but it's the only way to know "self"
        # (the Process instance) before subprocess.Popen.__init__
        # is called and the new process is created.
        # If we lose the race condition and the process is created
        # before "self" is assigned we won't be able to call any
        # Process method.
        # We could use a lock but it would serialize all Popen calls,
        # and that would suck.
        # In here we're also making sure that if the new process
        # terminates very fast we'll still be able to get its PID
        # and create time.
        self.__subproc = None
        self.__proc = self

        # This is a bit of a hack. We want to run this first, so
        # that we can have a Process instance before the process
        # is created.
        # We'll use this later in __getattribute__.
        self.__proc.__init__(pid=None)

        # This is the same logic used in subprocess.py to tell whether
        # the new process is running with limited permissions.
        if POSIX:
            if 'preexec_fn' not in kwargs:
                if 'user' in kwargs or 'group' in kwargs:
                    # In order to get a permission error we need to call
                    # os.seteuid/gid. We can't do that from here as it will
                    # change the main process EUID/EGID.
                    # We will set a proper AccessDenied in __init__ later.
                    pass
                else:
                    self.__proc._proc_name_cache = \
                        os.path.basename(args[0]).decode(sys.getfilesystemencoding()) \
                        if isinstance(args[0], bytes) else os.path.basename(args[0])

        # This will eventually create the process and assign a PID
        # to self.__subproc.
        self.__subproc = self.__orig_popen(*args, **kwargs)

        # This is the part where we actually initialize the Process class.
        self.__proc.__init__(self.__subproc.pid)

        # If we get here it means we were able to create the Process
        # instance before the process terminated.
        # We now want to make sure the created process is the one
        # we have wrapped.
        # We do this by checking its creation time, which is something
        # that is supposed to be unique.
        # In case the check fails we're not raising an exception,
        # but we won't be able to call any Process method.
        # See: https://github.com/giampaolo/psutil/issues/416
        with self.__proc.oneshot():
            self.__proc.create_time()

        if POSIX:
            # If we get a permission error here it means we don't have
            # the rights to access process information.
            # This is also what happens in subprocess.py.
            # It will result in a lazy AccessDenied being raised later.
            try:
                self.name()
            except AccessDenied:
                pass

    if sys.version_info >= (3, 3):
        # If we are on Python 3.3+ we can't monkey patch
        # subprocess.Popen because it's a C function.
        # We have to rely on a subprocess.Popen subclass instead.
        # We can't just inherit from subprocess.Popen because we need
        # to call Process.__init__ *before* Popen.__init__
        # (so that we can get an handle of the process while it's
        # being created).
        # The trick is to define __init__ and then overwrite it with
        # a new one.
        def __getattribute__(self, name):
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                # The only time we want to proxy the call to the
                # subprocess.Popen instance is when dealing with
                # subprocess.Popen methods.
                # Every other Process method should be handled by the
                # base class.
                if name in self._subproc_meths:
                    return getattr(self.__subproc, name)
                raise

        __orig_popen = __import__("subprocess").Popen
        _subproc_meths = frozenset([
            'communicate', 'send_signal', 'terminate', 'kill', 'wait',
            'poll', 'pid', 'returncode', 'stdin', 'stdout', 'stderr',
            '__enter__', '__exit__',
        ])

    else:
        # On Python 2 we can monkey patch subprocess.Popen and we
        # don't need to subclass.
        # This is better because it's more robust.
        def __new__(cls, *args, **kwargs):
            # This will create a psutil.Process instance, which is not
            # what we want. We'll have to override it later.
            proc = Process.__new__(cls)
            # The real Popen instance is created later in __init__.
            # This is a nastly hack to avoid that the user provides
            # a 'pid' argument, which would result in a psutil.Process
            # instance being created twice.
            if 'pid' in kwargs:
                raise TypeError("'pid' argument is not accepted")
            # We need to call __init__ later and we don't want to
            # do it twice.
            proc._Popen__subproc = None
            return proc

        __import__("subprocess").Popen = Popen
        __orig_popen = object.__new__(__import__("subprocess").Popen)

    # --- Popen methods

    def communicate(self, *args, **kwargs):
        """Just like subprocess.Popen.communicate(), but wait() is called
        on the psutil.Process instance.
        This is important because if the process terminates too quickly
        we won't be able to get its PID and create time, and so all
        Process methods will fail.
        """
        if self.__subproc.stdin:
            self.__subproc.stdin.close()
        ret = self.__subproc.communicate(*args, **kwargs)
        self.wait()
        return ret

    def wait(self, timeout=None):
        """Just like subprocess.Popen.wait(), but wait() is called on the
        psutil.Process instance.
        This is important because if the process terminates too quickly
        we won't be able to get its PID and create time, and so all
        Process methods will fail.
        """
        if self.__subproc is None:
            # This can happen if this gets called by atexit module.
            # The Popen instance is gone in the meantime.
            return None
        ret = self.__subproc.wait(timeout)
        try:
            super(Popen, self).wait(0)
        except TimeoutExpired:
            pass
        return ret

    # On py < 3.3 we are monkey patching subprocess.Popen so we need
    # to proxy all of its methods.
    if sys.version_info < (3, 3):
        def send_signal(self, sig):
            self.__subproc.send_signal(sig)

        def terminate(self):
            self.__subproc.terminate()

        def kill(self):
            self.__subproc.kill()

        def poll(self):
            return self.__subproc.poll()

        @property
        def stdin(self):
            return self.__subproc.stdin

        @property
        def stdout(self):
            return self.__subproc.stdout

        @property
        def stderr(self):
            return self.__subproc.stderr

        @property
        def pid(self):
            return self.__subproc.pid

        @property
        def returncode(self):
            return self.__subproc.returncode

        def __enter__(self):
            return self.__subproc.__enter__()

        def __exit__(self, *args, **kwargs):
            return self.__subproc.__exit__(*args, **kwargs)

    # --- utilities

    def __repr__(self):
        return \
            "<%s(pid=%s, name=%r, returncode=%s)>" % (
                self.__class__.__name__, self.pid, self.name(), self.returncode)

    def __eq__(self, other):
        # Necessary since we're overriding __eq__ in Process class.
        if isinstance(other, Popen):
            return self.__subproc == other.__subproc
        return super(Popen, self).__eq__(other)

    def __hash__(self):
        # Necessary since we're overriding __eq__ in Process class.
        return hash(self.__subproc)


# =====================================================================
# --- main
# =====================================================================

if __name__ == "__main__":
    from ._common import print_info
    print_info()