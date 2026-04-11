import os
from flask import Flask, jsonify, request, make_response
from flask_bcrypt import Bcrypt 
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

app = Flask(__name__)

# 2. Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '789456123_default_secret'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

# 3. Comprehensive CORS setup
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Vercel app reference
app = app 

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Smart Traveler API is perfectly running!"})

# 1. Registration
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    try:
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"status": "error", "message": "Please provide all required fields."}), 400
            
        existing_user = mongo.db.users.find_one({
            "$or": [{"email": data['email']}, {"username": data['username']}]
        })
        if existing_user:
            return jsonify({"status": "error", "message": "Username or Email already exists!"}), 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        mongo.db.users.insert_one({
            "username": data.get('username'),
            "email": data.get('email'),
            "password": hashed_password,
            "profile_pic": "default.jpg"
        })
        return jsonify({"status": "success", "message": "Account created successfully!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "Registration failed. Please try again."}), 500

# 2. Login
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    try:
        user_data = mongo.db.users.find_one({"email": data['email']})
        if user_data and bcrypt.check_password_hash(user_data['password'], data['password']):
            return jsonify({
                "status": "success", 
                "message": "Login successful!",
                "username": user_data['username'],
                "email": user_data['email'],
                "user_id": str(user_data['_id'])
            }), 200
        return jsonify({"status": "error", "message": "Invalid email or password."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": "An error occurred during login."}), 500

# 3. Feedback (Fixed)
@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    try:
        if not data:
            return jsonify({"status": "error", "message": "Feedback data is empty."}), 400
            
        mongo.db.feedbacks.insert_one({
            "name": data.get('name', 'Anonymous'),
            "email": data.get('email', 'N/A'),
            "message": data.get('message', ''),
            "rating": data.get('rating', 5)
        })
        return jsonify({"status": "success", "message": "Feedback submitted successfully! Thank you."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "Server is busy. Could not save feedback."}), 500

# 4. Update Profile (Fixed ObjectId issue)
@app.route('/api/update-profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing."}), 400
        
    try:
        # We use str(user_id) to ensure it's a valid string before converting to ObjectId
        mongo.db.users.update_one(
            {"_id": ObjectId(str(user_id))},
            {"$set": {
                "username": data.get('username'),
                "email": data.get('email')
            }}
        )
        return jsonify({"status": "success", "message": "Profile updated successfully! ✅"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to update profile. Please check user ID."}), 500

if __name__ == '__main__':
    app.run(debug=True)
