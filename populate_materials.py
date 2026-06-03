import sqlite3
import os

# Database path
db_path = 'scrapyard.db'

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Clear existing materials (optional - remove if you want to keep existing)
# cursor.execute('DELETE FROM materials')
# print('Cleared existing materials')

# Comprehensive materials list
materials = [
    # ============ PAPER PRODUCTS ============
    ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes and sheets'),
    ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines, office paper'),
    ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
    ('K7', 'Shredded Paper', 0.60, 0.30, 'Shredded document paper'),
    ('K8', 'Books', 0.50, 0.25, 'Paperback and hardcover books'),
    ('K9', 'Newspapers', 0.70, 0.35, 'Clean newspapers only'),
    ('K10', 'Magazines', 0.60, 0.30, 'Glossy magazines and catalogs'),
    
    # ============ ALUMINIUM ============
    ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
    ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap, siding'),
    ('AL3', 'Aluminium Wheels', 22.00, 15.00, 'Clean aluminium wheels/rims'),
    ('AL4', 'Aluminium Extrusions', 20.00, 14.00, 'Window frames, door frames'),
    ('AL5', 'Aluminium Sheet', 19.00, 13.00, 'Aluminium sheet and plate'),
    ('AL6', 'Aluminium Cast', 17.00, 11.00, 'Cast aluminium parts'),
    
    # ============ COPPER ============
    ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
    ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe, heavy wire'),
    ('CU3', 'Copper #2', 110.00, 85.00, 'Coated copper, mixed copper'),
    ('CU4', 'Copper Wire', 120.00, 90.00, 'Insulated copper wire'),
    ('CU5', 'Copper Pipe', 135.00, 105.00, 'Clean copper plumbing pipe'),
    ('CU6', 'Copper Sheet', 125.00, 95.00, 'Copper sheet and plate'),
    
    # ============ BRASS & BRONZE ============
    ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
    ('BR2', 'Red Brass', 80.00, 55.00, 'Red brass plumbing fixtures'),
    ('BR3', 'Bronze', 75.00, 52.00, 'Bronze statues, bearings'),
    ('BR4', 'Brass Radiator', 55.00, 38.00, 'Brass/copper radiators'),
    ('BR5', 'Brass Turnings', 45.00, 30.00, 'Brass machining shavings'),
    
    # ============ STEEL & IRON ============
    ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
    ('ST2', 'Stainless Steel 304', 15.00, 10.00, '304 stainless steel scrap'),
    ('ST3', 'Stainless Steel 316', 18.00, 12.00, '316 stainless steel scrap'),
    ('ST4', 'Cast Iron', 3.50, 2.00, 'Cast iron pipes, engine blocks'),
    ('ST5', 'Heavy Steel', 4.00, 2.50, 'Construction steel, beams, rebar'),
    ('ST6', 'Light Iron', 2.00, 1.00, 'Light gauge steel, appliances'),
    ('ST7', 'Sheet Metal', 3.00, 1.80, 'Mixed sheet metal scrap'),
    
    # ============ OTHER METALS ============
    ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
    ('PB2', 'Lead Batteries', 18.00, 12.00, 'Car batteries'),
    ('ZN1', 'Zinc', 16.00, 10.00, 'Zinc scrap, galvanized materials'),
    ('NI1', 'Nickel', 50.00, 35.00, 'Nickel scrap and alloys'),
    ('TI1', 'Titanium', 80.00, 55.00, 'Titanium scrap'),
    
    # ============ PLASTICS ============
    ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles - Type 1'),
    ('PL2', 'HDPE Natural', 5.00, 3.00, 'Natural HDPE jugs - Type 2'),
    ('PL3', 'HDPE Colored', 3.50, 2.00, 'Colored HDPE containers'),
    ('PL4', 'PVC Rigid', 2.50, 1.20, 'PVC pipes and fittings'),
    ('PL5', 'LDPE Film', 2.00, 1.00, 'Plastic bags, stretch film'),
    ('PL6', 'PP Rigid', 3.00, 1.50, 'Hard plastic containers'),
    ('PL7', 'PS Solid', 2.50, 1.20, 'Rigid polystyrene'),
    ('PL8', 'PS Foam', 1.50, 0.70, 'Styrofoam, foam cups'),
    ('PL9', 'Mixed Plastics', 2.00, 1.00, 'Mixed unsorted plastics'),
    ('PL10', 'ABS Plastic', 3.50, 2.00, 'ABS plastic from electronics'),
    
    # ============ GLASS ============
    ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles and jars'),
    ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass bottles'),
    ('GL3', 'Green Glass', 0.50, 0.25, 'Green glass bottles'),
    ('GL4', 'Mixed Glass', 0.40, 0.20, 'Mixed color glass'),
    
    # ============ ELECTRONICS ============
    ('CB1', 'Motherboards', 120.00, 80.00, 'Computer motherboards'),
    ('CB2', 'Low Grade Boards', 20.00, 10.00, 'TV/consumer electronics boards'),
    ('CB3', 'High Grade Boards', 150.00, 100.00, 'Server/telecom boards'),
    ('CB4', 'IC Chips', 500.00, 350.00, 'Computer processors and chips'),
    ('CB5', 'Memory Modules', 300.00, 200.00, 'RAM sticks'),
    ('CB6', 'Hard Drives', 15.00, 8.00, 'Complete hard drives'),
    ('CB7', 'Cell Phones', 50.00, 30.00, 'Complete cell phones'),
    ('CB8', 'Laptops', 30.00, 18.00, 'Complete laptops'),
    ('CB9', 'Cables', 10.00, 5.00, 'Mixed computer cables'),
    
    # ============ BATTERIES ============
    ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion rechargeable batteries'),
    ('BT2', 'NiMH Batteries', 15.00, 8.00, 'Nickel metal hydride batteries'),
    ('BT3', 'Lead Batteries', 18.00, 12.00, 'Car batteries'),
    
    # ============ OTHER ============
    ('TR1', 'Car Tires', 2.00, 1.00, 'Passenger car tires'),
    ('TR2', 'Truck Tires', 5.00, 2.50, 'Heavy truck tires'),
    ('RB1', 'Rubber', 1.50, 0.80, 'Mixed rubber scrap'),
    ('EL1', 'Electric Motors', 12.00, 7.00, 'Copper wound electric motors'),
    ('EL2', 'Alternators', 15.00, 9.00, 'Automotive alternators'),
    ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
]

print('=' * 60)
print('POPULATING MATERIALS DATABASE')
print('=' * 60)

inserted = 0
skipped = 0

for mat in materials:
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', mat)
        inserted += 1
        print(f'✓ {mat[0]:<10} {mat[1]:<25} R{mat[2]:>8} (in) / R{mat[3]:>8} (out)')
    except Exception as e:
        skipped += 1
        print(f'✗ Error: {mat[0]} - {e}')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM materials')
count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM materials WHERE is_active = 1')
active_count = cursor.fetchone()[0]

print('=' * 60)
print(f'✅ Successfully inserted: {inserted} materials')
print(f'📊 Total materials in database: {count}')
print(f'🟢 Active materials: {active_count}')
print('=' * 60)

# Show first 10 materials
print('\n📋 First 10 materials in database:')
cursor.execute('SELECT code, name, inbound_price, outbound_price FROM materials ORDER BY code LIMIT 10')
for row in cursor.fetchall():
    print(f'   {row[0]:<10} {row[1]:<25} In: R{row[2]:<8} Out: R{row[3]}')

conn.close()
print('\n✅ Database population complete!')
