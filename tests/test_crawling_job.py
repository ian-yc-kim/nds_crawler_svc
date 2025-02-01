import asyncio
import logging
import httpx
import pytest
from bs4 import BeautifulSoup

from nds_crawler_svc.crawling_job import start_crawling_job


class FakeResponse:
    def __init__(self, status_code, headers, text):
        self.status_code = status_code
        self.headers = headers
        self.text = text


class FakeAsyncClient:
    def __init__(self, responses):
        # responses: dict mapping url -> FakeResponse
        self.responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url, **kwargs):
        if url in self.responses:
            return self.responses[url]
        raise httpx.RequestError(f"URL not mocked: {url}")


@pytest.mark.asyncio
async def test_max_depth(monkeypatch):
    # Ensure that when depth exceeds 5, no HTTP fetch is attempted.
    call_counter = []

    async def fake_client_get(url, **kwargs):
        call_counter.append(1)
        return FakeResponse(200, {"content-type": "text/html"}, "<html></html>")

    # Setup FakeAsyncClient without any responses
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: FakeAsyncClient({}))
    monkeypatch.setattr("nds_crawler_svc.crawling_job.is_recently_crawled", lambda url, session: False)
    monkeypatch.setattr("nds_crawler_svc.crawling_job.store_crawled_data", lambda job_id, data: "fake_path")
    monkeypatch.setattr(FakeAsyncClient, "get", fake_client_get)

    await start_crawling_job("http://example.com", depth=6)
    assert len(call_counter) == 0


@pytest.mark.asyncio
async def test_deduplication(monkeypatch):
    # Simulate deduplication by forcing is_recently_crawled to return True
    get_called = False

    def fake_is_recently_crawled(url, session):
        nonlocal get_called
        get_called = True
        return True

    monkeypatch.setattr("nds_crawler_svc.crawling_job.is_recently_crawled", fake_is_recently_crawled)
    # Use a FakeAsyncClient that would raise error if called
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: FakeAsyncClient({}))

    await start_crawling_job("http://example.com", depth=0)
    # Since deduplication returns True, HTTP get should never be called
    assert get_called is True


@pytest.mark.asyncio
async def test_successful_fetch(monkeypatch):
    # Simulate a successful HTML fetch with one extracted link
    html_content = "<html><body><a href='http://example.com/page1'>Link1</a></body></html>"
    fake_response = FakeResponse(200, {"content-type": "text/html"}, html_content)

    # Create a FakeAsyncClient that returns the fake_response
    client_instance = FakeAsyncClient({"http://example.com": fake_response})
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: client_instance)
    monkeypatch.setattr("nds_crawler_svc.crawling_job.is_recently_crawled", lambda url, session: False)

    store_calls = []
    def fake_store(job_id, data):
        store_calls.append((job_id, data))
        return "fake_path"
    monkeypatch.setattr("nds_crawler_svc.crawling_job.store_crawled_data", fake_store)

    # To prevent actual recursion in test, override start_crawling_job for recursive calls
    original_start = start_crawling_job
    async def fake_recursive_start(url, depth):
        return
    monkeypatch.setattr("nds_crawler_svc.crawling_job.start_crawling_job", fake_recursive_start)

    await original_start("http://example.com", depth=0)
    assert len(store_calls) == 1
    job_id, data = store_calls[0]
    assert data.get("url") == "http://example.com"
    assert "http://example.com/page1" in data.get("links", [])
