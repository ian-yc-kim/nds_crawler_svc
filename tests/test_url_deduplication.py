import pytest
from datetime import datetime, timedelta

from nds_crawler_svc.models.recently_crawled_urls import RecentlyCrawledUrl


def test_duplicate_url(client, db_session):
    # Insert a record with crawl_timestamp within the last 7 days
    session = db_session
    url = "http://example.com/duplicate"
    record = RecentlyCrawledUrl(url=url, crawl_timestamp=datetime.utcnow())
    session.add(record)
    session.commit()
    
    response = client.post("/submit_url", json={"url": url})
    assert response.status_code == 400
    assert "recently crawled" in response.json().get("detail", "")


def test_non_duplicate_url(client, db_session):
    # Insert a record with crawl_timestamp older than 7 days
    session = db_session
    url = "http://example.com/nonduplicate"
    record = RecentlyCrawledUrl(url=url, crawl_timestamp=datetime.utcnow() - timedelta(days=10))
    session.add(record)
    session.commit()
    
    response = client.post("/submit_url", json={"url": url})
    assert response.status_code == 200
    assert "submitted" in response.json().get("message", "")


def test_new_url_submission(client):
    # Submit URL that does not exist in the database
    url = "http://example.com/new"
    response = client.post("/submit_url", json={"url": url})
    assert response.status_code == 200
    assert "submitted" in response.json().get("message", "")
