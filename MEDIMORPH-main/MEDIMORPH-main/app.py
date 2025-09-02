import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import pytesseract
import schedule
import time
import threading
from bson import ObjectId

# Import MongoDB configuration
from mongodb_config import configure_mongodb, get_database, get_mongodb_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure MongoDB
mongo = configure_mongodb(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    return None

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or email already exists!')
            return render_template('register.html')
        
        # Create new user
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        try:
            result = mongo.db.users.insert_one(user_data)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            flash('Registration failed! Please try again.')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find user by username or email
        user_data = mongo.db.users.find_one({'$or': [{'username': username}, {'email': username}]})
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            session['user_id'] = str(user_data['_id'])
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password!')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user_id = ObjectId(current_user.id)
        
        # Get user's medications
        medications = list(mongo.db.medications.find({'user_id': user_id}))
        
        # Get user's prescriptions
        prescriptions = list(mongo.db.prescriptions.find({'user_id': user_id}).sort('upload_date', -1))
        
        # Get user's health records
        health_records = list(mongo.db.health_records.find({'user_id': user_id}).sort('record_date', -1))
        
        # Get upcoming reminders
        now = datetime.utcnow()
        reminders = list(mongo.db.reminders.find({
            'user_id': user_id,
            'reminder_time': {'$gte': now}
        }).sort('reminder_time', 1).limit(5))
        
        return render_template('dashboard.html', 
                             medications=medications,
                             prescriptions=prescriptions,
                             health_records=health_records,
                             reminders=reminders)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error loading dashboard data.')
        return render_template('dashboard.html', 
                             medications=[], 
                             prescriptions=[], 
                             health_records=[], 
                             reminders=[])

@app.route('/add_medication', methods=['POST'])
@login_required
def add_medication():
    try:
        user_id = ObjectId(current_user.id)
        
        medication_data = {
            'user_id': user_id,
            'medication_name': request.form['medication_name'],
            'dosage': request.form['dosage'],
            'frequency': request.form['frequency'],
            'start_date': datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
            'end_date': datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form['end_date'] else None,
            'notes': request.form.get('notes', ''),
            'created_at': datetime.utcnow()
        }
        
        mongo.db.medications.insert_one(medication_data)
        flash('Medication added successfully!')
        
    except Exception as e:
        logger.error(f"Error adding medication: {e}")
        flash('Error adding medication!')
    
    return redirect(url_for('dashboard'))

@app.route('/upload_prescription', methods=['POST'])
@login_required
def upload_prescription():
    try:
        if 'prescription_file' not in request.files:
            flash('No file selected!')
            return redirect(url_for('dashboard'))
        
        file = request.files['prescription_file']
        if file.filename == '':
            flash('No file selected!')
            return redirect(url_for('dashboard'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text using OCR
            extracted_text = extract_text_from_image(filepath)
            
            user_id = ObjectId(current_user.id)
            prescription_data = {
                'user_id': user_id,
                'filename': filename,
                'filepath': filepath,
                'extracted_text': extracted_text,
                'upload_date': datetime.utcnow(),
                'notes': request.form.get('notes', '')
            }
            
            mongo.db.prescriptions.insert_one(prescription_data)
            flash('Prescription uploaded successfully!')
            
        else:
            flash('Invalid file type!')
            
    except Exception as e:
        logger.error(f"Error uploading prescription: {e}")
        flash('Error uploading prescription!')
    
    return redirect(url_for('dashboard'))

@app.route('/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    try:
        user_id = ObjectId(current_user.id)
        
        health_record_data = {
            'user_id': user_id,
            'record_type': request.form['record_type'],
            'value': request.form['value'],
            'unit': request.form['unit'],
            'record_date': datetime.strptime(request.form['record_date'], '%Y-%m-%d'),
            'notes': request.form.get('notes', ''),
            'created_at': datetime.utcnow()
        }
        
        mongo.db.health_records.insert_one(health_record_data)
        flash('Health record added successfully!')
        
    except Exception as e:
        logger.error(f"Error adding health record: {e}")
        flash('Error adding health record!')
    
    return redirect(url_for('dashboard'))

@app.route('/set_reminder', methods=['POST'])
@login_required
def set_reminder():
    try:
        user_id = ObjectId(current_user.id)
        
        reminder_data = {
            'user_id': user_id,
            'medication_name': request.form['medication_name'],
            'reminder_time': datetime.strptime(request.form['reminder_time'], '%Y-%m-%dT%H:%M'),
            'message': request.form.get('message', ''),
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        mongo.db.reminders.insert_one(reminder_data)
        flash('Reminder set successfully!')
        
    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        flash('Error setting reminder!')
    
    return redirect(url_for('dashboard'))

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return "Error: Could not read image"
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gray = cv2.dilate(gray, kernel, iterations=1)
        
        # Extract text
        text = pytesseract.image_to_string(gray)
        
        return text.strip() if text else "No text extracted"
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return f"Error extracting text: {str(e)}"

def check_reminders():
    """Check and process active reminders"""
    try:
        now = datetime.utcnow()
        active_reminders = mongo.db.reminders.find({
            'is_active': True,
            'reminder_time': {'$lte': now}
        })
        
        for reminder in active_reminders:
            # Here you would implement actual reminder notification
            # For now, just log it
            logger.info(f"Reminder for {reminder['medication_name']}: {reminder['message']}")
            
            # Mark reminder as processed
            mongo.db.reminders.update_one(
                {'_id': reminder['_id']},
                {'$set': {'is_active': False, 'processed_at': now}}
            )
            
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")

def run_reminder_scheduler():
    """Run reminder scheduler in background"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Schedule reminder checks
schedule.every(1).minutes.do(check_reminders)

# Start reminder scheduler in background thread
reminder_thread = threading.Thread(target=run_reminder_scheduler, daemon=True)
reminder_thread.start()

if __name__ == '__main__':
    try:
        # Test MongoDB connection
        client = get_mongodb_client()
        if client:
            print("✅ MongoDB connection successful")
            client.close()
        else:
            print("❌ MongoDB connection failed")
            exit(1)
        
        print("🏥 Starting MEDIMORPH application...")
        print("🌐 Access the application at: http://localhost:5000")
        print("🔔 Active medication reminders enabled!")
        print("💾 MongoDB ready for data storage!")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        print(f"❌ Failed to start application: {e}")

