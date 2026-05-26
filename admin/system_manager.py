from __future__ import annotations

import subprocess
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.database import Database
from app.knowledge import KnowledgeBase
from app.logger import get_logger

logger = get_logger(__name__)


async def get_system_status(db: Database, kb: Optional[KnowledgeBase] = None) -> str:
    runner_count = await db.get_runner_count()
    total_runs_row = await db.fetchone("SELECT COUNT(*) as cnt FROM runs")
    total_runs = total_runs_row["cnt"] if total_runs_row else 0
    weekly_runs_row = await db.fetchall(
        "SELECT COUNT(*) as cnt FROM runs WHERE run_date >= date('now', '-7 days')"
    )
    weekly_runs = weekly_runs_row[0]["cnt"] if weekly_runs_row else 0
    injuries_row = await db.fetchone(
        "SELECT COUNT(*) as cnt FROM injuries WHERE active = 1"
    )
    active_injuries = injuries_row["cnt"] if injuries_row else 0

    lines = [
        "📊 *System Status*\n",
        f"**Runners:** {runner_count}",
        f"**Total Runs:** {total_runs}",
        f"**Runs this week:** {weekly_runs}",
        f"**Active Injuries:** {active_injuries}",
    ]

    if kb:
        lines.append(f"**Knowledge Files:** {len(kb.get_all())}")

    lines.append(f"**Uptime:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


async def create_backup(
    backup_dir: str = "data/backups",
    max_backups: int = 7,
) -> Optional[str]:
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = backup_path / f"coach_backup_{timestamp}.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in ["knowledge", "docs", "data"]:
            folder_path = Path(folder)
            if not folder_path.exists():
                continue
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    skip_dirs = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
                    if not any(p in skip_dirs for p in file_path.parts):
                        zf.write(file_path, file_path.as_posix())

    backups = sorted(backup_path.glob("coach_backup_*.zip"), reverse=True)
    for old in backups[max_backups:]:
        old.unlink()
        logger.info("removed_old_backup", path=str(old))

    logger.info("backup_created", path=str(zip_name))
    return str(zip_name)


_start_time = time.time()


async def get_health_report(
    db: Database, kb: Optional[KnowledgeBase] = None, config: Optional[any] = None
) -> str:
    import psutil

    checks = []
    status = "✅ ALL GOOD"

    # DB health
    try:
        row = await db.fetchone("SELECT 1 AS ok")
        db_ok = row is not None and row["ok"] == 1
        checks.append(("Database", "✅" if db_ok else "❌"))
        if not db_ok:
            status = "⚠️  ISSUES DETECTED"
    except Exception as e:
        checks.append(("Database", f"❌ {e}"))
        status = "⚠️  ISSUES DETECTED"

    # KB health
    if kb:
        kb_count = len(kb.get_all())
        checks.append(("Knowledge Base", f"✅ {kb_count} files"))
    else:
        checks.append(("Knowledge Base", "⚠️  not loaded"))
        status = "⚠️  ISSUES DETECTED"

    # Runner counts
    try:
        runner_count = await db.get_runner_count()
        checks.append(("Registered Runners", str(runner_count)))
    except Exception as e:
        checks.append(("Registered Runners", f"❌ {e}"))
        status = "⚠️  ISSUES DETECTED"

    # Run stats
    try:
        total_runs = (await db.fetchone("SELECT COUNT(*) as cnt FROM runs"))["cnt"]
        weekly_runs = (
            await db.fetchone(
                "SELECT COUNT(*) as cnt FROM runs WHERE run_date >= date('now', '-7 days')"
            )
        )["cnt"]
        checks.append(("Total Runs", str(total_runs)))
        checks.append(("Runs This Week", str(weekly_runs)))
    except Exception as e:
        checks.append(("Runs", f"❌ {e}"))
        status = "⚠️  ISSUES DETECTED"

    # Active injuries
    try:
        injuries = (
            await db.fetchone("SELECT COUNT(*) as cnt FROM injuries WHERE active = 1")
        )["cnt"]
        checks.append(("Active Injuries", str(injuries)))
    except Exception:
        pass

    # Uptime
    uptime_sec = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    checks.append(("Uptime", f"{hours}h {minutes}m {seconds}s"))

    # Disk
    try:
        disk = psutil.disk_usage(".")
        free_gb = disk.free / (1024**3)
        checks.append(("Disk Free", f"{free_gb:.1f} GB"))
        if free_gb < 1:
            checks.append(("⚠️  Low Disk", "Less than 1 GB free"))
            status = "⚠️  ISSUES DETECTED"
    except Exception:
        checks.append(("Disk", "N/A"))

    # Memory
    try:
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        checks.append(("Memory", f"{mem_pct:.0f}% used"))
        if mem_pct > 90:
            checks.append(("⚠️  High Memory", f"{mem_pct:.0f}% used"))
            status = "⚠️  ISSUES DETECTED"
    except Exception:
        checks.append(("Memory", "N/A"))

    # Config info
    if config:
        checks.append(("Mode", config.bot_mode))
        checks.append(("DB Path", config.coach_db_path))

    # Build report
    lines = [
        "🏥 *Service Health Report*\n",
        f"**Status:** {status}\n",
    ]
    for label, value in checks:
        lines.append(f"**{label}:** {value}")

    return "\n".join(lines)


async def git_commit_knowledge(path: str, message: str) -> str:
    try:
        subprocess.run(
            ["git", "add", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("git_commit_success", path=path, message=message)
            return f"✅ Committed: {message}"
        else:
            logger.warning("git_commit_no_changes", stderr=result.stderr)
            return "No changes to commit."
    except Exception as e:
        logger.error("git_commit_failed", error=str(e))
        return f"Git commit failed: {e}"
