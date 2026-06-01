# Copy this file to config.py and update with your settings

class Config:
    SECRET_KEY = 'change-this-to-a-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///scrapyard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Serial port settings for your scale
    SCALE_PORT = 'COM3'      # Windows: COM3, Linux: '/dev/ttyUSB0'
    SCALE_BAUDRATE = 9600
    SCALE_TIMEOUT = 1
    
    # Optional: Enable debug mode (False for production)
    DEBUG = True
