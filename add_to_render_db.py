import pymysql
import os

# TiDB Cloud connection details
connection = pymysql.connect(
    host='gateway01.eu-central-1.prod.aws.tidbcloud.com',
    port=4000,
    user='se5M4cznTvHESuQ.root',
    password='ScrapYardPassword123!',
    database='scrapsoft',
    ssl={'ca': 'certs/tidb-ca.pem'} if os.path.exists('certs/tidb-ca.pem') else None
)

cursor = connection.cursor()

# Create materials table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        id INT PRIMARY KEY AUTO_INCREMENT,
        code VARCHAR(10) UNIQUE NOT NULL,
        name VARCHAR(50) UNIQUE NOT NULL,
        inbound_price DECIMAL(10,2),
        outbound_price DECIMAL(10,2),
        description TEXT,
        is_active BOOLEAN DEFAULT 1
    )
''')

# Materials to add
materials = [
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
    ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
    ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
    ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
    ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
    ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
    ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
    ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel'),
    ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
    ('PL2', 'HDPE Plastic', 3.80, 2.00, 'Milk bottles, detergent'),
    ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
    ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
    ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
    ('CB1', 'Circuit Boards', 45.00, 30.00, 'Circuit boards'),
    ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
]

print('=' * 60)
print('Adding materials to Render (TiDB Cloud) database')
print('=' * 60)

added = 0
for mat in materials:
    try:
        cursor.execute('''
            INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                inbound_price = VALUES(inbound_price),
                outbound_price = VALUES(outbound_price),
                description = VALUES(description)
        ''', mat)
        added += 1
        print(f'✓ Added: {mat[0]} - {mat[1]}')
    except Exception as e:
        print(f'✗ Error with {mat[0]}: {e}')

connection.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM materials')
count = cursor.fetchone()[0]
print('=' * 60)
print(f'✅ Total materials in Render database: {count}')
print('=' * 60)

cursor.close()
connection.close()
print('\n✅ Done! Refresh your Render app.')
