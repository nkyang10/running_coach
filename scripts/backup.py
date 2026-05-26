"""
Create a timestamped backup of data/ and knowledge/ directories.
Run manually or via Task Scheduler.

Usage:
  python scripts/backup.py              # Create backup
  python scripts/backup.py --keep 7     # Keep last N backups (auto-cleanup)
"""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_DIR / "data" / "backups"

EXCLUDE_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
EXCLUDE_PATTERNS = {"*.pyc", "*.db"}


def should_include(path: Path) -> bool:
    """Check if a path should be included in backup."""
    # Skip excluded directories
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return False
    # Skip excluded patterns
    for pattern in EXCLUDE_PATTERNS:
        if path.match(pattern):
            return False
    return True


def create_backup() -> Path:
    """Create a zip backup of important directories."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup-{timestamp}.zip"

    source_dirs = [
        PROJECT_DIR / "knowledge",
        PROJECT_DIR / "data",
        PROJECT_DIR / "docs",
    ]

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
            for file_path in source_dir.rglob("*"):
                if file_path.is_file() and should_include(file_path):
                    arcname = file_path.relative_to(PROJECT_DIR)
                    zipf.write(file_path, arcname)

    print(f"✅ Backup created: {backup_path}")
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"   Size: {size_mb:.1f} MB")
    return backup_path


def cleanup_old_backups(keep: int = 7):
    """Remove backups older than the most recent `keep` backups."""
    backups = sorted(BACKUP_DIR.glob("backup-*.zip"))
    if len(backups) <= keep:
        return

    to_delete = backups[:-keep]
    for backup in to_delete:
        backup.unlink()
        print(f"   Cleaned up: {backup.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backup coach data")
    parser.add_argument("--keep", type=int, default=7,
                        help="Number of backups to keep (default: 7)")
    args = parser.parse_args()

    backup_path = create_backup()
    cleanup_old_backups(args.keep)

    print(f"\n✅ Backup complete. {args.keep} most recent backups kept.")
