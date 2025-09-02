#!/usr/bin/env python3
"""
MongoDB Setup Script for MEDIMORPH
This script initializes the MongoDB database and creates sample data.
"""

import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mongodb_config import get_mongodb_client, init_collections

def create_sample_data(db):
    """Create sample data for testing"""
    try:
        # Create sample users
        sample_users = [
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': 'pbkdf2:sha256:600000$test_hash',  # This is just for demo
                'created_at': datetime.utcnow(),
                'is_active': True
            },
            {
                'username': 'demo_user',
                'email': 'demo@example.com',
                'password_hash': 'pbkdf2:sha256:600000$demo_hash',  # This is just for demo
                'created_at': datetime.utcnow(),
                'is_active': True
            }
        ]
        
        # Insert users
        for user in sample_users:
            existing = db.users.find_one({'email': user['email']})
            if not existing:
                db.users.insert_one(user)
                print(f"✅ Created user: {user['username']}")
            else:
                print(f"ℹ️ User already exists: {user['username']}")
        
        # Create sample medications
        sample_medications = [
            {
                'user_id': db.users.find_one({'username': 'testuser'})['_id'],
                'medication_name': 'Aspirin',
                'dosage': '100mg',
                'frequency': 'Once daily',
                'start_date': datetime.utcnow(),
                'end_date': datetime.utcnow() + timedelta(days=30),
                'notes': 'Take with food',
                'created_at': datetime.utcnow()
            },
            {
                'user_id': db.users.find_one({'username': 'testuser'})['_id'],
                'medication_name': 'Vitamin D',
                'dosage': '1000 IU',
                'frequency': 'Once daily',
                'start_date': datetime.utcnow(),
                'end_date': None,
                'notes': 'Take in the morning',
                'created_at': datetime.utcnow()
            }
        ]
        
        # Insert medications
        for med in sample_medications:
            existing = db.medications.find_one({
                'user_id': med['user_id'],
                'medication_name': med['medication_name']
            })
            if not existing:
                db.medications.insert_one(med)
                print(f"✅ Created medication: {med['medication_name']}")
            else:
                print(f"ℹ️ Medication already exists: {med['medication_name']}")
        
        # Create sample health records
        sample_health_records = [
            {
                'user_id': db.users.find_one({'username': 'testuser'})['_id'],
                'record_type': 'Blood Pressure',
                'value': '120/80',
                'unit': 'mmHg',
                'record_date': datetime.utcnow(),
                'notes': 'Normal reading',
                'created_at': datetime.utcnow()
            },
            {
                'user_id': db.users.find_one({'username': 'testuser'})['_id'],
                'record_type': 'Weight',
                'value': '70',
                'unit': 'kg',
                'record_date': datetime.utcnow(),
                'notes': 'Morning weight',
                'created_at': datetime.utcnow()
            }
        ]
        
        # Insert health records
        for record in sample_health_records:
            existing = db.health_records.find_one({
                'user_id': record['user_id'],
                'record_type': record['record_type'],
                'record_date': record['record_date']
            })
            if not existing:
                db.health_records.insert_one(record)
                print(f"✅ Created health record: {record['record_type']}")
            else:
                print(f"ℹ️ Health record already exists: {record['record_type']}")
        
        # Create sample reminders
        sample_reminders = [
            {
                'user_id': db.users.find_one({'username': 'testuser'})['_id'],
                'medication_name': 'Aspirin',
                'reminder_time': datetime.utcnow() + timedelta(hours=1),
                'message': 'Time to take your Aspirin',
                'is_active': True,
                'created_at': datetime.utcnow()
            }
        ]
        
        # Insert reminders
        for reminder in sample_reminders:
            existing = db.reminders.find_one({
                'user_id': reminder['user_id'],
                'medication_name': reminder['medication_name'],
                'reminder_time': reminder['reminder_time']
            })
            if not existing:
                db.reminders.insert_one(reminder)
                print(f"✅ Created reminder: {reminder['medication_name']}")
            else:
                print(f"ℹ️ Reminder already exists: {reminder['medication_name']}")
        
        print("\n✅ Sample data creation completed!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

def main():
    """Main setup function"""
    print("🏥 MEDIMORPH MongoDB Setup")
    print("=" * 40)
    
    # Test MongoDB connection
    print("🔌 Testing MongoDB connection...")
    client = get_mongodb_client()
    
    if not client:
        print("❌ Failed to connect to MongoDB!")
        print("Please ensure MongoDB is running on localhost:27017")
        return False
    
    try:
        # Get database
        db = client['medimorph']
        print(f"✅ Connected to database: {db.name}")
        
        # Initialize collections
        print("\n🗄️ Initializing collections...")
        init_collections(db)
        
        # Create sample data
        print("\n📊 Creating sample data...")
        create_sample_data(db)
        
        # Show database stats
        print("\n📈 Database Statistics:")
        print(f"Users: {db.users.count_documents({})}")
        print(f"Medications: {db.medications.count_documents({})}")
        print(f"Health Records: {db.health_records.count_documents({})}")
        print(f"Reminders: {db.reminders.count_documents({})}")
        
        print("\n🎉 MongoDB setup completed successfully!")
        print("You can now run the MEDIMORPH application.")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    finally:
        client.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

