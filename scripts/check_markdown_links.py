#!/usr/bin/env python3
"""Validate local Markdown links with no external dependencies."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".omx",
    ".claude",
    ".codex",
    ".agents",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
}
INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s+(\S+)", re.MULTILINE)


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(REPO_ROOT):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".md"):
                files.append(Path(root) / filename)
    return sorted(files)


def normalize_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target:
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    if (
        target.startswith("#")
        or target.startswith("http://")
        or target.startswith("https://")
        or target.startswith("mailto:")
        or target.startswith("app://")
    ):
        return None
    return unquote(target.split("#", 1)[0])


def resolve_target(source: Path, target: str) -> Path:
    if target.startswith("/"):
        return REPO_ROOT / target.lstrip("/")
    return source.parent / target


def main() -> int:
    failures: list[str] = []
    for markdown_file in iter_markdown_files():
        text = markdown_file.read_text(encoding="utf-8")
        targets = [match.group(1) for match in INLINE_LINK_RE.finditer(text)]
        targets.extend(match.group(1) for match in REFERENCE_LINK_RE.finditer(text))

        for raw_target in targets:
            normalized = normalize_target(raw_target)
            if normalized is None:
                continue

            resolved = resolve_target(markdown_file, normalized).resolve()
            if not resolved.exists():
                relative_source = markdown_file.relative_to(REPO_ROOT)
                failures.append(f"{relative_source}: missing local link target: {raw_target}")

    if failures:
        print("Markdown link check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Markdown link check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
