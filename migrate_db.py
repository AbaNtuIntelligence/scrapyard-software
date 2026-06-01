import sqlite3

# Connect to existing database
conn = sqlite3.connect('scrapyard.db')
cursor = conn.cursor()

try:
    # Add code column to materials if it doesn't exist
    cursor.execute('ALTER TABLE materials ADD COLUMN code TEXT')
    print('Added code column')
except sqlite3.OperationalError:
    print('Code column already exists')

try:
    # Add description column
    cursor.execute('ALTER TABLE materials ADD COLUMN description TEXT')
    print('Added description column')
except sqlite3.OperationalError:
    print('Description column already exists')

try:
    # Add is_active column
    cursor.execute('ALTER TABLE materials ADD COLUMN is_active BOOLEAN DEFAULT 1')
    print('Added is_active column')
except sqlite3.OperationalError:
    print('Is_active column already exists')

try:
    # Add material_code column to transactions
    cursor.execute('ALTER TABLE transactions ADD COLUMN material_code TEXT')
    print('Added material_code column to transactions')
except sqlite3.OperationalError:
    print('Material_code column already exists')

# Update existing materials with default codes
cursor.execute('SELECT id, name FROM materials')
materials = cursor.fetchall()

# Default codes mapping
code_mapping = {
    'Cardboard': 'K4',
    'Mixed Paper': 'K5', 
    'Aluminium Cans': 'AL1',
    'Steel/Tin Cans': 'ST1',
    'Plastic (PET)': 'PL1',
    'Plastic HDPE': 'PL2',
    'Glass': 'GL1',
    'Copper': 'CU1',
    'Brass': 'BR1',
    'Aluminium Scrap': 'AL2',
    'Stainless Steel': 'ST2',
    'Lead': 'PB1'
}

for mat_id, name in materials:
    code = code_mapping.get(name, name[:3].upper())
    cursor.execute('UPDATE materials SET code = ? WHERE id = ?', (code, mat_id))
    print(f'Updated {name} with code {code}')

conn.commit()
conn.close()
print('Migration complete!')
