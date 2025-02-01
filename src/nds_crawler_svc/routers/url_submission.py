from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from nds_crawler_svc.models.base import get_db
from nds_crawler_svc.service.deduplication import is_recently_crawled

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
    
    # Simulate successful processing (e.g., enqueue crawling job)
    return {"message": "URL submitted for crawling."}
