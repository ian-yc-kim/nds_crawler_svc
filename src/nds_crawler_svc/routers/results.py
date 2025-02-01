from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import os
import json
import logging
from typing import List, Any

router = APIRouter()

class CrawlResult(BaseModel):
    url: str
    title: str
    metadata: Any
    content: str

class PaginatedResults(BaseModel):
    results: List[CrawlResult]
    current_page: int
    total_pages: int

@router.get("/results/{job_id}", response_model=PaginatedResults)
def get_crawl_results(job_id: str, page: int = Query(1, gt=0)) -> PaginatedResults:
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id must be a non-empty string")
    directory = os.path.join("data", job_id)
    if not os.path.exists(directory) or not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail="Job results not found")
    try:
        files = [f for f in os.listdir(directory) if f.endswith('.json')]
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error reading job directory")
    try:
        # Sort files in descending order based on the timestamp part of the filename
        files.sort(key=lambda x: x.rstrip('.json'), reverse=True)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error sorting files")
    results = []
    for file_name in files:
        file_path = os.path.join(directory, file_name)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            if all(k in data for k in ("url", "title", "metadata", "content")):
                results.append(data)
        except Exception as e:
            logging.error(e, exc_info=True)
            # Skip malformed files and continue processing
            continue
    total_items = len(results)
    page_size = 100
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page number out of range")
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_results = results[start_index:end_index]
    return PaginatedResults(results=paginated_results, current_page=page, total_pages=total_pages)
