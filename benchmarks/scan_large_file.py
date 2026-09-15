"""Benchmark local e bounded sem dados de cliente."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import tempfile
import time
from pathlib import Path

from wirs.application.orchestrator import run_scan
from wirs.cli.app import PROFILE_BUDGETS
from wirs.detectors.builtin import PhpHeuristicsDetector
from wirs.domain import LocalDirectoryTarget
from wirs.infrastructure import ArtifactReader, LocalArtifactSource


def _peak_rss_bytes() -> int:
    if os.name == "nt":

        class MemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        process = kernel32.GetCurrentProcess()
        get_info = psapi.GetProcessMemoryInfo
        get_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(MemoryCounters), ctypes.c_ulong]
        get_info.restype = ctypes.c_bool
        if not get_info(process, ctypes.byref(counters), ctypes.sizeof(counters)):
            return 0
        return max(int(counters.PeakWorkingSetSize), int(counters.WorkingSetSize))

    import resource

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if os.uname().sysname == "Darwin" else value * 1024)


def _create_fixture(root: Path, size_bytes: int) -> None:
    with (root / "large.php").open("wb") as target:
        target.write(b"<?php // synthetic benchmark\n")
        remaining = size_bytes - target.tell()
        block = b"$value = 1; // benign filler\n" * 4096
        while remaining > 0:
            chunk = block[:remaining]
            target.write(chunk)
            remaining -= len(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size-mb", type=int, default=64)
    parser.add_argument("--profile", choices=tuple(PROFILE_BUDGETS), default="soft")
    args = parser.parse_args()
    if args.size_mb <= 0:
        parser.error("--size-mb precisa ser positivo")

    with tempfile.TemporaryDirectory(prefix="wirs-benchmark-") as directory:
        root = Path(directory)
        _create_fixture(root, args.size_mb * 1024 * 1024)
        started = time.perf_counter()
        result = run_scan(
            LocalDirectoryTarget(root),
            profile=args.profile,
            source=LocalArtifactSource(),
            adapters=[],
            reader=ArtifactReader(),
            budget=PROFILE_BUDGETS[args.profile],
            detectors=[PhpHeuristicsDetector()],
        )
        wall_time_s = time.perf_counter() - started
        filesystem = result.coverage[0]

    print(
        json.dumps(
            {
                "profile": args.profile,
                "fixture_bytes": args.size_mb * 1024 * 1024,
                "wall_time_s": round(wall_time_s, 6),
                "peak_rss_bytes": _peak_rss_bytes(),
                "coverage": filesystem.state.value,
                "coverage_note": filesystem.note,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
