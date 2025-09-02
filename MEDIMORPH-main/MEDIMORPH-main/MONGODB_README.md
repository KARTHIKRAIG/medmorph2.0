# MEDIMORPH - MongoDB Version

A comprehensive healthcare management system built with Flask and MongoDB for efficient data storage and retrieval.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB Community Server
- Windows 10/11 (for .bat files)

### 1. Install MongoDB
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install with default settings
3. Start MongoDB service or run: `mongod --dbpath C:\data\db`

### 2. Setup Project
```bash
# Navigate to project directory
cd MEDIMORPH-main

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
# Setup MongoDB collections and sample data
python setup_mongodb.py
```

### 4. Start Application
```bash
# Option 1: Use batch file (Windows)
start_mongodb.bat

# Option 2: Direct Python execution
python app.py
```

### 5. Access Application
Open your browser and go to: `http://localhost:5000`

## 🗄️ Database Structure

### Collections
- **users**: User accounts and authentication
- **medications**: Medication management
- **prescriptions**: Prescription uploads and OCR
- **health_records**: Health metrics tracking
- **reminders**: Medication reminders

### Sample Data
The setup script creates:
- Test users: `testuser` / `test@example.com`
- Sample medications
- Sample health records
- Sample reminders

## 🔧 Configuration

### MongoDB Connection
- **URI**: `mongodb://localhost:27017/`
- **Database**: `medimorph`
- **Collections**: Automatically created with proper indexes

### Environment Variables
- `MONGO_URI`: MongoDB connection string
- `SECRET_KEY`: Flask secret key (change in production)

## 📱 Features

### User Management
- User registration and login
- Secure password hashing
- Session management with Flask-Login

### Medication Management
- Add/edit medications
- Dosage and frequency tracking
- Start/end date management

### Prescription OCR
- Image upload support (PNG, JPG, JPEG, GIF, PDF)
- Text extraction using Tesseract OCR
- Prescription data storage

### Health Records
- Track various health metrics
- Date-based record keeping
- Notes and observations

### Reminders
- Medication reminder system
- Background scheduler
- Time-based notifications

## 🛠️ Development

### Project Structure
```
MEDIMORPH-main/
├── app.py                 # Main Flask application
├── mongodb_config.py      # MongoDB configuration
├── setup_mongodb.py       # Database initialization
├── start_mongodb.bat      # Windows startup script
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
├── uploads/              # File upload directory
└── models/               # ML model scripts
```

### Key Dependencies
- **Flask**: Web framework
- **Flask-Login**: User authentication
- **Flask-PyMongo**: MongoDB integration
- **PyMongo**: MongoDB driver
- **OpenCV**: Image processing
- **Tesseract**: OCR functionality
- **Schedule**: Reminder scheduling

## 🔍 Troubleshooting

### MongoDB Connection Issues
1. Ensure MongoDB service is running
2. Check if port 27017 is available
3. Verify MongoDB installation

### OCR Issues
1. Install Tesseract OCR
2. Add Tesseract to system PATH
3. Verify image file formats

### Virtual Environment Issues
1. Delete `.venv` folder
2. Recreate with: `python -m venv .venv`
3. Reinstall dependencies

## 📊 Testing

### Run Tests
```bash
# Test MongoDB connection
python -c "from mongodb_config import get_mongodb_client; print('Connection:', 'OK' if get_mongodb_client() else 'FAILED')"

# Test application startup
python -c "from app import app; print('App loaded successfully')"
```

### Sample Data Verification
```bash
# Check database contents
python -c "
from mongodb_config import get_database
db = get_database()
print(f'Users: {db.users.count_documents({})}')
print(f'Medications: {db.medications.count_documents({})}')
"
```

## 🚀 Production Deployment

### Security Considerations
1. Change `SECRET_KEY` in `app.py`
2. Use environment variables for sensitive data
3. Enable MongoDB authentication
4. Use HTTPS in production

### Performance Optimization
1. MongoDB connection pooling
2. Index optimization
3. Query optimization
4. Caching strategies

## 📚 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard
- `POST /add_medication` - Add medication
- `POST /upload_prescription` - Upload prescription
- `POST /add_health_record` - Add health record
- `POST /set_reminder` - Set reminder

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review MongoDB logs
3. Check application logs
4. Create an issue in the repository

---

**Note**: This is the MongoDB version of MEDIMORPH. All data is stored in MongoDB collections instead of SQLite database.

