import asyncio
import pytest

# Dummy async task scheduler for testing

def dummy_create_task(coro):
    dummy_create_task.called = True
    dummy_create_task.coro = coro
    return None

dummy_create_task.called = False

def reset_dummy_create_task():
    dummy_create_task.called = False
    dummy_create_task.coro = None


def test_invalid_json_payload(client):
    # Sending an invalid JSON payload
    response = client.post("/submit", data="Not a JSON")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid JSON object" in data.get("detail", "")


def test_payload_not_object(client):
    response = client.post("/submit", json=["http://example.com"])
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "Payload must be a JSON object."


def test_missing_urls_key(client):
    response = client.post("/submit", json={"not_urls": []})
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "Missing 'urls' key in payload."


def test_urls_not_list(client):
    response = client.post("/submit", json={"urls": "http://example.com"})
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "'urls' must be a list."


def test_exceeding_maximum_urls(client):
    # Generate 101 URLs
    urls = [f"http://example.com/{i}" for i in range(101)]
    response = client.post("/submit", json={"urls": urls})
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "Maximum 100 URLs allowed."


def test_no_valid_urls(client):
    # All URLs are invalid
    response = client.post("/submit", json={"urls": ["ftp://example.com", "invalidurl"]})
    assert response.status_code == 400
    data = response.json()
    assert data.get("detail") == "No valid URLs provided"


def test_valid_submission(monkeypatch, client):
    reset_dummy_create_task()
    monkeypatch.setattr(asyncio, 'create_task', dummy_create_task)
    # Include duplicates and an invalid url in the payload
    urls = ["http://example.com", "https://example.org", "invalid", "http://example.com"]
    response = client.post("/submit", json={"urls": urls})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data.get("status") == "Crawling jobs initiated"
    # Only unique valid URLs should be scheduled: "http://example.com" and "https://example.org"
    assert dummy_create_task.called is True
