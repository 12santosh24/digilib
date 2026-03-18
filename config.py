"""
config.py - Configuration for DigiLib
Uses environment variables for production (Render/Railway)
Falls back to defaults for local development
"""
import os
from datetime import timedelta

class Config:
    # ── Security ──
    SECRET_KEY = os.environ.get('SECRET_KEY', 'digilib-dev-secret-change-in-production')
    
    # ── Database ──
    # In production: set DATABASE_URL env var to PostgreSQL URL
    # In development: uses local SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL.startswith('postgres://'):
        # Render gives postgres://, SQLAlchemy needs postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # ── Session ──
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ── Library Settings ──
    TOTAL_SEATS = 92
    OPENING_TIME = "6:00 AM"
    CLOSING_TIME = "9:00 PM"

    # ── Fee Structure ──
    FEE_STRUCTURE = {1: 300, 2: 500, 3: 700}

    # ── Admin Credentials ──
    # CHANGE THESE via environment variables in production!
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # ── WhatsApp / SMS via Twilio ──
    # Get free credentials at: https://www.twilio.com
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN  = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE       = os.environ.get('TWILIO_PHONE', '')       # Your Twilio number e.g. +1234567890
    TWILIO_WHATSAPP    = os.environ.get('TWILIO_WHATSAPP', '')    # e.g. whatsapp:+14155238886

    # ── Fast2SMS (India SMS - cheaper alternative) ──
    FAST2SMS_API_KEY   = os.environ.get('FAST2SMS_API_KEY', '')   # From fast2sms.com

    # ── App URL (used in reminder messages) ──
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')

    # ── Reminder Settings ──
    REMINDER_DAYS_BEFORE = 3   # Send reminder N days before due date
