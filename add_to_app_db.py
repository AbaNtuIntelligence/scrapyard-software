import sqlite3
import os

# Use the correct database path that your app is using
db_path = 'app/scrapyard.db'

print(f'Adding materials to: {db_path}')
print('=' * 60)

# Make sure the directory exists
os.makedirs('app', exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create materials table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT UNIQUE NOT NULL,
        inbound_price REAL,
        outbound_price REAL,
        description TEXT,
        is_active BOOLEAN DEFAULT 1
    )
''')

# Materials to add
materials = [
    # Paper Products
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
    ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
    ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
    
    # Metals - Aluminium
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
    
    # Metals - Copper
    ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
    ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
    
    # Metals - Brass & Steel
    ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
    ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
    ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel'),
    
    # Other Metals
    ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
    
    # Plastics
    ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
    ('PL2', 'HDPE Plastic', 3.80, 2.00, 'Milk bottles, detergent'),
    
    # Glass
    ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
    ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass'),
    
    # Electronics
    ('CB1', 'Circuit Boards', 45.00, 30.00, 'Circuit boards'),
    ('CB2', 'Motherboards', 120.00, 80.00, 'Computer motherboards'),
    
    # Batteries
    ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
    
    # Other
    ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
]

added = 0
for mat in materials:
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', mat)
        added += 1
        print(f'✓ Added: {mat[0]} - {mat[1]}')
    except Exception as e:
        print(f'✗ Error: {mat[0]} - {e}')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM materials')
count = cursor.fetchone()[0]
print('=' * 60)
print(f'✅ Total materials in app database: {count}')
print('=' * 60)

# Show all materials
cursor.execute('SELECT code, name, inbound_price, outbound_price FROM materials ORDER BY code')
print('\n📋 Materials in database:')
for row in cursor.fetchall():
    print(f'   {row[0]:<10} {row[1]:<25} R{row[2]:>8.2f} in / R{row[3]:>8.2f} out')

conn.close()
print('\n✅ Done! Restart Flask and refresh your Materials page.')
