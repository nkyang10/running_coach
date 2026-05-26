from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from app.database import Database
from app.logger import get_logger

logger = get_logger(__name__)


class HealthMonitor:
    def __init__(self, db: Database, alert_callback=None) -> None:
        self.db = db
        self.alert_callback = alert_callback
        self._last_check: Optional[float] = None
        self._consecutive_failures = 0
        self._max_consecutive = 3

    async def check(self) -> dict[str, any]:
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": False,
            "healthy": False,
            "errors": [],
        }

        try:
            await self.db.fetchone("SELECT 1")
            results["database"] = True
        except Exception as e:
            results["errors"].append(f"database: {e}")

        results["healthy"] = results["database"]

        self._last_check = time.time()
        if not results["healthy"]:
            self._consecutive_failures += 1
            if (
                self._consecutive_failures >= self._max_consecutive
                and self.alert_callback
            ):
                await self.alert_callback(
                    f"⚠️ Health check failed {self._consecutive_failures}x\n"
                    + "\n".join(results["errors"])
                )
        else:
            self._consecutive_failures = 0

        return results


async def run_health_loop(monitor: HealthMonitor, interval_seconds: int = 3600) -> None:
    while True:
        result = await monitor.check()
        if result["healthy"]:
            logger.debug("health_check_ok")
        else:
            logger.error("health_check_failed", errors=result["errors"])
        await asyncio.sleep(interval_seconds)
