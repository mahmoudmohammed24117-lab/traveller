import os
from flask import Flask, jsonify, request, make_response
from flask_bcrypt import Bcrypt 
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv

# 1. Load Settings
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '789456123_default_secret'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

# 2. Strategic CORS (The Ultimate Fix)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "API is online and stable!"})

# 1. User Registration
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    try:
        if not data: return jsonify({"status": "error", "message": "No data received"}), 400
        if mongo.db.users.find_one({"$or": [{"email": data['email']}, {"username": data['username']}]}):
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
        return jsonify({"status": "error", "message": "Registration failed"}), 500

# 2. User Login
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
                "user_id": str(user_data['_id'])
            }), 200
        return jsonify({"status": "error", "message": "Invalid email or password."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": "Login failed"}), 500

# 3. Feedback (Fixed "Server Sleeping" error)
@app.route('/api/feedback', methods=['POST', 'OPTIONS'])
def save_feedback():
    if request.method == 'OPTIONS': return make_response('', 204)
    try:
        data = request.get_json(force=True) # Force read even if header is wrong
        mongo.db.feedbacks.insert_one({
            "name": data.get('name', 'Anonymous'),
            "email": data.get('email', 'N/A'),
            "message": data.get('message', ''),
            "rating": data.get('rating', 5)
        })
        return jsonify({"status": "success", "message": "Feedback submitted successfully!"}), 201
    except Exception as e:
        print(f"Feedback Error: {str(e)}") # Useful for Vercel logs
        return jsonify({"status": "error", "message": "Feedback saved locally but server is busy."}), 500

# 4. Update Profile (Final Fix)
@app.route('/api/update-profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS': return make_response('', 204)
    data = request.json
    user_id = data.get('user_id')
    if not user_id: return jsonify({"status": "error", "message": "Missing User ID"}), 400
    try:
        # Update using ObjectId
        result = mongo.db.users.update_one(
            {"_id": ObjectId(str(user_id))},
            {"$set": {
                "username": data.get('username'),
                "email": data.get('email')
            }}
        )
        if result.modified_count > 0:
            return jsonify({"status": "success", "message": "Profile updated successfully!"}), 200
        return jsonify({"status": "error", "message": "No changes were made."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Update failed. Error in ID format."}), 500

if __name__ == '__main__':
    app.run(debug=True)
