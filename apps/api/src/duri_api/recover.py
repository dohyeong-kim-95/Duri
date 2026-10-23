"""Run orphan media recovery for every month partition.

Usage:
    python -m duri_api.recover --storage-root /path/to/DuriStorage --timezone Asia/Seoul
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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


def load_known_participants(storage_root: Path) -> dict[str, str]:
    """Find participants already stored in any partition's metadata.json.

    Args:
        storage_root: DuriStorage root directory.

    Returns:
        {actor_id: display_name} from the first partition that has a non-empty
        participants map, or {} if none has one (the app writer then fills it
        on its next write to that partition).
    """
    for period in list_periods(storage_root):
        metadata_path = storage_root / "timeline" / period[:4] / period / "metadata.json"
        if not metadata_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(metadata, dict):
            continue
        stored_participants = metadata.get("participants")
        if not isinstance(stored_participants, dict) or not stored_participants:
            continue

        participants: dict[str, str] = {}
        for actor_id, participant in stored_participants.items():
            if not isinstance(participant, dict):
                continue
            display_name = participant.get("display_name")
            if isinstance(display_name, str):
                participants[actor_id] = display_name
        if participants:
            return participants
    return {}


def recover_all_periods(
    storage_root: Path,
    app_timezone: str,
) -> tuple[dict[str, int], dict[str, str]]:
    """Re-register orphan photos in every partition (photos/ files not in metadata.json).

    A failing partition (e.g. sink format or broken metadata.json) is skipped so
    the other partitions are still recovered.

    Args:
        storage_root: DuriStorage root directory.
        app_timezone: App timezone of the writer, e.g. "Asia/Seoul".

    Returns:
        (recovered_counts, failed_periods): number of recovered Logs per period
        (only periods with at least one), and the error message per failed period.
    """
    # A partition created here gets the participants known from other months;
    # existing partitions keep their own.
    writer = DuriStorageWriter(
        storage_root=storage_root,
        participants=load_known_participants(storage_root),
        app_timezone=app_timezone,
    )
    recovered_counts: dict[str, int] = {}
    failed_periods: dict[str, str] = {}
    for period in list_periods(storage_root):
        try:
            recovered = writer.recover_orphan_media(period)
        except Exception as exc:
            failed_periods[period] = f"{type(exc).__name__}: {exc}"
            continue
        if recovered:
            recovered_counts[period] = len(recovered)
    return recovered_counts, failed_periods


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

    recovered_counts, failed_periods = recover_all_periods(
        Path(arguments.storage_root), arguments.timezone
    )
    for period, count in recovered_counts.items():
        print(f"{period}: recovered {count}")
    for period, error in failed_periods.items():
        print(f"{period}: failed: {error}", file=sys.stderr)
    if failed_periods:
        return 1
    if not recovered_counts:
        print("no orphan media found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
