from fastapi import FastAPI
from nds_crawler_svc.routers import url_submission

app = FastAPI(debug=True)

app.include_router(url_submission.router)
