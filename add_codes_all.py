import sqlite3
import os

# Try multiple database locations
db_paths = [
    'scrapyard.db',
    'app/scrapyard.db',
    '../scrapyard.db',
]

materials_to_add = [
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('CU1', 'Copper', 120.00, 90.00, 'Clean copper wire'),
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
]

print('=' * 60)
print('ADDING MATERIALS TO DATABASE')
print('=' * 60)

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f'\n📁 Found database at: {db_path}')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for mat in materials_to_add:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', mat)
                print(f'✓ {mat[0]} - {mat[1]} added to {db_path}')
            except Exception as e:
                print(f'✗ Error: {e}')
        
        conn.commit()
        conn.close()

print('\n✅ Done!')
