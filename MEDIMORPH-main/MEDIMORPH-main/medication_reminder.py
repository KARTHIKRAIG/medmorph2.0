import schedule
import time
import threading
from datetime import datetime, timedelta
import re
import json
from flask_socketio import emit

class MedicationReminder:
    def __init__(self, socketio=None, mongo=None, app=None):
        self.reminder_thread = None
        self.is_running = False
        self.socketio = socketio
        self.mongo = mongo  # Use mongo.db for MongoDB operations
        self.app = app  # Store Flask app instance for context
        self.active_reminders = {}  # Store active reminders by user_id
    
    def setup_reminders_for_user(self, medication, user_id):
        """Set up reminders for a medication based on its frequency for a specific user (MongoDB version)"""
        if not self.mongo:
            print("MongoDB not configured in MedicationReminder.")
            return
        reminder_data = {
            'user_id': user_id,
            'medication_name': medication.get('medication_name'),
            'reminder_time': medication.get('reminder_time'),
            'created_at': datetime.utcnow(),
            'status': 'pending'
        }
        self.mongo.db.reminders.insert_one(reminder_data)

    def start_reminder_service(self):
        """Start the active reminder checking service"""
        if not self.is_running:
            self.is_running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()
            print("🔔 Medication reminder service started")

    def stop_reminder_service(self):
        """Stop the reminder service"""
        self.is_running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=1)
        print("🔕 Medication reminder service stopped")

    def _reminder_loop(self):
        """Main reminder checking loop - runs continuously (MongoDB version)"""
        while self.is_running:
            try:
                self._check_and_send_reminders()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Reminder loop error: {e}")
                time.sleep(60)  # Wait longer on error

    def _check_and_send_reminders(self):
        """Check for due reminders and send alerts (MongoDB version)"""
        if not self.mongo or not self.app:
            return
        try:
            with self.app.app_context():
                now = datetime.utcnow()
                due_reminders = list(self.mongo.db.reminders.find({
                    'reminder_time': {'$lte': now},
                    'status': 'pending'
                }))
                for reminder in due_reminders:
                    user_id = reminder['user_id']
                    med_name = reminder.get('medication_name', 'Medication')
                    # Send real-time notification if socketio is available
                    if self.socketio:
                        self.socketio.emit('reminder', {
                            'user_id': str(user_id),
                            'message': f"Time to take your medication: {med_name}"
                        })
                    # Mark reminder as sent
                    self.mongo.db.reminders.update_one(
                        {'_id': reminder['_id']},
                        {'$set': {'status': 'sent', 'sent_at': now}}
                    )
        except Exception as e:
            print(f"❌ Reminder check error: {e}")
