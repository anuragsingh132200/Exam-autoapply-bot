"""
MongoDB Database Service
Provides async MongoDB connection using Motor and Beanie ODM.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from app.config import settings


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect(cls):
        """Initialize MongoDB connection and Beanie ODM."""
        cls.client = AsyncIOMotorClient(settings.mongodb_uri)
        
        # Import models here to avoid circular imports
        from app.models.exam import Exam
        from app.models.user import User
        from app.models.session import WorkflowSession
        from app.models.field_mapping import FieldMapping
        from app.models.analytics import ExamAnalytics
        
        # Initialize Beanie with document models
        await init_beanie(
            database=cls.client[settings.database_name],
            document_models=[
                Exam,
                User,
                WorkflowSession,
                FieldMapping,
                ExamAnalytics,
            ]
        )
        print(f"✅ Connected to MongoDB: {settings.database_name}")
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("❌ Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        if not cls.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.client[settings.database_name]


# Convenience function for dependency injection
async def get_db():
    """FastAPI dependency for database access."""
    return Database.get_database()
