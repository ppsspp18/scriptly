import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_NAME = "scriptly"

client = AsyncIOMotorClient(os.environ["MONGODB_URL"])
database = client[DATABASE_NAME]

bookmark_collection = database["bookmarks"]
settings_collection = database["settings"]
