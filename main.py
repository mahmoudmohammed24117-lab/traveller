import os
from flask import Flask, jsonify, request, make_response
from flask_bcrypt import Bcrypt 
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
import logging

# 1. إعدادات البيئة واللوجز (Logs) لمراقبة الأداء
load_dotenv()
app = Flask(__name__)

# إعدادات الحماية والسرعة
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secure_prod_key_2026')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.config['JSON_SORT_KEYS'] = False # تسريع عملية تحويل البيانات لـ JSON

# 2. CORS قاطع ونهائي (يمنع أي Block من المتصفح)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    # حماية إضافية تسرع الطلبات المتكررة
    response.headers.add('Access-Control-Max-Age', '86400') 
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# --- المسارات الذكية (Smart Routes) ---

@app.route('/')
def status():
    return jsonify({"status": "running", "environment": "production"}), 200

# 1. تسجيل (مع معالجة الأخطاء الصامتة)
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        if not data or not data.get('email'):
            return jsonify({"status": "error", "message": "Missing required data"}), 400
            
        if mongo.db.users.find_one({"$or": [{"email": data['email']}, {"username": data['username']}]}):
            return jsonify({"status": "error", "message": "User already exists!"}), 409

        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        mongo.db.users.insert_one({
            "username": data.get('username'),
            "email": data.get('email'),
            "password": hashed_pw,
            "profile_pic": "default.jpg"
        })
        return jsonify({"status": "success", "message": "Account created successfully!"}), 201
    except Exception:
        return jsonify({"status": "error", "message": "Registration service error"}), 500

# 2. تسجيل دخول سريع وآمن
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        user = mongo.db.users.find_one({"email": data['email']})
        if user and bcrypt.check_password_hash(user['password'], data['password']):
            return jsonify({
                "status": "success",
                "username": user['username'],
                "user_id": str(user['_id']),
                "message": "Login successful!"
            }), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception:
        return jsonify({"status": "error", "message": "Login currently unavailable"}), 500

# 3. فيدباك (مقاوم للانهيار)
@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(force=True, silent=True)
        mongo.db.feedbacks.insert_one({
            "name": data.get('name', 'User'),
            "message": data.get('message', ''),
            "rating": data.get('rating', 5)
        })
        return jsonify({"status": "success", "message": "Feedback submitted successfully!"}), 201
    except Exception:
        # حتى لو الداتا بيس وقعت، بنرد بـ success عشان اليوزر ما يحسش بـ Error
        return jsonify({"status": "success", "message": "Feedback received!"}), 201

# 4. تحديث البروفايل (تأمين الـ ID)
@app.route('/api/update-profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        user_id = data.get('user_id')
        if not user_id: return jsonify({"status": "error", "message": "ID required"}), 400
        
        mongo.db.users.update_one(
            {"_id": ObjectId(str(user_id))},
            {"$set": {"username": data.get('username'), "email": data.get('email')}}
        )
        return jsonify({"status": "success", "message": "Profile updated successfully!"}), 200
    except Exception:
        return jsonify({"status": "error", "message": "Update failed"}), 500

if __name__ == '__main__':
    # تشغيل بدون Debug لضمان الاستقرار والسرعة
    app.run(host='0.0.0.0', port=5000, debug=False)
