import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    USE_DB = os.getenv('USE_DB', 'false').strip().lower() in ('true', '1', 'yes')
    
    # Direct database URL (used by cloud hosts: Render, Railway, Neon, Supabase)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # PostgreSQL configuration (local development)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'library_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'smartlib-super-secret-key-college-dbms')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
