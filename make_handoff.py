"""Build a numbered hand-off zip in ./handoff/.

Double-click make_handoff.bat (or run: python make_handoff.py).
Each run creates a new numbered zip. Nothing is deleted or overwritten.
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HANDOFF_DIR = ROOT / "handoff"

# Top-level files always included if they exist.
INCLUDE_FILES = [
    "main.py",
    "requirements.txt",
    "pyproject.toml",
    "README.md",
    "CREDITS.md",
    "LICENSE.txt",
    "START_HERE.txt",
    ".gitignore",
    "session.py",
    "ai_sync.py",
    "AymashTain LED Remote.spec",
]

# Optional AI context files — included only when present.
INCLUDE_AI_CONTEXT = [
    "AI_CONTEXT.md",
    "AI_NOTES.md",
    "AI_SESSIONS.md",
    "AI_BRIEF.md",
    "AI_BACKLOG.md",
    "PROJECT.md",
]

# Top-level folders always included if they exist.
INCLUDE_DIRS = [
    "aymashtain",
    "AI_SYNC_PACK",
    "tests",
    "assets",
]

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".git",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "handoff",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".db",
    ".db-wal",
    ".db-shm",
    ".log",
    ".tmp",
}

EXCLUDE_FILE_NAMES = {
    "make_handoff.py",
    "make_handoff.bat",
    "events.csv",
    "events.json",
    "test.txt",
}


def next_number(folder: Path) -> int:
    if not folder.is_dir():
        return 1
    highest = 0
    pattern = re.compile(r"^handoff_(\d+)_", re.IGNORECASE)
    for entry in folder.iterdir():
        match = pattern.match(entry.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        current = Path(dirpath)
        if current == HANDOFF_DIR or HANDOFF_DIR in current.parents:
            continue
        for name in filenames:
            p = current / name
            if should_skip(p):
                continue
            yield p


def collect() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []

    for name in INCLUDE_FILES + INCLUDE_AI_CONTEXT:
        p = ROOT / name
        if p.is_file():
            out.append((p, name))

    for dirname in INCLUDE_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            continue
        for p in iter_files(base):
            rel = p.relative_to(ROOT)
            out.append((p, str(rel).replace(os.sep, "/")))

    seen: set[str] = set()
    unique: list[tuple[Path, str]] = []
    for p, arc in out:
        if arc in seen:
            continue
        seen.add(arc)
        unique.append((p, arc))
    return unique


def build_readme(number: int, files: list[tuple[Path, str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"AymashTain LED RGB Remote - Hand-off bundle #{number:03d}",
        f"Built: {now}",
        f"Source folder: {ROOT}",
        "",
        "READ THIS FIRST IF YOU ARE AN AI ASSISTANT",
        "==========================================",
        "",
        "This is a complete snapshot of the project. Everything you need is",
        "already here. Do not ask the user to go find files.",
        "",
        "  1. Open AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md and follow it.",
        "  2. Read AI_SYNC_PACK/00 through 05 in order.",
        "  3. Read AI_SYNC_PACK/06_CURRENT_CHAT.md LAST.",
        "     It records exactly what was done in the previous session and",
        "     what comes next.",
        "  4. Then ask the user which single file to work on.",
        "",
        "HOW THIS BUNDLE WAS MADE",
        "========================",
        "",
        "The user double-clicked make_handoff.bat in the project root. The",
        "script bundled the current source tree into this zip. It is a",
        "frozen snapshot. Any later edits on the user's PC are not in here.",
        "",
        "WHAT IS INSIDE",
        "==============",
        "- aymashtain/          full source package (the actual app)",
        "- AI_SYNC_PACK/        00-07 sync documents (read these first)",
        "- main.py, requirements.txt, pyproject.toml",
        "- README.md, CREDITS.md, .gitignore, the PyInstaller .spec",
        "- tests/ and assets/ if present",
        "- AI_CONTEXT.md, AI_NOTES.md, AI_SESSIONS.md, etc. if present",
        "",
        "WHAT IS DELIBERATELY NOT INSIDE",
        "================================",
        "- __pycache__, .venv, build/, dist/, .git",
        "- *.db files (the user's saved profiles and buttons)",
        "- session *.log / *.json / *.csv log files",
        "- exported events.csv / events.json (session junk)",
        "- the handoff/ folder itself (no recursive bundles)",
        "",
        f"Files bundled: {len(files)}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    HANDOFF_DIR.mkdir(exist_ok=True)
    number = next_number(HANDOFF_DIR)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"handoff_{number:03d}_{stamp}.zip"
    zip_path = HANDOFF_DIR / zip_name

    files = collect()
    if not files:
        print("Nothing to bundle - is this the project root?")
        return 1

    readme = build_readme(number, files)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("HANDOFF_README.txt", readme)
        for p, arc in files:
            try:
                zf.write(p, arcname=arc)
            except OSError as exc:
                print(f"  skipped {arc}: {exc}")

    size_kb = zip_path.stat().st_size / 1024
    print()
    print("=" * 62)
    print(f"  Hand-off #{number:03d} created")
    print("=" * 62)
    print(f"  File   : {zip_path}")
    print(f"  Files  : {len(files)}")
    print(f"  Size   : {size_kb:.1f} KB")
    print()
    print("  Unzip it anywhere, then drop the whole folder into a new AI chat.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
