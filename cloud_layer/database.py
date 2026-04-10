import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "smarteyes")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_db():
    if not MONGO_URI or "username" in MONGO_URI:
        print("WARNING: MONGO_URI is not set properly, check your .env file. Falling back to local MongoDB.")
        uri = "mongodb://localhost:27017"
    else:
        uri = MONGO_URI
    
    print(f"Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(uri)
    db.db = db.client[DB_NAME]
    print("Connected to MongoDB!")

async def close_db():
    if db.client:
        db.client.close()
        print("MongoDB connection closed.")

def get_db():
    return db.db
