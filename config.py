import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'scrapyard-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///scrapyard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Serial port settings for scale
    SCALE_PORT = os.environ.get('SCALE_PORT', 'COM3')
    SCALE_BAUDRATE = int(os.environ.get('SCALE_BAUDRATE', 9600))
    SCALE_TIMEOUT = int(os.environ.get('SCALE_TIMEOUT', 1))
    
    # Debug mode
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
