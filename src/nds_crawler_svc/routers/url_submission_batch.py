from fastapi import APIRouter, Request, HTTPException
import asyncio
import datetime
import logging

from nds_crawler_svc.crawling_job import start_crawling_job

router = APIRouter()

@router.post("/submit")
async def submit_batch_urls(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid JSON object.")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object.")

    if "urls" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'urls' key in payload.")

    urls = payload.get("urls")
    if not isinstance(urls, list):
        raise HTTPException(status_code=400, detail="'urls' must be a list.")

    if len(urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs allowed.")

    valid_urls = set()
    for url in urls:
        if isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
            valid_urls.add(url)

    if not valid_urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")

    job_id = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

    for url in valid_urls:
        try:
            asyncio.create_task(start_crawling_job(url))
        except Exception as e:
            logging.error(e, exc_info=True)

    logging.info(f"Batch URL submission processed with job_id: {job_id}")
    return {"job_id": job_id, "status": "Crawling jobs initiated"}
