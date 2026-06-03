import sqlite3
import os

# Find the correct database path
db_paths = [
    'scrapyard.db',
    'app/scrapyard.db',
    'instance/scrapyard.db',
]

db_used = None
for path in db_paths:
    if os.path.exists(path):
        db_used = path
        print(f'Found database at: {path}')
        break

if not db_used:
    print('No database found. Creating new one...')
    db_used = 'scrapyard.db'

conn = sqlite3.connect(db_used)
cursor = conn.cursor()

# Make sure materials table exists
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

# All materials to add
materials = [
    # Paper Products
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
    ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines, office paper'),
    ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
    ('K7', 'Shredded Paper', 0.60, 0.30, 'Shredded document paper'),
    
    # Metals - Aluminium
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
    ('AL3', 'Aluminium Wheels', 22.00, 15.00, 'Clean aluminium wheels'),
    
    # Metals - Copper
    ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
    ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
    ('CU3', 'Copper Wire', 120.00, 90.00, 'Insulated copper wire'),
    
    # Metals - Brass & Steel
    ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
    ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
    ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel scrap'),
    ('ST3', 'Cast Iron', 3.50, 2.00, 'Cast iron pipes, engine blocks'),
    
    # Other Metals
    ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
    ('ZN1', 'Zinc', 16.00, 10.00, 'Zinc scrap'),
    
    # Plastics
    ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
    ('PL2', 'HDPE Plastic', 3.80, 2.00, 'Milk bottles, detergent'),
    ('PL3', 'PVC Plastic', 2.50, 1.20, 'PVC pipes and fittings'),
    ('PL4', 'Mixed Plastics', 2.00, 1.00, 'Mixed unsorted plastics'),
    
    # Glass
    ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
    ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass'),
    ('GL3', 'Green Glass', 0.50, 0.25, 'Green glass bottles'),
    
    # Electronics
    ('CB1', 'Circuit Boards', 45.00, 30.00, 'Green circuit boards'),
    ('CB2', 'Motherboards', 120.00, 80.00, 'Computer motherboards'),
    ('CB3', 'IC Chips', 500.00, 350.00, 'Computer processors'),
    
    # Batteries
    ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
    ('BT2', 'Lead Batteries', 18.00, 12.00, 'Car batteries'),
    
    # Other
    ('TR1', 'Car Tires', 2.00, 1.00, 'Passenger car tires'),
    ('EL1', 'Electric Motors', 12.00, 7.00, 'Copper wound motors'),
    ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
]

print('=' * 60)
print(f'Adding materials to: {db_used}')
print('=' * 60)

added = 0
for mat in materials:
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', mat)
        added += 1
        print(f'✓ {mat[0]:<10} {mat[1]:<25} R{mat[2]:>6.2f} in / R{mat[3]:>6.2f} out')
    except Exception as e:
        print(f'✗ Error with {mat[0]}: {e}')

conn.commit()

# Show count
cursor.execute('SELECT COUNT(*) FROM materials')
count = cursor.fetchone()[0]
print('=' * 60)
print(f'✅ Total materials in database: {count}')
print('=' * 60)

# Show all materials
print('\n📋 All materials in database:')
cursor.execute('SELECT code, name, inbound_price, outbound_price FROM materials ORDER BY code')
for row in cursor.fetchall():
    print(f'   {row[0]:<10} {row[1]:<25} In: R{row[2]:>8.2f} Out: R{row[3]:>8.2f}')

conn.close()
print('\n✅ Done! Restart Flask and refresh your Materials page.')
