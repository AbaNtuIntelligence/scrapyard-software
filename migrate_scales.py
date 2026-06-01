import sqlite3
import os

def run_migration():
    # Connect to database
    db_path = 'scrapyard.db'
    if os.environ.get('RENDER'):
        db_path = '/tmp/scrapyard.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting scale management migration...")
    
    # Create scale_config table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scale_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scale_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                serial_number TEXT,
                model TEXT,
                capacity_kg INTEGER,
                last_calibration DATE,
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                display_order INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')
        print("✓ Created scale_config table")
    except sqlite3.OperationalError as e:
        print(f"  Scale config table: {e}")
    
    # Create scale_calibration table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scale_calibration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scale_id TEXT NOT NULL,
                calibration_date DATE NOT NULL,
                next_calibration_date DATE,
                certified_by TEXT,
                certificate_number TEXT,
                notes TEXT
            )
        ''')
        print("✓ Created scale_calibration table")
    except sqlite3.OperationalError as e:
        print(f"  Scale calibration table: {e}")
    
    # Insert default scale configuration if empty
    cursor.execute('SELECT COUNT(*) FROM scale_config')
    if cursor.fetchone()[0] == 0:
        scales = [
            ('scale_1', 'Main Gate Scale', 'Main Entrance', 5000, 1),
            ('scale_2', 'Secondary Scale', 'South Gate', 3000, 2),
            ('scale_3', 'Processing Scale', 'Sorting Area', 1000, 3),
            ('scale_4', 'Weighbridge Scale', 'Weighbridge', 20000, 4)
        ]
        
        for scale in scales:
            cursor.execute('''
                INSERT INTO scale_config (scale_id, name, location, capacity_kg, display_order, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', scale)
        print(f"✓ Inserted {len(scales)} default scales")
    
    # Add missing columns to existing tables
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN scale_id TEXT')
        print("✓ Added scale_id column to transactions")
    except sqlite3.OperationalError:
        print("  Scale_id column already exists")
    
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN direction TEXT')
        print("✓ Added direction column to transactions")
    except sqlite3.OperationalError:
        print("  Direction column already exists")
    
    try:
        cursor.execute('ALTER TABLE transactions ADD COLUMN reference_number TEXT')
        print("✓ Added reference_number column to transactions")
    except sqlite3.OperationalError:
        print("  Reference_number column already exists")
    
    try:
        cursor.execute('ALTER TABLE materials ADD COLUMN inbound_price REAL')
        print("✓ Added inbound_price column to materials")
    except sqlite3.OperationalError:
        print("  Inbound_price column already exists")
    
    try:
        cursor.execute('ALTER TABLE materials ADD COLUMN outbound_price REAL')
        print("✓ Added outbound_price column to materials")
    except sqlite3.OperationalError:
        print("  Outbound_price column already exists")
    
    # Update existing materials with prices if needed
    cursor.execute('SELECT COUNT(*) FROM materials WHERE inbound_price IS NULL')
    if cursor.fetchone()[0] > 0:
        material_prices = [
            ('K4', 'Cardboard', 1.50, 0.80),
            ('K5', 'Mixed Paper', 0.80, 0.40),
            ('AL1', 'Aluminium Cans', 25.00, 18.00),
            ('ST1', 'Steel/Tin Cans', 2.20, 1.50),
            ('PL1', 'Plastic PET', 4.50, 2.50),
            ('CU1', 'Copper', 120.00, 90.00),
            ('BR1', 'Brass', 65.00, 45.00),
            ('AL2', 'Aluminium Scrap', 18.00, 12.00),
            ('ST2', 'Stainless Steel', 15.00, 10.00),
            ('PB1', 'Lead', 22.00, 15.00),
            ('GL1', 'Glass', 0.60, 0.30),
            ('PL2', 'Plastic HDPE', 3.80, 2.00)
        ]
        
        for code, name, in_price, out_price in material_prices:
            cursor.execute('''
                UPDATE materials 
                SET inbound_price = ?, outbound_price = ? 
                WHERE code = ? OR name = ?
            ''', (in_price, out_price, code, name))
        print(f"✓ Updated material prices for {len(material_prices)} materials")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("\nNew tables created:")
    print("  - scale_config: Store scale settings")
    print("  - scale_calibration: Track calibration history")
    print("\nNew columns added:")
    print("  - transactions.scale_id: Track which scale was used")
    print("  - transactions.direction: inbound/outbound")
    print("  - materials.inbound_price/outbound_price: Separate pricing")

if __name__ == '__main__':
    run_migration()
