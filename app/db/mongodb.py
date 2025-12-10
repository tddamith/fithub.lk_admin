import motor.motor_asyncio
from app.core.config import settings
import logging

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB]
            logging.info(f"Connected to MongoDB: {settings.MONGO_DB}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logging.info("MongoDB connection closed.")

    async def get_collection(self, collection_name: str):
        """
        Get a collection from the database. MongoDB creates collections lazily.
        """
        if self.db is None:
            raise Exception("Database connection is not established. Call connect() first.")

        collections = await self.db.list_collection_names()
        if collection_name not in collections:
            create_collection_if_not_exists = await self.create_collection_if_not_exists(collection_name)
            # logging.info(f"Collection '{collection_name}' does not exist. Creating it implicitly.")
        
        return self.db[collection_name]

    async def create_collection_if_not_exists(self, collection_name: str):
        """Explicitly create a collection if it doesn't exist."""
        if self.db is None:
            raise Exception("Database connection is not established. Call connect() first.")

        existing_collections = await self.db.list_collection_names()
        if collection_name not in existing_collections:
            await self.db.create_collection(collection_name)
            logging.info(f"Collection '{collection_name}' created.")
        else:
            logging.info(f"Collection '{collection_name}' already exists.")
