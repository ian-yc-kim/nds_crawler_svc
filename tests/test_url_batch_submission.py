import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

# Helper function to create a fake asyncio.create_task
# which increments the provided counter and returns a dummy task

def fake_create_task(coro, counter):
    counter["count"] += 1
    # Return a dummy task using asyncio.sleep
    return asyncio.create_task(asyncio.sleep(0))


@pytest.fixture
def patch_create_task(monkeypatch):
    # This fixture patches asyncio.create_task to count calls
    counter = {"count": 0}

    # Define a wrapper that calls the original fake function with our counter
    def create_task_wrapper(coro):
        counter["count"] += 1
        # Instead of scheduling the actual task, we return a dummy completed future
        return asyncio.create_task(asyncio.sleep(0))

    # Instead of using the wrapper above directly (which would recurse), we patch it
    # by creating our own fake that simply increments the counter and returns a dummy task.
    # To avoid recursion, we use a lambda that returns an already scheduled dummy task.
    def custom_create_task(coro):
        counter["count"] += 1
        return asyncio.sleep(0)

    monkeypatch.setattr(asyncio, "create_task", custom_create_task)
    return counter


def test_valid_payload(client, monkeypatch):
    # Patch create_task to count calls
    counter = {"count": 0}
    def custom_create_task(coro):
        counter["count"] += 1
        # Return a dummy coroutine that is already done
        return asyncio.sleep(0)
    monkeypatch.setattr(asyncio, "create_task", custom_create_task)

    payload = {
        "urls": [
            "http://example.com/1",
            "https://example.com/2",
            "http://example.com/3"
        ]
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert "job_id" in data
    assert data.get("status") == "Crawling jobs initiated"
    # Expect exactly 3 tasks scheduled
    assert counter["count"] == 3


def test_duplicate_urls(client, monkeypatch):
    counter = {"count": 0}
    def custom_create_task(coro):
        counter["count"] += 1
        return asyncio.sleep(0)
    monkeypatch.setattr(asyncio, "create_task", custom_create_task)

    payload = {
        "urls": [
            "http://example.com/1",
            "http://example.com/1",
            "https://example.com/2",
            "http://example.com/1"
        ]
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data.get("status") == "Crawling jobs initiated"
    # There are 2 unique urls
    assert counter["count"] == 2


def test_exceed_max_urls(client):
    # Create a payload with 101 valid urls
    urls = [f"http://example.com/{i}" for i in range(101)]
    payload = {"urls": urls}
    response = client.post("/submit", json=payload)
    assert response.status_code == 400
    data = response.json()
    # Check that the error detail mentions the 100 URL limit
    assert "Maximum 100 URLs allowed" in data.get("detail", "")


@pytest.mark.parametrize("payload", [
    {"urls": []},
    {"urls": ["invalid_url", "www.example.com"]}
])
def test_empty_and_invalid_urls(client, payload):
    response = client.post("/submit", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "No valid URLs provided" in data.get("detail", "")


def test_malformed_json(client):
    # Sending malformed JSON data (string that is not JSON formatted)
    headers = {"Content-Type": "application/json"}
    response = client.post("/submit", data='not a json', headers=headers)
    assert response.status_code == 400
    data = response.json()
    # The error message is expected to indicate invalid JSON
    assert "Invalid JSON object." in data.get("detail", "")


def test_concurrent_submissions(client, monkeypatch):
    # Global counter to count asynchronous task scheduling across concurrent submissions
    counter = {"count": 0}

    def custom_create_task(coro):
        counter["count"] += 1
        return asyncio.sleep(0)
    monkeypatch.setattr(asyncio, "create_task", custom_create_task)

    def send_request():
        payload = {"urls": ["http://example.com/a", "https://example.com/b"]}
        resp = client.post("/submit", json=payload)
        return resp

    # Simulate 5 concurrent submissions using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_request) for _ in range(5)]
        responses = [future.result() for future in futures]

    # Verify each response
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data.get("status") == "Crawling jobs initiated"

    # Each submission should schedule 2 tasks
    assert counter["count"] == 5 * 2


def test_performance_large_batch(client, monkeypatch):
    counter = {"count": 0}
    def custom_create_task(coro):
        counter["count"] += 1
        return asyncio.sleep(0)
    monkeypatch.setattr(asyncio, "create_task", custom_create_task)

    # Generate 99 unique valid URLs
    urls = [f"http://example.com/{i}" for i in range(99)]
    payload = {"urls": urls}
    response = client.post("/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data.get("status") == "Crawling jobs initiated"
    # Verify that 99 tasks were scheduled
    assert counter["count"] == 99
