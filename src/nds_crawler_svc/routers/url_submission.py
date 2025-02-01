from fastapi import APIRouter, Depends, HTTPException
import asyncio
import logging
from sqlalchemy.orm import Session

from nds_crawler_svc.models.base import get_db
from nds_crawler_svc.service.deduplication import is_recently_crawled
from nds_crawler_svc.crawling_job import start_crawling_job

router = APIRouter()

@router.post("/submit_url")
async def submit_url(payload: dict, session: Session = Depends(get_db)):
    """
    Endpoint to submit a URL for crawling.
    Request JSON should have a "url" key.
    """
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    
    try:
        if is_recently_crawled(url, session):
            raise HTTPException(status_code=400, detail="URL was recently crawled. Duplicate submission.")
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    # Trigger the crawling job asynchronously without affecting the immediate HTTP response.
    try:
        asyncio.create_task(start_crawling_job(url, depth=0))
    except Exception as e:
        logging.error(e, exc_info=True)
    
    return {"message": "URL submitted for crawling."}
