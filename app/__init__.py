from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import uuid
import random
import os

# ============ CREATE APP ============
app = Flask(__name__)
app.secret_key = 'scrapyard-secret-key-2026'


@app.route('/force-add-materials')
def force_add_materials():
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing
    cursor.execute('DELETE FROM materials')
    
    # Add all materials (same list as above)
    materials = [ ... ]  # Add your full list here
    
    for m in materials:
        cursor.execute('INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active) VALUES (?, ?, ?, ?, ?, 1)', m)
    
    conn.commit()
    count = cursor.execute('SELECT COUNT(*) FROM materials').fetchone()[0]
    conn.close()
    
    return f'Added {count} materials!'

# ============ DECORATORS ============
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============ DATABASE ============
def get_db():
    if os.environ.get('RENDER'):
        db_path = '/tmp/scrapyard.db'
    else:
        db_path = 'app/scrapyard.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Materials table
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

    # Sellers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            id_number TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            seller_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            material_code TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            amount REAL NOT NULL,
            scale_id TEXT,
            direction TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Insert default users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                      ('admin', 'admin123', 'admin', 'System Administrator'))
        cursor.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                      ('operator', 'operator123', 'operator', 'Yard Operator'))

    # Delete all existing materials to start fresh
    cursor.execute('DELETE FROM materials')
    print('Cleared existing materials')

    # Insert ALL materials
    print('📦 Adding all materials...')
    all_materials = [
        # Paper Products (7)
        ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
        ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
        ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
        ('K7', 'Shredded Paper', 0.60, 0.30, 'Shredded document paper'),
        ('K8', 'Books', 0.50, 0.25, 'Paperback and hardcover books'),
        ('K9', 'Newspapers', 0.70, 0.35, 'Clean newspapers only'),
        ('K10', 'Kraft Paper', 1.10, 0.55, 'Brown kraft paper bags'),
        
        # Plastics (8)
        ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
        ('PL2', 'HDPE Natural', 5.00, 3.00, 'Natural HDPE jugs'),
        ('PL3', 'HDPE Colored', 3.50, 2.00, 'Colored HDPE containers'),
        ('PL4', 'PVC Rigid', 2.50, 1.20, 'PVC pipes and fittings'),
        ('PL5', 'LDPE Film', 2.00, 1.00, 'Plastic bags, stretch film'),
        ('PL6', 'PP Rigid', 3.00, 1.50, 'Hard plastic containers'),
        ('PL7', 'Mixed Plastics', 2.00, 1.00, 'Mixed unsorted plastics'),
        
        # Glass (4)
        ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
        ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass'),
        ('GL3', 'Green Glass', 0.50, 0.25, 'Green glass bottles'),
        ('GL4', 'Mixed Glass', 0.40, 0.20, 'Mixed color glass'),
        
        # Aluminium (6)
        ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
        ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
        ('AL3', 'Aluminium Wheels', 22.00, 15.00, 'Clean aluminium wheels'),
        ('AL4', 'Aluminium Extrusions', 20.00, 14.00, 'Window frames, doors'),
        ('AL5', 'Aluminium Sheet', 19.00, 13.00, 'Aluminium sheet and plate'),
        ('AL6', 'Aluminium Cast', 17.00, 11.00, 'Cast aluminium parts'),
        
        # Copper (5)
        ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
        ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
        ('CU3', 'Copper Wire', 120.00, 90.00, 'Insulated copper wire'),
        ('CU4', 'Copper Pipe', 135.00, 105.00, 'Clean copper plumbing pipe'),
        ('CU5', 'Copper Sheet', 125.00, 95.00, 'Copper sheet and plate'),
        
        # Brass & Bronze (5)
        ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
        ('BR2', 'Red Brass', 80.00, 55.00, 'Red brass plumbing fixtures'),
        ('BR3', 'Bronze', 75.00, 52.00, 'Bronze statues, bearings'),
        ('BR4', 'Brass Radiator', 55.00, 38.00, 'Brass/copper radiators'),
        
        # Steel & Iron (7)
        ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
        ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel'),
        ('ST3', 'Cast Iron', 3.50, 2.00, 'Cast iron pipes, engine blocks'),
        ('ST4', 'Heavy Steel', 4.00, 2.50, 'Construction steel, beams'),
        ('ST5', 'Light Iron', 2.00, 1.00, 'Light gauge steel'),
        ('ST6', 'Sheet Metal', 3.00, 1.80, 'Mixed sheet metal scrap'),
        
        # Other Metals (5)
        ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
        ('PB2', 'Lead Batteries', 18.00, 12.00, 'Car batteries'),
        ('ZN1', 'Zinc', 16.00, 10.00, 'Zinc scrap'),
        ('NI1', 'Nickel', 50.00, 35.00, 'Nickel scrap'),
        
        # Electronics (6)
        ('CB1', 'Circuit Boards', 45.00, 30.00, 'Green circuit boards'),
        ('CB2', 'Motherboards', 120.00, 80.00, 'Computer motherboards'),
        ('CB3', 'IC Chips', 500.00, 350.00, 'Computer processors'),
        ('CB4', 'Hard Drives', 15.00, 8.00, 'Complete hard drives'),
        ('CB5', 'Cell Phones', 50.00, 30.00, 'Complete cell phones'),
        
        # Batteries (3)
        ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
        ('BT2', 'NiMH Batteries', 15.00, 8.00, 'Nickel metal hydride'),
        
        # Other (5)
        ('TR1', 'Car Tires', 2.00, 1.00, 'Passenger car tires'),
        ('EL1', 'Electric Motors', 12.00, 7.00, 'Copper wound motors'),
        ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
    ]
    
    for m in all_materials:
        try:
            cursor.execute('''
                INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', m)
            print(f'  ✓ Added: {m[0]} - {m[1]}')
        except Exception as e:
            print(f'  ✗ Error adding {m[0]}: {e}')
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM materials')
    count = cursor.fetchone()[0]
    print(f'✅ Total materials in database: {count}')
    
    conn.close()
init_db()

# ============ HELPERS ============
def get_mock_weight():
    return round(random.uniform(0.5, 100.0), 2)

# ============ AUTH ROUTES ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['is_admin'] = (user['role'] == 'admin')
            flash(f'Welcome {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============ MAIN ROUTES ============
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = datetime.now().date()
        
        # Get today's transactions
        cursor.execute('''
            SELECT t.*, s.full_name as seller_name, m.name as material_name
            FROM transactions t
            LEFT JOIN sellers s ON t.seller_id = s.id
            LEFT JOIN materials m ON t.material_id = m.id
            WHERE DATE(t.timestamp) = ?
            ORDER BY t.timestamp DESC
            LIMIT 20
        ''', (today,))
        
        rows = cursor.fetchall()
        today_transactions = []
        for row in rows:
            trans = dict(row)
            trans['time_display'] = trans.get('timestamp', '')[:16] if trans.get('timestamp') else ''
            today_transactions.append(trans)
        
        # Get totals
        cursor.execute('''
            SELECT 
                COALESCE(SUM(weight_kg), 0) as total_weight,
                COALESCE(SUM(amount), 0) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE DATE(timestamp) = ?
        ''', (today,))
        totals = cursor.fetchone()
        conn.close()
        
        return render_template('index.html',
                             today_transactions=today_transactions,
                             today_weight=totals['total_weight'],
                             today_amount=totals['total_amount'],
                             today_count=totals['transaction_count'],
                             active_page='dashboard')
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('index.html',
                             today_transactions=[],
                             today_weight=0,
                             today_amount=0,
                             today_count=0,
                             active_page='dashboard')

@app.route('/materials')
@login_required
def materials():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    return render_template('materials.html', materials=materials, active_page='materials')

@app.route('/scales')
@login_required
def scales_dashboard():
    return render_template('scales_dashboard.html', active_page='scales')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', active_page='reports')

@app.route('/sellers')
@login_required
def sellers():
    return render_template('sellers.html', active_page='sellers')

@app.route('/new_transaction', methods=['GET', 'POST'])
@login_required
def new_transaction():
    if request.method == 'POST':
        flash('Transaction saved!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('new_transaction.html', active_page='new_transaction')

# ============ API ROUTES ============
@app.route('/api/get_weight')
def api_get_weight():
    return jsonify({'success': True, 'weight': get_mock_weight()})

@app.route('/api/materials', methods=['GET'])
@login_required
def api_get_materials():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    return jsonify([dict(m) for m in materials])

@app.route('/api/materials', methods=['POST'])
@admin_required
def api_create_material():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (data['code'], data['name'], data['inbound_price'], data['outbound_price'], data.get('description', '')))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Material code or name already exists'}), 400
    finally:
        conn.close()

# ============ RUN ============
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)