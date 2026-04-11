import os
from dotenv import load_dotenv

# تحديد مسار الفولدر اللي فيه ملف config.py
basedir = os.path.abspath(os.path.dirname(__file__))

# تحميل ملف الـ .env اللي موجود جنبه في نفس فولدر backend
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # سحب البيانات من الـ .env
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_123')
    MONGO_URI = os.getenv('MONGO_URI')
    
    # إعدادات إضافية لو حبيت (زي رفع الصور)
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')