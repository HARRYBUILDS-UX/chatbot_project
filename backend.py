import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def get_db():
    """Establish a connection and return the database instance."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")  # Use env variable
    client = MongoClient(mongo_uri)
    return client["chatbot_db"]

def store_document(file_name, content):
    """Stores or updates document content in MongoDB efficiently."""
    db = get_db()
    collection = db["documents"]

    try:
        result = collection.update_one(
            {"file_name": file_name},  # Check if document exists
            {"$set": {"content": content}},  # Update content if exists
            upsert=True  # Insert if not exists
        )

        if result.matched_count > 0:
            return f"Document '{file_name}' updated successfully."
        else:
            return f"Document '{file_name}' stored successfully."

    except pymongo.errors.PyMongoError as e:
        return f"Error storing document: {e}"

def get_documents():
    """Fetch all stored documents (file names only)."""
    db = get_db()
    collection = db["documents"]

    try:
        return list(collection.find({}, {"_id": 0, "file_name": 1}))
    except pymongo.errors.PyMongoError as e:
        return f"Error fetching documents: {e}"

def get_document_by_name(file_name):
    """Fetch a specific document by name."""
    db = get_db()
    collection = db["documents"]

    try:
        return collection.find_one({"file_name": file_name}, {"_id": 0})
    except pymongo.errors.PyMongoError as e:
        return f"Error fetching document: {e}"

