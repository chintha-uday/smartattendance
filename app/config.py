import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = os.getenv("APP_NAME", "Smart Attendance")
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    APP_ENV = os.getenv("APP_ENV", "development")
    TIME_ZONE = os.getenv("TIME_ZONE", "India Standard Time")
    DB_URL = os.getenv("DB_URL", "sqlite:///./smartattendance_dev.db")

settings = Settings()
