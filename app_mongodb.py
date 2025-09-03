#!/usr/bin/env python3
"""
MEDIMORPH - AI-Powered Prescription Digitization & Medication Reminder System
MongoDB Version

This version uses MongoDB instead of SQLite for data storage.
Connection string: mongodb://localhost:27017/
Database: medimorph_db
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import threading
import time
import json
from bson import ObjectId

# Import MongoDB configuration and models
from mongodb_config import (
    init_mongodb, test_mongodb_connection, create_default_users, get_database_stats,
    User, Medication, Reminder, MedicationLog, PrescriptionUpload
)

# Import AI components
from prescription_ocr import PrescriptionOCR
from ai_processor import AIProcessor
from medication_reminder import MedicationReminder

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    try:
        return User.objects(id=ObjectId(user_id)).first()
    except:
        return None

# Initialize AI components
ocr_processor = PrescriptionOCR()
ai_processor = AIProcessor()

# MongoDB-compatible reminder system will be initialized after MongoDB connection

# -------------------------
# Routes
# -------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        print(f"Login attempt for username: {username}")
        user = User.objects(username=username).first()
        
        if user and user.check_password(password):
            print(f"Password verified for user: {username}")
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            user.save()
            return jsonify({'success': True, 'message': 'Login successful', 'user': user.to_dict()})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'Login failed'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if User.objects(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
        if User.objects(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 409
        
        user = User(
            username=username,
            email=email,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_active=True
        )
        user.set_password(password)
        user.save()
        print(f"New user registered: {username}")
        return jsonify({'success': True, 'message': 'Registration successful', 'user_id': str(user.id)}), 201
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        username = current_user.username
        logout_user()
        return jsonify({'success': True, 'message': f'User {username} logged out'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Logout failed: {str(e)}'}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/medications', methods=['GET', 'POST'])
@login_required
def medications():
    if request.method == 'POST':
        try:
            data = request.json
            if not data.get('name'):
                return jsonify({'error': 'Medication name is required'}), 400
            
            existing = Medication.objects(user_id=current_user.id, name=data['name'], is_active=True).first()
            if existing:
                return jsonify({'error': 'Medication already exists'}), 409
            
            medication = Medication(
                user_id=current_user.id,
                user_username=current_user.username,
                name=data['name'],
                dosage=data.get('dosage', ''),
                frequency=data.get('frequency', ''),
                instructions=data.get('instructions', ''),
                duration=data.get('duration', ''),
                source='manual'
            )
            medication.save()
            return jsonify({'success': True, 'message': 'Medication added', 'medication': medication.to_dict()}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            medications = Medication.objects(user_id=current_user.id, is_active=True).order_by('-created_at')
            return jsonify([med.to_dict() for med in medications])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/upload-prescription', methods=['POST'])
@login_required
def upload_prescription():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        upload_record = PrescriptionUpload(
            user_id=current_user.id,
            filename=filename,
            original_filename=file.filename,
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            mime_type=file.content_type,
            processing_status='processing'
        )
        upload_record.save()
        
        start_time = time.time()
        extracted_text = ocr_processor.extract_text_from_image(filepath)
        processing_time = time.time() - start_time
        medications = ai_processor.extract_medications(extracted_text)
        
        medications_added = 0
        for med_data in medications:
            if not Medication.objects(user_id=current_user.id, name=med_data['name'], is_active=True).first():
                med = Medication(
                    user_id=current_user.id,
                    user_username=current_user.username,
                    name=med_data['name'],
                    dosage=med_data.get('dosage', ''),
                    frequency=med_data.get('frequency', ''),
                    instructions=med_data.get('instructions', ''),
                    source='ocr',
                    confidence_score=med_data.get('confidence', 0.8)
                )
                med.save()
                medications_added += 1
        
        upload_record.extracted_text = extracted_text
        upload_record.processing_time = processing_time
        upload_record.medications_found = len(medications)
        upload_record.medications_added = medications_added
        upload_record.processing_status = 'completed'
        upload_record.processed_at = datetime.utcnow()
        upload_record.save()
        
        return jsonify({'success': True, 'message': 'Prescription processed', 'medications': medications, 'added': medications_added})
    except Exception as e:
        if 'upload_record' in locals():
            upload_record.processing_status = 'failed'
            upload_record.error_message = str(e)
            upload_record.save()
        return jsonify({'success': False, 'message': 'Processing failed', 'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat(), 'database': 'mongodb'})

@app.route('/database-status')
def database_status():
    try:
        stats = get_database_stats()
        if stats:
            return jsonify({'status': 'connected', 'database': 'mongodb', 'stats': stats, 'timestamp': datetime.utcnow().isoformat()})
        return jsonify({'status': 'error', 'message': 'Failed to get stats'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# -------------------------
# WebSocket Events
# -------------------------
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        print(f"🔌 User {current_user.username} connected")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')
        print(f"🔌 User {current_user.username} disconnected")

# -------------------------
# MongoDB Reminder System
# -------------------------
class MongoMedicationReminder:
    def __init__(self, socketio=None, app=None):
        self.reminder_thread = None
        self.is_running = False
        self.socketio = socketio
        self.app = app

    def start_reminder_service(self):
        if not self.is_running:
            self.is_running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()
            print("🔔 Reminder service started")

    def stop_reminder_service(self):
        self.is_running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=5)

    def _reminder_loop(self):
        while self.is_running:
            try:
                with self.app.app_context():
                    self._check_and_send_reminders()
                time.sleep(60)
            except Exception as e:
                print(f"❌ Reminder loop error: {e}")
                time.sleep(60)

    def _check_and_send_reminders(self):
        now = datetime.now().strftime('%H:%M')
        reminders = Reminder.objects(is_active=True)
        for reminder in reminders:
            if now == reminder.time:
                self._send_reminder_alert(reminder)

    def _send_reminder_alert(self, reminder):
        medication = Medication.objects(id=reminder.medication_id).first()
        if not medication:
            return
        reminder.last_sent = datetime.now()
        reminder.save()
        alert = {'type': 'reminder', 'medication': medication.name, 'time': reminder.time, 'timestamp': datetime.now().isoformat()}
        if self.socketio:
            self.socketio.emit('medication_reminder', alert, room=f'user_{reminder.user_id}')
        print(f"🔔 Sent reminder for {medication.name}")

# -------------------------
# Initialization
# -------------------------
reminder_system = None

def initialize_mongodb_app():
    """Initialize MongoDB connection and setup"""
    global reminder_system
    try:
        print("🔄 Initializing MongoDB application...")

        # FIX: Connect before testing
        if not init_mongodb(app):
            print("❌ MongoDB initialization failed")
            return False
        if not test_mongodb_connection():
            print("❌ MongoDB connection test failed")
            return False

        if not create_default_users():
            print("⚠️ Default users not created")

        reminder_system = MongoMedicationReminder(socketio=socketio, app=app)
        stats = get_database_stats()
        if stats:
            print(f"📊 DB Status: {stats}")
        print("✅ MongoDB initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

if __name__ == '__main__':
    if not initialize_mongodb_app():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    if reminder_system:
        reminder_system.start_reminder_service()
    print("🏥 MEDIMORPH running on MongoDB")
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
