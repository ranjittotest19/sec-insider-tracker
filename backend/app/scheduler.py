"""
Background scheduler — polls EDGAR every 15 minutes for new Form 4 and 13D/13G filings.
Started automatically when the FastAPI app boots.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.edgar_form4 import ingest_recent_filings
from app.services.edgar_13dg import ingest_recent_13dg

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def poll_form4():
    try:
        n = ingest_recent_filings()
        if n:
            logger.info(f"[Scheduler] Form 4: inserted {n} new records")
    except Exception as e:
        logger.error(f"[Scheduler] Form 4 error: {e}")


def poll_13dg():
    try:
        n = ingest_recent_13dg()
        if n:
            logger.info(f"[Scheduler] 13D/13G: inserted {n} new records")
    except Exception as e:
        logger.error(f"[Scheduler] 13D/13G error: {e}")


def start():
    scheduler.add_job(poll_form4, IntervalTrigger(minutes=15), id="form4_poll", replace_existing=True)
    scheduler.add_job(poll_13dg, IntervalTrigger(minutes=20), id="13dg_poll", replace_existing=True)
    scheduler.start()
    logger.info("[Scheduler] Started — polling Form 4 every 15 min, 13D/13G every 20 min")


def stop():
    scheduler.shutdown()
