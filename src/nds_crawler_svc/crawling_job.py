import asyncio
import datetime
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from nds_crawler_svc.service.deduplication import is_recently_crawled
from nds_crawler_svc.storage import store_crawled_data
from nds_crawler_svc.models.base import SessionLocal


async def start_crawling_job(url: str, depth: int = 0) -> None:
    """
    Asynchronous function to start a crawling job for the given URL.
    Recursively crawls links extracted from the page up to a maximum depth of 5.
    """
    # Validate URL
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ('http', 'https'):
        logging.error(f"Invalid URL scheme: {url}")
        return

    # Enforce maximum depth
    if depth > 5:
        logging.info(f"Maximum crawling depth reached for URL: {url}")
        return

    # Deduplication check
    session = SessionLocal()
    try:
        if is_recently_crawled(url, session):
            logging.info(f"URL already crawled recently: {url}")
            return
    except Exception as e:
        logging.error(e, exc_info=True)
        return
    finally:
        session.close()

    async with httpx.AsyncClient(timeout=10) as client:
        response = None
        # Attempt standard fetch
        try:
            response = await client.get(url)
        except Exception as e:
            logging.error(f"Standard fetch failed for {url}: {e}", exc_info=True)

        # If standard fetch fails or non-200 status, attempt fallback dynamic content retrieval
        if response is None or response.status_code != 200:
            fallback_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            try:
                response = await client.get(url, headers=fallback_headers)
            except Exception as e:
                logging.error(f"Dynamic fetch failed for {url}: {e}", exc_info=True)
                return

        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and "text/html" in content_type:
            try:
                soup = BeautifulSoup(response.text, "html.parser")
                links = []
                # Extract all href links from <a> tags
                for tag in soup.find_all("a", href=True):
                    link = tag.get("href")
                    if link:
                        links.append(link)
            except Exception as e:
                logging.error(f"Error parsing HTML for {url}: {e}", exc_info=True)
                return

            # Prepare job data and store crawled data
            job_id = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            data = {"url": url, "links": links}
            try:
                store_result = store_crawled_data(job_id, data)
                logging.info(f"Stored crawled data for URL {url}: {store_result}")
            except Exception as e:
                logging.error(f"Error storing crawled data for {url}: {e}", exc_info=True)

            # Recursively crawl extracted links concurrently
            tasks = []
            for link in links:
                tasks.append(asyncio.create_task(start_crawling_job(link, depth + 1)))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logging.error(f"Non-HTML content or unsuccessful response for {url}. Status code: {response.status_code}")
