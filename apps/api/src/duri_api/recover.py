"""Run orphan media recovery for every month partition.

Usage:
    python -m duri_api.recover --storage-root /path/to/DuriStorage --timezone Asia/Seoul
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from duri_api.storage import PERIOD_PATTERN, DuriStorageWriter


def list_periods(storage_root: Path) -> list[str]:
    """List the month partitions under DuriStorage/timeline.

    Args:
        storage_root: DuriStorage root directory.

    Returns:
        Sorted "YYYY-MM" names of partition directories (other names are ignored).
    """
    periods: list[str] = []
    for partition in sorted(storage_root.glob("timeline/*/*")):
        if not partition.is_dir():
            continue
        if PERIOD_PATTERN.fullmatch(partition.name) is None:
            continue
        if partition.parent.name != partition.name[:4]:
            continue
        periods.append(partition.name)
    return periods


def recover_all_periods(storage_root: Path, app_timezone: str) -> dict[str, int]:
    """Re-register orphan photos in every partition (photos/ files not in metadata.json).

    Args:
        storage_root: DuriStorage root directory.
        app_timezone: App timezone of the writer, e.g. "Asia/Seoul".

    Returns:
        Number of recovered Logs per period (only periods with at least one).
    """
    # Recovery only reuses the participants already stored in each metadata.json.
    writer = DuriStorageWriter(
        storage_root=storage_root,
        participants={},
        app_timezone=app_timezone,
    )
    recovered_counts: dict[str, int] = {}
    for period in list_periods(storage_root):
        recovered = writer.recover_orphan_media(period)
        if recovered:
            recovered_counts[period] = len(recovered)
    return recovered_counts


def main(argv: list[str] | None = None) -> int:
    """Command line entry point.

    Args:
        argv: Arguments without the program name (None reads sys.argv).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Recover orphan media in DuriStorage.")
    parser.add_argument("--storage-root", default=os.environ.get("DURI_STORAGE_ROOT"))
    parser.add_argument("--timezone", default=os.environ.get("DURI_APP_TIMEZONE", "Asia/Seoul"))
    arguments = parser.parse_args(argv)
    if not arguments.storage_root:
        parser.error("--storage-root or DURI_STORAGE_ROOT is required")

    recovered_counts = recover_all_periods(Path(arguments.storage_root), arguments.timezone)
    if not recovered_counts:
        print("no orphan media found")
        return 0
    for period, count in recovered_counts.items():
        print(f"{period}: recovered {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
