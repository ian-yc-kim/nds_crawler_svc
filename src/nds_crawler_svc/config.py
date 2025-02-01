import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
SERVICE_URL = os.getenv("SERVICE_URL", "0.0.0.0")
SERVICE_PORT = os.getenv("SERVICE_PORT", 8000)