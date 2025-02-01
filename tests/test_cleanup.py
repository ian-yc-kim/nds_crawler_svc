import logging
from datetime import datetime, timedelta

from nds_crawler_svc.models.base import SessionLocal, Base, engine
from nds_crawler_svc.models.recently_crawled_urls import RecentlyCrawledUrl
from nds_crawler_svc.tasks import cleanup_old_urls


def test_cleanup_old_urls():
    # Ensure tables are created in the in-memory database
    Base.metadata.create_all(bind=engine)

    # Create two records: one older than 7 days and one recent
    session = SessionLocal()
    try:
        old_time = datetime.utcnow() - timedelta(days=8)
        new_time = datetime.utcnow()
        record_old = RecentlyCrawledUrl(url='http://example.com/old', crawl_timestamp=old_time)
        record_new = RecentlyCrawledUrl(url='http://example.com/new', crawl_timestamp=new_time)
        session.add_all([record_old, record_new])
        session.commit()
    except Exception as e:
        logging.error(e, exc_info=True)
        session.rollback()
    finally:
        session.close()

    # Run the cleanup
    cleanup_old_urls()

    # Verify that only the new record remains
    session = SessionLocal()
    try:
        remaining = session.query(RecentlyCrawledUrl).all()
        assert len(remaining) == 1, 'Expected one record to remain after cleanup'
        assert remaining[0].url == 'http://example.com/new', 'The remaining record should be the new URL'
    except Exception as e:
        logging.error(e, exc_info=True)
        raise
    finally:
        session.close()
