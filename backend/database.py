"""
Database Configuration
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    
    def __init__(self):
        # Get MongoDB URI from environment or use default
        self.MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.DB_NAME = os.getenv('DB_NAME', 'deepfake_detection')
        
        # Collection names
        self.COLLECTION_DETECTIONS = 'detections'
        
        # Connection
        self.client = None
        self.db = None
        
    def connect(self):
        try:
            self.client = MongoClient(self.MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.server_info()
            
            # Get database
            self.db = self.client[self.DB_NAME]
            
            # Create indexes
            self._create_indexes()
            
            print(f"Connected to MongoDB: {self.DB_NAME}")
            return True
            
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    def _create_indexes(self):
        if self.db is None:
            return
        
        collection = self.db[self.COLLECTION_DETECTIONS]
        
        # Index on file_hash for fast duplicate checking
        collection.create_index('file_hash', unique=True)
        
        # Index on timestamp for history queries
        collection.create_index('timestamp')
        
        # Index on content_type for filtering
        collection.create_index('content_type')
        
        # Index on verdict for statistics
        collection.create_index('verdict')
        
        print("Database indexes created")
    
    def get_collection(self, collection_name):
        if self.db is None:
            raise Exception("Database not connected")
        return self.db[collection_name]
    
    def close(self):
        if self.client:
            self.client.close()
            print("Database connection closed")
    
    def is_connected(self):
        if self.client is None:
            return False
        
        try:
            self.client.server_info()
            return True
        except:
            return False


# Global database instance
db_config = DatabaseConfig()


def get_db():
    if not db_config.is_connected():
        db_config.connect()
    return db_config.db


def get_detections_collection():
    return db_config.get_collection(db_config.COLLECTION_DETECTIONS)
