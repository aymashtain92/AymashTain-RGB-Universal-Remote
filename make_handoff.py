"""
One-click hand-off bundle builder for AymashTain LED RGB Remote.

Produces a FLAT, single-folder ZIP with:
  - Merged documentation (3 files instead of 7)
  - Merged package __init__ re-exports (1 doc instead of 5 files)
  - Flattened source tree using __ instead of folder separators
  - "# Original Path:" header injected into every text file
  - Sequential numbering (handoff_001.zip, handoff_002.zip, ...)
  - Zero subdirectories inside the ZIP

Target size: ~32 files (leaves room for screenshots under the 50-file cap).

Usage:
    python make_handoff.py              # build the zip
    python make_handoff.py --dry-run    # list files only, no zip
"""

import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
HANDOFF_DIR = PROJECT_ROOT / "handoff"
TEMP_BUILD_DIR = HANDOFF_DIR / "temp_flat_build"

# ---------------------------------------------------------------------------
# EXPLICIT ALLOWLIST - only these source files are bundled.
# ---------------------------------------------------------------------------
INCLUDE_PATHS = [
    "main.py",
    "aymashtain/__init__.py",
    "aymashtain/app.py",
    "aymashtain/config.py",
    "aymashtain/events.py",
    "aymashtain/paths.py",
    "aymashtain/ble/manager.py",
    "aymashtain/protocol/mrstar.py",
    "aymashtain/storage/db.py",
    "aymashtain/vision/camera.py",
    "aymashtain/audio/engine.py",
    "aymashtain/ui/context.py",
    "aymashtain/ui/theme.py",
    "aymashtain/ui/main_window.py",
    "aymashtain/ui/widgets/__init__.py",
    "aymashtain/ui/widgets/color_wheel.py",
    "aymashtain/ui/widgets/strip_preview.py",
    "aymashtain/ui/tabs/__init__.py",
    "aymashtain/ui/tabs/connect_tab.py",
    "aymashtain/ui/tabs/remote_tab.py",
    "aymashtain/ui/tabs/music_tab.py",
    "aymashtain/ui/tabs/sweep_tab.py",
    "aymashtain/ui/tabs/camera_tab.py",
    "aymashtain/ui/tabs/console_tab.py",
    "aymashtain/ui/tabs/lab_tab.py",
    "aymashtain/ui/tabs/events_tab.py",
    "aymashtain/ui/tabs/options_tab.py",
]

# Tiny re-export __init__.py files - merged into a single reference doc
# instead of being bundled individually. Keeps the file count low.
PACKAGE_INIT_FILES = [
    "aymashtain/ble/__init__.py",
    "aymashtain/protocol/__init__.py",
    "aymashtain/storage/__init__.py",
    "aymashtain/vision/__init__.py",
    "aymashtain/audio/__init__.py",
]

# Documentation merge groups.
DOC_GROUPS = {
    "00_PROJECT_MASTER_DOCS.md": [
        "AI_SYNC_PACK/00_MASTER_SUMMARY.md",
        "AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md",
        "AI_SYNC_PACK/05_DEVELOPER_README.md",
        "AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md",
    ],
    "01_WORKFLOW_AND_TODO.md": [
        "AI_SYNC_PACK/01_WORKFLOW.md",
        "AI_SYNC_PACK/03_TODO_USER_AND_AI.md",
        "AI_SYNC_PACK/04_AI_ERRORS_ONLY.md",
    ],
    "02_CURRENT_CHAT.md": [
        "AI_SYNC_PACK/06_CURRENT_CHAT.md",
    ],
}

# Header syntax by extension.
HASH_HEADER_EXTS = {
    ".py", ".bat", ".sh", ".ps1", ".toml", ".yaml", ".yml",
    ".ini", ".cfg", ".spec", ".txt", ".conf",
}
HTML_HEADER_EXTS = {".md"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_next_zip_filename() -> Path:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    nums = []
    for f in HANDOFF_DIR.glob("handoff_*.zip"):
        stem = f.stem  # "handoff_001"
        try:
            nums.append(int(stem.split("_")[-1]))
        except (ValueError, IndexError):
            continue
    return HANDOFF_DIR / f"handoff_{max(nums, default=0) + 1:03d}.zip"


def clean_temp_dir() -> None:
    if TEMP_BUILD_DIR.exists():
        shutil.rmtree(TEMP_BUILD_DIR)
    TEMP_BUILD_DIR.mkdir(parents=True, exist_ok=True)


def _header_for(rel_str: str, suffix: str) -> str:
    if suffix in HTML_HEADER_EXTS:
        return f"<!-- Original Path: {rel_str} -->\n\n"
    if suffix in HASH_HEADER_EXTS:
        return f"# Original Path: {rel_str}\n\n"
    return ""


def _flat_name(rel_str: str) -> str:
    return rel_str.replace("/", "__")


def _write_with_header(src: Path, dst: Path, rel_str: str) -> None:
    header = _header_for(rel_str, src.suffix.lower())
    if header:
        try:
            content = src.read_text(encoding="utf-8", errors="ignore")
            dst.write_text(header + content, encoding="utf-8")
            return
        except Exception as exc:
            print(f"  ! read failed {rel_str}: {exc} - raw copy")
    shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def merge_documentation() -> int:
    print("[1/5] Merging documentation files...")
    produced = 0
    for combined_name, source_files in DOC_GROUPS.items():
        chunks = []
        for rel_file in source_files:
            src = PROJECT_ROOT / rel_file
            if not src.is_file():
                print(f"  ! MISSING: {rel_file}")
                continue
            content = src.read_text(encoding="utf-8", errors="ignore")
            chunks.append(
                f"<!-- BEGIN FILE: {rel_file} -->\n\n"
                f"{content}\n\n"
                f"<!-- END FILE: {rel_file} -->"
            )
            print(f"  + merged: {rel_file}")
        if chunks:
            out = TEMP_BUILD_DIR / combined_name
            out.write_text("\n\n---\n\n".join(chunks), encoding="utf-8")
            print(f"  = created: {combined_name}")
            produced += 1
    print()
    return produced


def merge_package_inits() -> None:
    """Merge tiny re-export __init__.py files into one reference doc."""
    print("[2/5] Merging package __init__ re-exports...")
    chunks = []
    for rel_str in PACKAGE_INIT_FILES:
        src = PROJECT_ROOT / rel_str
        if not src.is_file():
            print(f"  ! MISSING: {rel_str}")
            continue
        content = src.read_text(encoding="utf-8", errors="ignore")
        chunks.append(
            f"## `{rel_str}`\n\n"
            f"Real path on disk: `{rel_str}`\n\n"
            f"```python\n{content.rstrip()}\n```\n"
        )
        print(f"  + merged: {rel_str}")

    if not chunks:
        print("  (nothing to merge)")
        print()
        return

    header = (
        "# Package `__init__.py` Re-Exports\n\n"
        "These sub-package `__init__.py` files are tiny re-export shims.\n"
        "They are bundled here instead of as separate files to keep the\n"
        "handoff total under 50 files.\n\n"
        "If you need to update one, ask the user to paste the current file\n"
        "content and send a full replacement for it by name.\n\n"
        "---\n\n"
    )
    out = TEMP_BUILD_DIR / "_package_init_exports.md"
    out.write_text(header + "\n---\n\n".join(chunks), encoding="utf-8")
    print("  = created: _package_init_exports.md")
    print()


def bundle_source_files() -> int:
    print("[3/5] Bundling source files with Original Path headers...")
    count = 0
    seen = set()
    for rel_str in INCLUDE_PATHS:
        src = PROJECT_ROOT / rel_str
        if not src.is_file():
            print(f"  ! MISSING: {rel_str}")
            continue
        flat = _flat_name(rel_str)
        if flat in seen:
            print(f"  ! COLLISION: {flat}")
            continue
        seen.add(flat)
        dst = TEMP_BUILD_DIR / flat
        _write_with_header(src, dst, rel_str)
        count += 1
        print(f"  + {rel_str}  ->  {flat}")
    print(f"\n  Source files bundled: {count}\n")
    return count


def write_handoff_readme() -> None:
    readme = TEMP_BUILD_DIR / "HANDOFF_README.txt"
    readme.write_text(
        "AymashTain LED RGB Remote - Hand-off Bundle\n"
        "============================================\n\n"
        "This is a FLAT snapshot. Every file is in this one folder.\n"
        "File names use __ instead of folder separators.\n"
        "Example: aymashtain/ui/tabs/remote_tab.py\n"
        "      -> aymashtain__ui__tabs__remote_tab.py\n\n"
        "Each source file starts with a comment header:\n"
        "  # Original Path: <real/path.py>          (for code)\n"
        "  <!-- Original Path: <real/path.md> -->   (for markdown)\n\n"
        "READ THESE FILES FIRST, IN THIS ORDER:\n"
        "  1. 00_PROJECT_MASTER_DOCS.md\n"
        "  2. 01_WORKFLOW_AND_TODO.md\n"
        "  3. _package_init_exports.md\n"
        "  4. 02_CURRENT_CHAT.md   <-- read this last, it is where we left off\n\n"
        "Then ask the user which single file to work on next.\n\n"
        "Project facts:\n"
        "  - Python 3.14.7 on Windows 10\n"
        "  - Entry point: main.py -> aymashtain.app:main\n"
        "  - This is a PACKAGE project, not a single main.py\n"
        "  - Never mix MR Star BC commands with Classic 56/CC commands\n"
        "  - Never put brightness inside the colour frame\n"
        "  - Always give full replacement files, not patches\n"
        "  - Always run: python -m py_compile .\\path\\to\\file.py\n"
        "  - Always run: python -m pytest -q  (after touching any __init__.py)\n\n"
        f"Bundle created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        encoding="utf-8",
    )
    print("[4/5] HANDOFF_README.txt written.\n")


def summarize_and_zip(dry_run: bool) -> None:
    files = sorted(p.name for p in TEMP_BUILD_DIR.iterdir() if p.is_file())
    total = len(files)

    print("-" * 60)
    print(f"  Total files: {total}")
    print(f"  Under 35-file target: {'YES' if total <= 35 else 'NO'}")
    print(f"  Under 50-file cap:    {'YES' if total <= 50 else 'NO'}")
    print("-" * 60)
    print()
    print("  File list:")
    for name in files:
        print(f"    {name}")
    print()

    if dry_run:
        print("[5/5] DRY RUN - no zip created.")
        shutil.rmtree(TEMP_BUILD_DIR)
        return

    zip_path = get_next_zip_filename()
    print(f"[5/5] Creating flat ZIP: {zip_path.name} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(TEMP_BUILD_DIR.iterdir()):
            if item.is_file():
                zf.write(item, arcname=item.name)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        has_subdirs = any("/" in n for n in names)

    shutil.rmtree(TEMP_BUILD_DIR)

    print()
    print(f"  Bundle: {zip_path}")
    print(f"  Zero subdirectories: {'YES' if not has_subdirs else 'NO'}")
    print()


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    print("=" * 60)
    print("  AymashTain Hand-off Bundle Builder")
    if dry_run:
        print("  MODE: dry run (list only)")
    print("=" * 60)
    print()
    clean_temp_dir()
    merge_documentation()
    merge_package_inits()
    bundle_source_files()
    write_handoff_readme()
    summarize_and_zip(dry_run)
    print("Done.")


if __name__ == "__main__":
    main()
