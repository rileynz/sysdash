"""System metrics collection.

All functions here are cheap, non-blocking snapshots. Anything that needs
a time delta (network/disk throughput) keeps its own last-seen state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import psutil


@dataclass
class CpuSnapshot:
    percent: float
    per_core: list[float]
    load_avg: tuple[float, float, float]


@dataclass
class MemorySnapshot:
    used_gb: float
    total_gb: float
    percent: float
    swap_used_gb: float
    swap_total_gb: float


@dataclass
class DiskSnapshot:
    used_gb: float
    total_gb: float
    percent: float
    read_mb_s: float
    write_mb_s: float


@dataclass
class NetworkSnapshot:
    download_mb_s: float
    upload_mb_s: float


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float


@dataclass
class ProcessSnapshot:
    processes: list[ProcessInfo] = field(default_factory=list)


def get_cpu() -> CpuSnapshot:
    per_core = psutil.cpu_percent(percpu=True)
    overall = sum(per_core) / len(per_core) if per_core else 0.0
    try:
        load = psutil.getloadavg()
    except (OSError, AttributeError):
        # getloadavg is unix-only; not available on Windows
        load = (0.0, 0.0, 0.0)
    return CpuSnapshot(percent=overall, per_core=per_core, load_avg=load)


def get_memory() -> MemorySnapshot:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    gb = 1024**3
    return MemorySnapshot(
        used_gb=vm.used / gb,
        total_gb=vm.total / gb,
        percent=vm.percent,
        swap_used_gb=swap.used / gb,
        swap_total_gb=swap.total / gb,
    )


class DiskMonitor:
    """Tracks disk I/O throughput between calls (needs a time delta)."""

    def __init__(self, path: str = "/") -> None:
        self.path = path
        self._last_io = psutil.disk_io_counters()
        self._last_time = time.monotonic()

    def snapshot(self) -> DiskSnapshot:
        usage = psutil.disk_usage(self.path)
        gb = 1024**3
        mb = 1024**2

        now = time.monotonic()
        io = psutil.disk_io_counters()
        elapsed = max(now - self._last_time, 0.001)

        read_mb_s = 0.0
        write_mb_s = 0.0
        if io is not None and self._last_io is not None:
            read_mb_s = (io.read_bytes - self._last_io.read_bytes) / mb / elapsed
            write_mb_s = (io.write_bytes - self._last_io.write_bytes) / mb / elapsed

        self._last_io = io
        self._last_time = now

        return DiskSnapshot(
            used_gb=usage.used / gb,
            total_gb=usage.total / gb,
            percent=usage.percent,
            read_mb_s=max(read_mb_s, 0.0),
            write_mb_s=max(write_mb_s, 0.0),
        )


class NetworkMonitor:
    """Tracks network throughput between calls (needs a time delta)."""

    def __init__(self) -> None:
        self._last_io = psutil.net_io_counters()
        self._last_time = time.monotonic()

    def snapshot(self) -> NetworkSnapshot:
        mb = 1024**2
        now = time.monotonic()
        io = psutil.net_io_counters()
        elapsed = max(now - self._last_time, 0.001)

        down_mb_s = (io.bytes_recv - self._last_io.bytes_recv) / mb / elapsed
        up_mb_s = (io.bytes_sent - self._last_io.bytes_sent) / mb / elapsed

        self._last_io = io
        self._last_time = now

        return NetworkSnapshot(
            download_mb_s=max(down_mb_s, 0.0),
            upload_mb_s=max(up_mb_s, 0.0),
        )


def get_top_processes(limit: int = 6) -> ProcessSnapshot:
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info
            mem = info["memory_info"]
            procs.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info["name"] or "?",
                    cpu_percent=info["cpu_percent"] or 0.0,
                    memory_mb=(mem.rss / 1024**2) if mem else 0.0,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    procs.sort(key=lambda x: x.cpu_percent, reverse=True)
    return ProcessSnapshot(processes=procs[:limit])


def kill_process(pid: int) -> tuple[bool, str]:
    """Attempt to terminate a process. Returns (success, message)."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        return True, f"Sent terminate signal to {name} (pid {pid})"
    except psutil.NoSuchProcess:
        return False, f"No process with pid {pid}"
    except psutil.AccessDenied:
        return False, f"Permission denied terminating pid {pid}"
    except Exception as e:  # noqa: BLE001 - surface any unexpected error to the UI
        return False, f"Failed to terminate pid {pid}: {e}"
