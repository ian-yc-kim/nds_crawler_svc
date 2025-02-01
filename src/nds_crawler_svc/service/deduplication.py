import datetime
import logging

from sqlalchemy.orm import Session
from nds_crawler_svc.models.recently_crawled_urls import RecentlyCrawledUrl


def is_recently_crawled(url: str, session: Session) -> bool:
    """
    Check if the given URL was crawled within the last 7 days.

    Parameters:
    - url: The URL to check.
    - session: SQLAlchemy Session instance.

    Returns:
    - True if a record for the URL exists with crawl_timestamp within the last 7 days, else False.
    """
    try:
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        record = session.query(RecentlyCrawledUrl).filter(
            RecentlyCrawledUrl.url == url,
            RecentlyCrawledUrl.crawl_timestamp >= seven_days_ago
        ).first()
        return record is not None
    except Exception as e:
        logging.error(e, exc_info=True)
        return False
