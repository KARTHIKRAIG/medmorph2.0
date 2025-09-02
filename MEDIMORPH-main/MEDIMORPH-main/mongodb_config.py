import os
from pymongo import MongoClient
from flask_pymongo import PyMongo

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "medimorph"

# MongoDB Client
def get_mongodb_client():
    """Get MongoDB client instance"""
    try:
        client = MongoClient(MONGODB_URI)
        # Test the connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return client
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None

# Flask-PyMongo Configuration
def configure_mongodb(app):
    """Configure Flask app with MongoDB"""
    app.config['MONGO_URI'] = MONGODB_URI + MONGODB_DB
    mongo = PyMongo(app)
    
    # Initialize collections
    init_collections(mongo.db)
    
    return mongo

def init_collections(db):
    """Initialize MongoDB collections with proper indexes"""
    try:
        # Users collection
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
        db.users.create_index('email', unique=True)
        db.users.create_index('username', unique=True)
        
        # Medications collection
        if 'medications' not in db.list_collection_names():
            db.create_collection('medications')
        db.medications.create_index('user_id')
        db.medications.create_index('medication_name')
        
        # Prescriptions collection
        if 'prescriptions' not in db.list_collection_names():
            db.create_collection('prescriptions')
        db.prescriptions.create_index('user_id')
        db.prescriptions.create_index('upload_date')
        
        # Health records collection
        if 'health_records' not in db.list_collection_names():
            db.create_collection('health_records')
        db.health_records.create_index('user_id')
        db.health_records.create_index('record_date')
        
        # Reminders collection
        if 'reminders' not in db.list_collection_names():
            db.create_collection('reminders')
        db.reminders.create_index('user_id')
        db.reminders.create_index('reminder_time')
        
        print("✅ MongoDB collections initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing collections: {e}")

def get_database():
    """Get database instance"""
    client = get_mongodb_client()
    if client:
        return client[MONGODB_DB]
    return None

def close_connection(client):
    """Close MongoDB connection"""
    if client:
        client.close()
        print("✅ MongoDB connection closed")
