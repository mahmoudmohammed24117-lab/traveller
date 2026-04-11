import os
from flask import Flask, jsonify, request, make_response
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '789456123_default_secret'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

# 3. إعدادات الرفع
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 4. تشغيل المكتبات وتعديل الـ CORS الشامل
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# الدالة دي هي "القفل والمفتاح" لحل مشكلة CORS نهائياً
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# تعريف الـ app لـ Vercel
app = app 

# --- Helper Functions ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

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
    return jsonify({"status": "success", "message": "API is Running!"})

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    data = request.json
    try:
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
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
        return make_response('', 204)
    data = request.json
    try:
        user_data = mongo.db.users.find_one({"email": data['email']})
        if user_data and bcrypt.check_password_hash(user_data['password'], data['password']):
            return jsonify({"status": "success", "message": "Logged in!"}), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
