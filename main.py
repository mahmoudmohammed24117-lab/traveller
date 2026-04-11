import os
from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt 
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# 1. تحميل الإعدادات
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

# 2. إعدادات الـ Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.getenv('SECRET_KEY', '789456123_default_secret')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI') or os.getenv('MONGO_URI')

# 3. إعدادات الرفع
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 4. تشغيل المكتبات وتعديل الـ CORS (حل مشكلة الـ Blocked by CORS نهائياً)
CORS(app, resources={r"/*": {"origins": "*"}})

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# تعريف الـ app لـ Vercel
app = app 

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.profile_pic = user_data.get('profile_pic', 'default.jpg')

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    except:
        return None

# --- المسارات (Routes) ---

@app.route('/')
def home():
    try:
        mongo.db.command('ping')
        db_status = "Connected"
    except:
        db_status = "Not Connected"
    return jsonify({
        "status": "success", 
        "message": "Smart Traveler AI API is Running!",
        "database": db_status
    })

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    data = request.json
    try:
        if not data or not data.get('password') or not data.get('username') or not data.get('email'):
            return jsonify({"status": "error", "message": "Missing data"}), 400
            
        existing_user = mongo.db.users.find_one({
            "$or": [{"email": data['email']}, {"username": data['username']}]
        })
        
        if existing_user:
            return jsonify({"status": "error", "message": "Username or Email already exists!"}), 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        mongo.db.users.insert_one({
            "username": data['username'],
            "email": data['email'],
            "password": hashed_password,
            "profile_pic": "default.jpg"
        })
        return jsonify({"status": "success", "message": "Account created!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    data = request.json
    try:
        user_data = mongo.db.users.find_one({"email": data['email']})
        if user_data and bcrypt.check_password_hash(user_data['password'], data['password']):
            user_obj = User(user_data)
            login_user(user_obj)
            return jsonify({
                "status": "success", 
                "message": "Logged in!",
                "user_id": user_obj.id,
                "username": user_obj.username
            }), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    data = request.json
    try:
        mongo.db.feedbacks.insert_one(data)
        return jsonify({"status": "success", "message": "Feedback saved!"}), 201
    except:
        return jsonify({"status": "error", "message": "Error saving feedback"}), 500

if __name__ == '__main__':
    app.run(debug=True)
