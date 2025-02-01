import logging
from datetime import datetime, timedelta

from nds_crawler_svc.models.base import SessionLocal
from nds_crawler_svc.models.recently_crawled_urls import RecentlyCrawledUrl


def cleanup_old_urls() -> None:
    session = SessionLocal()
    try:
        threshold = datetime.utcnow() - timedelta(days=7)
        # Delete records older than 7 days
        session.query(RecentlyCrawledUrl).filter(RecentlyCrawledUrl.crawl_timestamp < threshold).delete(synchronize_session=False)
        session.commit()
        logging.info('Cleanup old URLs task completed successfully.')
    except Exception as e:
        logging.error(e, exc_info=True)
        session.rollback()
    finally:
        session.close()
