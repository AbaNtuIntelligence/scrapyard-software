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



@app.route('/api/get_all_weights')
def api_get_all_weights():
    return jsonify({'success': True, 'scales': {}})

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


@app.route('/admin/add-scales')
def admin_add_scales():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scale_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scale_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            capacity_kg INTEGER,
            is_operational BOOLEAN DEFAULT 1,
            is_active BOOLEAN DEFAULT 0,
            display_order INTEGER DEFAULT 0
        )
    ''')
    
    # Insert default scales
    scales = [
        ('scale_1', 'Main Gate Scale', 'Main Entrance', 5000, 1, 1, 1),
        ('scale_2', 'Secondary Scale', 'South Gate', 3000, 1, 0, 2),
        ('scale_3', 'Processing Scale', 'Sorting Area', 1000, 1, 0, 3),
        ('scale_4', 'Weighbridge Scale', 'Weighbridge', 20000, 1, 0, 4),
    ]
    
    for s in scales:
        cursor.execute('''
            INSERT OR REPLACE INTO scale_config (scale_id, name, location, capacity_kg, is_operational, is_active, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', s)
    
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM scale_config')
    count = cursor.fetchone()[0]
    conn.close()
    
    return f'<h2>✅ Added {count} scales to database!</h2><p>Scales added: Main Gate, Secondary, Processing, Weighbridge</p><a href="/scales">Go to Scales Page</a>'



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
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all scales from database
        cursor.execute('SELECT * FROM scale_config ORDER BY display_order')
        db_scales = cursor.fetchall()
        
        # If no scales in database, create defaults
        if len(db_scales) == 0:
            default_scales = [
                ('scale_1', 'Main Gate Scale', 'Main Entrance', 5000, 1, 1),
                ('scale_2', 'Secondary Scale', 'South Gate', 3000, 1, 0),
                ('scale_3', 'Processing Scale', 'Sorting Area', 1000, 1, 0),
                ('scale_4', 'Weighbridge Scale', 'Weighbridge', 20000, 1, 0),
            ]
            for s in default_scales:
                cursor.execute('''
                    INSERT INTO scale_config (scale_id, name, location, capacity_kg, is_operational, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', s)
            conn.commit()
            
            # Fetch again
            cursor.execute('SELECT * FROM scale_config ORDER BY display_order')
            db_scales = cursor.fetchall()
        
        scales = {}
        for scale in db_scales:
            scales[scale['scale_id']] = {
                'name': scale['name'],
                'location': scale['location'],
                'capacity_kg': scale['capacity_kg'],
                'is_operational': scale.get('is_operational', 1),
                'is_active': scale.get('is_active', 0),
                'icon': 'fa-balance-scale'
            }
        
        # Get active scale
        active_scale = None
        active_scale_name = 'None'
        for scale_id, scale in scales.items():
            if scale.get('is_active'):
                active_scale = scale_id
                active_scale_name = scale['name']
                break
        
        conn.close()
        
        return render_template('scales_dashboard.html', 
                             scales=scales,
                             active_scale=active_scale,
                             active_scale_name=active_scale_name,
                             active_page='scales')
                             
    except Exception as e:
        print(f"Scales error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('scales_dashboard.html', 
                             scales={},
                             active_scale=None,
                             active_scale_name='None',
                             active_page='scales')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', active_page='reports')

@app.route('/sellers')
@login_required
def sellers():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all sellers with their transaction totals
        cursor.execute('''
            SELECT 
                s.id,
                s.full_name,
                s.id_number,
                s.phone,
                s.created_at,
                COUNT(t.id) as transaction_count,
                COALESCE(SUM(t.weight_kg), 0) as total_weight,
                COALESCE(SUM(t.amount), 0) as total_earned
            FROM sellers s
            LEFT JOIN transactions t ON s.id = t.seller_id
            GROUP BY s.id, s.full_name, s.id_number, s.phone, s.created_at
            ORDER BY s.full_name
        ''')
        
        sellers = cursor.fetchall()
        conn.close()
        
        return render_template('sellers.html', sellers=sellers, active_page='sellers')
        
    except Exception as e:
        print(f"Sellers error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading sellers: {str(e)}', 'danger')
        return render_template('sellers.html', sellers=[], active_page='sellers')

@app.route('/new_transaction', methods=['GET', 'POST'])
@login_required
def new_transaction():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            seller_name = request.form['seller_name']
            id_number = request.form['id_number']
            phone = request.form.get('phone', '')
            material_id = request.form['material_id']
            scale_id = request.form.get('scale_id', 'scale_1')
            direction = request.form.get('direction', 'inbound')
            weight = float(request.form['weight'])
            
            # Get material price based on direction
            if direction == 'inbound':
                cursor.execute('SELECT code, inbound_price as price FROM materials WHERE id = ?', (material_id,))
            else:
                cursor.execute('SELECT code, outbound_price as price FROM materials WHERE id = ?', (material_id,))
            
            material = cursor.fetchone()
            if not material:
                flash('Material not found', 'danger')
                return redirect(url_for('new_transaction'))
            
            amount = weight * material['price']
            
            # Create or get seller
            cursor.execute('SELECT id FROM sellers WHERE id_number = ?', (id_number,))
            seller = cursor.fetchone()
            
            if seller:
                seller_id = seller['id']
            else:
                cursor.execute('INSERT INTO sellers (full_name, id_number, phone) VALUES (?, ?, ?)',
                             (seller_name, id_number, phone))
                seller_id = cursor.lastrowid
            
            # Create transaction
            ticket_number = f"{direction[:3].upper()}{uuid.uuid4().hex[:5].upper()}"
            cursor.execute('''
                INSERT INTO transactions (ticket_number, seller_id, material_id, material_code, weight_kg, amount, scale_id, direction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ticket_number, seller_id, material_id, material['code'], weight, amount, scale_id, direction))
            
            conn.commit()
            conn.close()
            
            flash(f'✓ Transaction saved! Ticket: {ticket_number}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error saving transaction: {str(e)}', 'danger')
            return redirect(url_for('new_transaction'))
    
    # GET request - show form
    cursor.execute('SELECT * FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    
    return render_template('new_transaction.html', materials=materials, active_page='new_transaction')

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

@app.route('/api/reports/generate', methods=['GET'])
@login_required
def api_generate_report():
    try:
        report_type = request.args.get('report_type', 'inbound')
        date_range = request.args.get('date_range', 'month')
        start_date_str = request.args.get('start_date', '')
        end_date_str = request.args.get('end_date', '')
        
        # Calculate date range
        end_date = datetime.now()
        if date_range == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = end_date - timedelta(days=end_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'month':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'custom' and start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            start_date = end_date - timedelta(days=30)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if report_type == 'inbound' or report_type == 'outbound':
            # Material report
            cursor.execute('''
                SELECT 
                    m.code, 
                    m.name, 
                    COALESCE(SUM(t.weight_kg), 0) as total_weight,
                    COALESCE(SUM(t.amount), 0) as total_amount,
                    COUNT(t.id) as transaction_count,
                    CASE 
                        WHEN SUM(t.weight_kg) > 0 
                        THEN ROUND(SUM(t.amount) / SUM(t.weight_kg), 2)
                        ELSE 0 
                    END as avg_price
                FROM materials m
                LEFT JOIN transactions t ON m.id = t.material_id 
                    AND t.direction = ?
                    AND DATE(t.timestamp) BETWEEN DATE(?) AND DATE(?)
                WHERE m.is_active = 1
                GROUP BY m.id, m.code, m.name
                HAVING total_weight > 0 OR total_amount > 0
                ORDER BY total_weight DESC
            ''', (report_type, start_date, end_date))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'code': row['code'],
                    'name': row['name'],
                    'total_weight': float(row['total_weight']),
                    'total_amount': float(row['total_amount']),
                    'transaction_count': row['transaction_count'],
                    'avg_price': float(row['avg_price'])
                })
            
            total_weight = sum(i['total_weight'] for i in items)
            total_amount = sum(i['total_amount'] for i in items)
            
            result = {
                'success': True,
                'report_type': report_type,
                'period': f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}',
                'items': items,
                'total_weight': total_weight,
                'total_amount': total_amount,
                'transaction_count': sum(i['transaction_count'] for i in items),
                'avg_price': total_amount / total_weight if total_weight > 0 else 0
            }
            
        elif report_type == 'seller':
            # Seller performance report
            cursor.execute('''
                SELECT 
                    s.full_name,
                    s.id_number,
                    s.phone,
                    COALESCE(SUM(t.weight_kg), 0) as total_weight,
                    COALESCE(SUM(t.amount), 0) as total_amount,
                    COUNT(t.id) as transaction_count,
                    MIN(t.timestamp) as first_transaction,
                    MAX(t.timestamp) as last_transaction
                FROM sellers s
                LEFT JOIN transactions t ON s.id = t.seller_id
                    AND DATE(t.timestamp) BETWEEN DATE(?) AND DATE(?)
                GROUP BY s.id, s.full_name, s.id_number, s.phone
                HAVING total_weight > 0 OR total_amount > 0
                ORDER BY total_amount DESC
            ''', (start_date, end_date))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'full_name': row['full_name'],
                    'id_number': row['id_number'],
                    'phone': row['phone'] or '-',
                    'total_weight': float(row['total_weight']),
                    'total_amount': float(row['total_amount']),
                    'transaction_count': row['transaction_count'],
                    'first_transaction': row['first_transaction'][:10] if row['first_transaction'] else '-',
                    'last_transaction': row['last_transaction'][:10] if row['last_transaction'] else '-'
                })
            
            total_weight = sum(i['total_weight'] for i in items)
            total_amount = sum(i['total_amount'] for i in items)
            
            result = {
                'success': True,
                'report_type': 'seller',
                'period': f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}',
                'items': items,
                'total_weight': total_weight,
                'total_amount': total_amount,
                'transaction_count': sum(i['transaction_count'] for i in items),
                'avg_price': total_amount / total_weight if total_weight > 0 else 0
            }
        else:
            result = {'success': False, 'error': 'Invalid report type'}
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"Report error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ RUN ============
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)