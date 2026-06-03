import sqlite3
import os

# Database path - use the correct one for your setup
db_path = 'scrapyard.db'

# If app is using scrapyard.db in app folder, also update that one
app_db_path = 'app/scrapyard.db'

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Materials to add
materials_to_add = [
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('CU1', 'Copper', 120.00, 90.00, 'Clean copper wire'),
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
]

print('=' * 60)
print('ADDING MATERIALS TO DATABASE')
print('=' * 60)

for mat in materials_to_add:
    try:
        # Check if material already exists
        cursor.execute('SELECT code FROM materials WHERE code = ?', (mat[0],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE materials 
                SET name = ?, inbound_price = ?, outbound_price = ?, description = ?, is_active = 1
                WHERE code = ?
            ''', (mat[1], mat[2], mat[3], mat[4], mat[0]))
            print(f'✓ Updated: {mat[0]} - {mat[1]}')
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', mat)
            print(f'✓ Added: {mat[0]} - {mat[1]}')
            
    except Exception as e:
        print(f'✗ Error with {mat[0]}: {e}')

conn.commit()

# Verify
cursor.execute('SELECT code, name, inbound_price, outbound_price FROM materials WHERE code IN ("AL1", "CU1", "K4")')
print('\n✅ Verification:')
for row in cursor.fetchall():
    print(f'   {row[0]} - {row[1]}: In R{row[2]}/kg, Out R{row[3]}/kg')

conn.close()
print('\n✅ Done!')
