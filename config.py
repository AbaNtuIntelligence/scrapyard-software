import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'scrapyard-secret-key-2026')
    
    # Database Configuration
    if os.environ.get('RENDER'):
        # Production on Render
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url and 'tidbcloud.com' in database_url:
            # Get the CA certificate path
            cert_paths = [
                '/etc/ssl/certs/tidb-ca.pem',
                '/tmp/tidb-ca.pem',
                Path(__file__).parent / 'certs' / 'tidb-ca.pem',
            ]
            
            cert_file = None
            for path in cert_paths:
                if Path(path).exists():
                    cert_file = str(path)
                    break
            
            if cert_file:
                clean_url = database_url.replace('mysql://', '').replace('mysql+pymysql://', '')
                database_url = f"mysql+pymysql://{clean_url}&ssl_ca={cert_file}&ssl_verify_cert=true"
            else:
                database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        
        elif database_url:
            database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        
        SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///scrapyard.db'
    else:
        # Local development
        SQLALCHEMY_DATABASE_URI = 'sqlite:///scrapyard.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }


# ========== DEBUG CODE - ADD THIS AFTER THE CONFIG CLASS ==========
import os
print("\n" + "="*60)
print("🔍 DATABASE CONFIGURATION DEBUG")
print("="*60)
print(f"RENDER env var: {os.environ.get('RENDER', 'NOT SET')}")
print(f"DATABASE_URL env var: {'✅ SET' if os.environ.get('DATABASE_URL') else '❌ NOT SET'}")

if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    if 'tidbcloud' in db_url.lower():
        print("✅ SUCCESS: Using TiDB Cloud! Data will persist across deploys!")
        # Mask the password for security
        import re
        masked_url = re.sub(r':([^@]+)@', ':***@', db_url)
        print(f"   URL: {masked_url}")
    elif 'sqlite' in db_url.lower():
        print("❌ CRITICAL: Using SQLite! Data will be lost on every deploy!")
    else:
        print(f"⚠️ Unknown database type: {db_url[:50]}...")
else:
    print("❌ CRITICAL: DATABASE_URL not set! Using fallback SQLite!")
    print("   Your data will be wiped on every deploy!")
print("="*60 + "\n")
# ========== END DEBUG CODE ==========