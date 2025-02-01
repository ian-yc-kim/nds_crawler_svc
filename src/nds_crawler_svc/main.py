import logging

import uvicorn
from nds_crawler_svc.app import app
from nds_crawler_svc.config import SERVICE_URL, SERVICE_PORT


# Set up logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    service_url = SERVICE_URL
    service_port = int(SERVICE_PORT)
    uvicorn.run(app, host=service_url, port=service_port)


if __name__ == "__main__":
    # Entry point for the application
    main()