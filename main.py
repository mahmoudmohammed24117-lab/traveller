import os
from flask import Flask, jsonify, request, make_response
from flask_bcrypt import Bcrypt 
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv

# 1. تحميل الإعدادات
load_dotenv()

app = Flask(__name__)

# 2. إعدادات الـ Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '789456123_default_secret'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

# 3. تشغيل المكتبات وتعديل الـ CORS الشامل
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# حل مشكلة الـ CORS من السيرفر مباشرة
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# تعريف الـ app لـ Vercel
app = app 

# --- المسارات (Routes) ---

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Smart Traveler API is Running!"})

# 1. تسجيل مستخدم جديد
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

# 2. تسجيل الدخول (حل مشكلة الـ undefined ببعث الـ username)
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    data = request.json
    try:
        user_data = mongo.db.users.find_one({"email": data['email']})
        if user_data and bcrypt.check_password_hash(user_data['password'], data['password']):
            return jsonify({
                "status": "success", 
                "message": "Logged in!",
                "username": user_data['username'],
                "email": user_data['email'],
                "user_id": str(user_data['_id'])
            }), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. حفظ الفيدباك (Feedback)
@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    data = request.json
    try:
        mongo.db.feedbacks.insert_one({
            "name": data.get('name'),
            "email": data.get('email'),
            "message": data.get('message'),
            "rating": data.get('rating')
        })
        return jsonify({"status": "success", "message": "Feedback submitted successfully!!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "فشل في حفظ البيانات"}), 500

# 4. تحديث بيانات البروفايل (Update Profile)
@app.route('/api/update-profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    data = request.json
    user_id = data.get('user_id')
    try:
        # قوله "أه حققتهالك" وظبط الداتا بيس
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "username": data.get('username'),
                "email": data.get('email')
            }}
        )
        return jsonify({"status": "success", "message": "Profile updated successfully!!! ✅"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
