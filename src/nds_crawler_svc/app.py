from fastapi import FastAPI
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from nds_crawler_svc.routers import url_submission
from nds_crawler_svc.tasks import cleanup_old_urls

app = FastAPI(debug=True)

app.include_router(url_submission.router)

scheduler = BackgroundScheduler()

@app.on_event("startup")
async def startup_event():
    try:
        # Schedule the cleanup_old_urls job to run every 1 day
        scheduler.add_job(cleanup_old_urls, 'interval', days=1)
        scheduler.start()
        # Run an immediate cleanup on startup
        cleanup_old_urls()
        app.state.scheduler = scheduler
    except Exception as e:
        logging.error(e, exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    try:
        if hasattr(app.state, "scheduler"):
            app.state.scheduler.shutdown()
    except Exception as e:
        logging.error(e, exc_info=True)
