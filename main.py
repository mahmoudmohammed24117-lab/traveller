import os
from flask import Flask, jsonify, request, make_response
from flask_bcrypt import Bcrypt 
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import json
import requests
from dotenv import load_dotenv

# 1. إعدادات البيئة
load_dotenv()
app = Flask(__name__)

# إعدادات الحماية والسرعة المتوافقة مع Vercel و MongoDB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secure_prod_key_2026')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.config['JSON_SORT_KEYS'] = False 

# 2. إعدادات CORS الشاملة لمنع أي تعارض مع MonsterASP أو الـ Live Server
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '86400') 
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# إعدادات الذكاء الاصطناعي (Groq AI) لصفحة الشات الذكي
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_xxxx")

# --- 🏛️ المسارات الأساسية (المستخدمين والبروفايل) ---

@app.route('/')
def status():
    return jsonify({"status": "running", "environment": "production", "features": "whatsapp_suite_enabled"}), 200

# 1. تسجيل حساب جديد في MongoDB
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        if not data or not data.get('email') or not data.get('username') or not data.get('password'):
            return jsonify({"status": "error", "message": "Missing required data"}), 400
            
        if mongo.db.users.find_one({"$or": [{"email": data['email']}, {"username": data['username']}]}):
            return jsonify({"status": "error", "message": "User already exists!"}), 409

        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        mongo.db.users.insert_one({
            "username": data.get('username'),
            "email": data.get('email'),
            "password": hashed_pw,
            "profile_pic": "static/uploads/default.jpg"
        })
        return jsonify({"status": "success", "message": "Account created successfully!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "Registration service error"}), 500

# 2. تسجيل دخول سريع وآمن
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        user = mongo.db.users.find_one({"$or": [{"email": data.get('email')}, {"username": data.get('username')}]})
        if user and bcrypt.check_password_hash(user['password'], data['password']):
            return jsonify({
                "status": "success",
                "username": user['username'],
                "user_id": str(user['_id']),
                "profile_pic": user.get('profile_pic', 'static/uploads/default.jpg'),
                "message": "Login successful!"
            }), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception:
        return jsonify({"status": "error", "message": "Login currently unavailable"}), 500

# 3. تحديث بيانات الملف الشخصي والصورة
@app.route('/api/update-profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        user_id = data.get('user_id')
        if not user_id: return jsonify({"status": "error", "message": "ID required"}), 400
        
        update_fields = {}
        if data.get('username'): update_fields['username'] = data['username']
        if data.get('email'): update_fields['email'] = data['email']
        if data.get('profile_pic'): update_fields['profile_pic'] = data['profile_pic']
        
        mongo.db.users.update_one({"_id": ObjectId(str(user_id))}, {"$set": update_fields})
        return jsonify({"status": "success", "message": "Profile updated successfully!"}), 200
    except Exception:
        return jsonify({"status": "error", "message": "Update failed"}), 500


# --- 💬 مسارات مجتمع الشات والواتساب سويت الجلوبال (MongoDB) ---

# 4. جلب تاريخ الرسائل للروم الحالية (بديل load_history القديم)
@app.route('/api/community/history', methods=['GET'])
def get_room_history():
    try:
        room = request.args.get('room', 'global_group')
        messages = mongo.db.community_messages.find({"room": room}).sort("timestamp", 1).limit(50)
        
        messages_list = []
        for msg in messages:
            messages_list.append({
                "msg_id": str(msg['_id']),
                "room": msg.get('room', 'global_group'),
                "username": msg.get('username'),
                "profile_pic": msg.get('profile_pic', 'static/uploads/default.jpg'),
                "message": msg.get('message', ''),
                "file_url": msg.get('file_url', ''),
                "file_type": msg.get('file_type', ''),
                "reactions": msg.get('reactions', {}),
                "timestamp": msg.get('timestamp', datetime.utcnow().strftime('%H:%M'))
            })
        return jsonify(messages_list), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 5. إرسال رسالة جديدة للكومينتي (بديل send_msg القديم)
@app.route('/api/community/send', methods=['POST', 'OPTIONS'])
def send_community_msg():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        room = data.get('room', 'global_group')
        username = data.get('username')
        
        user_info = mongo.db.users.find_one({"username": username})
        p_pic = user_info['profile_pic'] if user_info and 'profile_pic' in user_info else 'static/uploads/default.jpg'
        
        new_msg = {
            "room": room,
            "username": username,
            "profile_pic": p_pic,
            "message": data.get('message', ''),
            "file_url": data.get('file_url', ''),
            "file_type": data.get('file_type', ''),
            "reactions": {},
            "timestamp": datetime.utcnow().strftime('%H:%M')
        }
        result = mongo.db.community_messages.insert_one(new_msg)
        new_msg['msg_id'] = str(result.inserted_id)
        del new_msg['_id']
        
        return jsonify({"status": "success", "data": new_msg}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 6. إضافة تفاعل إيموجي على رسالة معينة
@app.route('/api/community/react', methods=['POST', 'OPTIONS'])
def add_msg_reaction():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        msg_id = data.get('msg_id')
        username = data.get('username')
        emoji = data.get('emoji')
        
        mongo.db.community_messages.update_one(
            {"_id": ObjectId(str(msg_id))},
            {"$set": {f"reactions.{username}": emoji}}
        )
        return jsonify({"status": "success", "msg_id": msg_id, "username": username, "emoji": emoji}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 7. إنشاء غرفة فرعية مخصصة للعائلات
@app.route('/api/community/create-room', methods=['POST', 'OPTIONS'])
def create_custom_room():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        room_name = data.get('room_name')
        creator = data.get('creator')
        
        if not room_name or not creator:
            return jsonify({"status": "error", "message": "Missing room info"}), 400
            
        room_id = f"room_{int(datetime.utcnow().timestamp())}"
        mongo.db.custom_rooms.insert_one({
            "room_id": room_id,
            "room_name": room_name,
            "creator": creator,
            "created_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        })
        return jsonify({"status": "success", "room_id": room_id, "room_name": room_name}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 8. جلب قائمة كل الأعضاء المسجلين بالسيستم
@app.route('/api/community/users', methods=['GET'])
def get_community_users():
    try:
        users = mongo.db.users.find({}, {"username": 1, "profile_pic": 1, "_id": 0})
        return jsonify(list(users)), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 🤖 مسارات الذكاء الاصطناعي والفيدباك ---

# 9. شات ومخطط السفر بالذكاء الاصطناعي
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(silent=True)
        user_msg = data.get("message")
        user_id = data.get("user_id")

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional travel planner. Output a valid JSON object strictly."},
                {"role": "user", "content": user_msg}
            ],
            "response_format": { "type": "json_object" },
            "temperature": 0.3
        }
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=20)
        ai_reply = response.json()['choices'][0]['message']['content']

        if user_id:
            mongo.db.chat_history.insert_one({
                "user_id": user_id,
                "query": user_msg,
                "response": ai_reply,
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({"reply": ai_reply})
    except Exception:
        return jsonify({"status": "error", "message": "AI failed"}), 500

# 10. حفظ التقييمات
@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(force=True, silent=True)
        mongo.db.feedbacks.insert_one({
            "name": data.get('name', 'User'),
            "message": data.get('message', ''),
            "rating": data.get('rating', 5),
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        })
        return jsonify({"status": "success", "message": "Feedback submitted successfully!"}), 201
    except Exception:
        return jsonify({"status": "success", "message": "Feedback received!"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
