# Add this to config.py - put it right after the Config class
import os
print("\n" + "="*60)
print("🔍 DATABASE CONFIGURATION DEBUG")
print("="*60)
print(f"RENDER env var: {os.environ.get('RENDER', 'NOT SET')}")
print(f"DATABASE_URL env var: {'✅ SET' if os.environ.get('DATABASE_URL') else '❌ NOT SET'}")

if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    if 'sqlite' in db_url.lower():
        print("❌ CRITICAL: Using SQLite! Data will be lost on every deploy!")
        print(f"   URL: {db_url}")
    elif 'tidbcloud' in db_url.lower():
        print("✅ SUCCESS: Using TiDB Cloud! Data will persist across deploys!")
        # Mask password for security
        import re
        masked_url = re.sub(r':([^@]+)@', ':***@', db_url)
        print(f"   URL: {masked_url}")
    else:
        print(f"⚠️ Unknown database type: {db_url[:50]}...")
else:
    print("❌ CRITICAL: DATABASE_URL not set! Using fallback SQLite!")
print("="*60 + "\n")