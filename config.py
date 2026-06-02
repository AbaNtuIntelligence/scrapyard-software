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
            # Try multiple possible locations
            cert_paths = [
                '/etc/ssl/certs/tidb-ca.pem',  # Render system path
                '/tmp/tidb-ca.pem',             # Render temp path
                Path(__file__).parent / 'certs' / 'tidb-ca.pem',  # Local project path
            ]
            
            cert_file = None
            for path in cert_paths:
                if Path(path).exists():
                    cert_file = str(path)
                    break
            
            # If certificate exists, add SSL parameters
            if cert_file:
                # Convert mysql:// to mysql+pymysql:// and add SSL
                clean_url = database_url.replace('mysql://', '').replace('mysql+pymysql://', '')
                database_url = f"mysql+pymysql://{clean_url}&ssl_ca={cert_file}&ssl_verify_cert=true"
            else:
                # Fallback without certificate (may still work on some systems)
                database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        
        elif database_url:
            # Non-TiDB database
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
