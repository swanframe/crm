import os
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

class Config:
    """
    Kelas konfigurasi dasar untuk aplikasi Flask.
    Mengambil pengaturan dari variabel lingkungan.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_default'
    # Konfigurasi database PostgreSQL
    # Format: postgresql://user:password@host:port/database_name
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:04040404@localhost:5432/crm_db'
    # Anda bisa menambahkan konfigurasi lain di sini, seperti DEBUG, TESTING, dll.
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'