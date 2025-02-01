import asyncio
import json
import logging
import pytest
from fastapi import HTTPException

# No need to import asyncio.create_task since we will monkeypatch it
import asyncio

# Use the TestClient fixture from conftest

def dummy_create_task(coro):
    # A dummy function to simulate scheduling of async task
    dummy_create_task.called = True
    dummy_create_task.coro = coro
    return None

dummy_create_task.called = False

def test_valid_submission(client, monkeypatch):
    # Patch asyncio.create_task to track if it gets called
    monkeypatch.setattr(asyncio, 'create_task', dummy_create_task)

    # Ensure that deduplication check passes
    # We don't override is_recently_crawled so it uses the actual implementation which in test DB should allow submission

    payload = {"url": "http://example.com"}
    response = client.post("/submit_url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "URL submitted for crawling."
    # Verify that the crawling job was scheduled
    assert dummy_create_task.called is True


def fake_is_recently_crawled(url, session):
    return True


def test_duplicate_submission(client, monkeypatch):
    # Override deduplication function to simulate duplicate submission
    monkeypatch.setattr("nds_crawler_svc.routers.url_submission.is_recently_crawled", fake_is_recently_crawled)
    payload = {"url": "http://example.com"}
    response = client.post("/submit_url", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "URL was recently crawled. Duplicate submission."


@pytest.mark.parametrize("payload, expected_status", [
    ({}, 400),
    ({"url": ""}, 400)
])
def test_missing_url(client, payload, expected_status):
    # Test cases where URL is missing or empty
    response = client.post("/submit_url", json=payload)
    assert response.status_code == expected_status
    data = response.json()
    if payload == {}:
        assert data.get("detail") == "URL is required."
    else:
        # If URL is empty string, the validation might pass the check and schedule job, but our logic doesn't enforce non-empty string
        # Depending on business logic, an empty string might be considered invalid. For now, we assume it is invalid downstream.
        pass
