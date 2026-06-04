from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import uuid
import random
import os

# ============ CREATE APP INSTANCE ============
app = Flask(__name__)
app.secret_key = 'scrapyard-secret-key-2026'

# ============ CONFIGURATION ============
try:
    from config import Config
    app.config.from_object(Config)
except ImportError:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'scrapyard-secret-key-2026')
    app.config['SCALE_PORT'] = os.environ.get('SCALE_PORT', 'COM3')
    app.config['SCALE_BAUDRATE'] = int(os.environ.get('SCALE_BAUDRATE', 9600))

# ============ PERMISSION DECORATORS ============
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ HELPER FUNCTIONS ============
def get_mock_weight():
    return round(random.uniform(0.5, 100.0), 2)

def get_current_weight(scale_id='scale_1'):
    return round(random.uniform(0.5, 100.0), 2)

# ============ DATABASE FUNCTIONS ============
def get_db():
    # Use absolute path for clarity
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'scrapyard.db')
    
    # Override for Render
    if os.environ.get('RENDER'):
        db_path = '/tmp/scrapyard.db'
    
    print(f"Connecting to database at: {db_path}")  # Debug line
    
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
            reference_number TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers (id),
            FOREIGN KEY (material_id) REFERENCES materials (id)
        )
    ''')
    
    # Scale config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scale_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scale_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            capacity_kg INTEGER,
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            last_calibration DATE
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
            email TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default scales
    cursor.execute('SELECT COUNT(*) FROM scale_config')
    if cursor.fetchone()[0] == 0:
        scales = [
            ('scale_1', 'Main Gate Scale', 'Main Entrance', 5000, 1),
            ('scale_2', 'Secondary Scale', 'South Gate', 3000, 2),
            ('scale_3', 'Processing Scale', 'Sorting Area', 1000, 3),
            ('scale_4', 'Weighbridge Scale', 'Weighbridge', 20000, 4)
        ]
        cursor.executemany('''
            INSERT INTO scale_config (scale_id, name, location, capacity_kg, display_order)
            VALUES (?, ?, ?, ?, ?)
        ''', scales)
    
    # Insert default users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        users = [
            ('admin', 'admin123', 'admin', 'System Administrator', 'admin@scrapsoft.com'),
            ('operator', 'operator123', 'operator', 'Yard Operator', 'operator@scrapsoft.com')
        ]
        cursor.executemany('''
            INSERT INTO users (username, password, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        ''', users)
    
    # Auto-populate default materials if none exist
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0] == 0:
        print('📦 No materials found. Adding default materials...')
        default_materials = [
            ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
            ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
            ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
            ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
            ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
            ('AL3', 'Aluminium Wheels', 22.00, 15.00, 'Clean aluminium wheels'),
            ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
            ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
            ('CU3', 'Copper Wire', 120.00, 90.00, 'Insulated copper wire'),
            ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
            ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
            ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel'),
            ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
            ('PL2', 'HDPE Plastic', 3.80, 2.00, 'Milk bottles, detergent'),
            ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
            ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass'),
            ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
            ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
            ('CB1', 'Circuit Boards', 45.00, 30.00, 'Green circuit boards'),
            ('TR1', 'Car Tires', 2.00, 1.00, 'Passenger car tires'),
            ('EL1', 'Electric Motors', 12.00, 7.00, 'Copper wound motors'),
            ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
        ]
        for m in default_materials:
            try:
                cursor.execute('''
                    INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', m)
                print(f'  ✓ Added: {m[0]} - {m[1]}')
            except Exception as e:
                print(f'  ✗ Error adding {m[0]}: {e}')
        print(f'✅ Added {len(default_materials)} default materials')
    
    conn.commit()
    conn.close()
# ============ AUTHENTICATION ROUTES ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ? AND is_active = 1', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['is_admin'] = (user['role'] == 'admin')
            
            if session['is_admin']:
                flash('✓ Welcome Administrator! You have full CRUD access.', 'success')
            else:
                flash('✓ Welcome Operator! You have view-only access.', 'success')
            
            return redirect(url_for('dashboard'))
        else:
            flash('✗ Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('✓ You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ============ MAIN ROUTES ============
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute('''
        SELECT t.*, s.full_name as seller_name, m.name as material_name
        FROM transactions t
        JOIN sellers s ON t.seller_id = s.id
        JOIN materials m ON t.material_id = m.id
        WHERE DATE(t.timestamp) = ?
        ORDER BY t.timestamp DESC
    ''', (today,))
    rows = cursor.fetchall()
    today_transactions = []
    for row in rows:
        trans = dict(row)
        trans['time_display'] = trans.get('timestamp', '')[:16] if trans.get('timestamp') else ''
        today_transactions.append(trans)
    
    cursor.execute('SELECT COALESCE(SUM(weight_kg), 0), COALESCE(SUM(amount), 0) FROM transactions WHERE DATE(timestamp) = ?', (today,))
    totals = cursor.fetchone()
    conn.close()
    
    return render_template('index.html', 
                         today_transactions=today_transactions,
                         today_weight=totals[0],
                         today_amount=totals[1],
                         active_page='dashboard')

@app.route('/new_transaction', methods=['GET', 'POST'])
@login_required
def new_transaction():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        seller_name = request.form['seller_name']
        id_number = request.form['id_number']
        phone = request.form.get('phone', '')
        material_id = request.form['material_id']
        scale_id = request.form.get('scale_id', 'scale_1')
        direction = request.form.get('direction', 'inbound')
        weight = float(request.form['weight'])
        
        if direction == 'inbound':
            cursor.execute('SELECT code, inbound_price as price FROM materials WHERE id = ?', (material_id,))
        else:
            cursor.execute('SELECT code, outbound_price as price FROM materials WHERE id = ?', (material_id,))
        material = cursor.fetchone()
        amount = weight * material['price']
        
        cursor.execute('SELECT id FROM sellers WHERE id_number = ?', (id_number,))
        seller = cursor.fetchone()
        if seller:
            seller_id = seller['id']
        else:
            cursor.execute('INSERT INTO sellers (full_name, id_number, phone) VALUES (?, ?, ?)',
                         (seller_name, id_number, phone))
            seller_id = cursor.lastrowid
        
        ticket_number = f"{direction[:3].upper()}{uuid.uuid4().hex[:5].upper()}"
        cursor.execute('''
            INSERT INTO transactions (ticket_number, seller_id, material_id, material_code, weight_kg, amount, scale_id, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_number, seller_id, material_id, material['code'], weight, amount, scale_id, direction))
        conn.commit()
        conn.close()
        flash(f'Transaction saved! Ticket: {ticket_number}', 'success')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT id, code, name, inbound_price, outbound_price FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    cursor.execute('SELECT * FROM scale_config WHERE is_active = 1 ORDER BY display_order')
    db_scales = cursor.fetchall()
    scales = {s['scale_id']: {'name': s['name'], 'location': s['location'], 'capacity_kg': s['capacity_kg']} for s in db_scales}
    conn.close()
    return render_template('new_transaction.html', materials=materials, scales=scales, active_page='new_transaction')

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
        cursor.execute('SELECT * FROM sellers ORDER BY full_name')
        sellers = cursor.fetchall()
        conn.close()
        return render_template('sellers.html', sellers=sellers, active_page='sellers')
    except Exception as e:
        print(f"Error in sellers route: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading sellers: {str(e)}', 'danger')
        return render_template('sellers.html', sellers=[], active_page='sellers')

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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scale_config ORDER BY display_order')
    db_scales = cursor.fetchall()
    scales = {s['scale_id']: dict(s) for s in db_scales}
    conn.close()
    return render_template('scales_dashboard.html', scales=scales, active_page='scales')

# ============ API ROUTES ============
@app.route('/api/get_weight')
@login_required
def api_get_weight():
    scale_id = request.args.get('scale', 'scale_1')
    return jsonify({'success': True, 'weight': get_mock_weight(), 'scale': scale_id})

@app.route('/api/get_all_weights')
@login_required
def api_get_all_weights():
    results = {f'scale_{i}': {'weight': get_mock_weight()} for i in range(1, 5)}
    return jsonify({'success': True, 'scales': results})

@app.route('/api/update_scale_status', methods=['POST'])
@admin_required
def api_update_scale_status():
    """Update scale operational status (active/inactive)"""
    data = request.json
    scale_id = data.get('scale_id')
    is_operational = data.get('is_operational', False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Update the scale's operational status
    cursor.execute('UPDATE scale_config SET is_operational = ? WHERE scale_id = ?', 
                  (1 if is_operational else 0, scale_id))
    
    # If deactivating and this scale was active, clear active flag
    if not is_operational:
        cursor.execute('UPDATE scale_config SET is_active = 0 WHERE scale_id = ?', (scale_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'scale_id': scale_id, 'is_operational': is_operational})

@app.route('/api/set_active_scale', methods=['POST'])
@admin_required
def api_set_active_scale():
    """Set which scale is currently active for transactions"""
    data = request.json
    scale_id = data.get('scale_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if scale is operational
    cursor.execute('SELECT is_operational FROM scale_config WHERE scale_id = ?', (scale_id,))
    result = cursor.fetchone()
    
    if not result or not result['is_operational']:
        return jsonify({'success': False, 'error': 'Cannot activate non-operational scale'}), 400
    
    # Reset all scales to inactive, then set selected as active
    cursor.execute('UPDATE scale_config SET is_active = 0')
    cursor.execute('UPDATE scale_config SET is_active = 1 WHERE scale_id = ?', (scale_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'scale_id': scale_id})

@app.route('/api/get_scale_status', methods=['GET'])
@login_required
def api_get_scale_status():
    """Get status of all scales"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT scale_id, name, location, is_operational, is_active FROM scale_config')
    scales = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'scales': [dict(s) for s in scales]
    })

# ============ REPORT API ROUTE ============
@app.route('/api/reports/generate', methods=['GET'])
@login_required
def api_generate_report():
    try:
        report_type = request.args.get('report_type', 'inbound')
        date_range = request.args.get('date_range', 'month')
        start_date_str = request.args.get('start_date', '')
        end_date_str = request.args.get('end_date', '')
        
        # Admin check for outbound reports
        if report_type == 'outbound' and not session.get('is_admin', False):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        if date_range == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'yesterday':
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = end_date - timedelta(days=end_date.weekday())
        elif date_range == 'month':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'custom' and start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get report data
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
            ORDER BY total_weight DESC
        ''', (report_type, start_date, end_date))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'code': row['code'],
                'name': row['name'],
                'total_weight': row['total_weight'] or 0,
                'total_amount': row['total_amount'] or 0,
                'transaction_count': row['transaction_count'] or 0,
                'avg_price': row['avg_price'] or 0
            })
        
        conn.close()
        
        # Calculate totals
        total_weight = sum(i['total_weight'] for i in items)
        total_amount = sum(i['total_amount'] for i in items)
        transaction_count = sum(i['transaction_count'] for i in items)
        avg_price = total_amount / total_weight if total_weight > 0 else 0
        
        return jsonify({
            'success': True,
            'report_type': report_type,
            'period': f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}',
            'items': items,
            'total_weight': total_weight,
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'avg_price': avg_price
        })
        
    except Exception as e:
        print(f"Report error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

# ============ RUN APP ============
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

# ============ MATERIALS API ROUTES ============
@app.route('/api/materials', methods=['GET'])
@login_required
def api_get_materials():
    """Get all materials as JSON"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    return jsonify([dict(m) for m in materials])

@app.route('/api/materials', methods=['POST'])
@admin_required
def api_create_material():
    """Create a new material"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (data['code'], data['name'], data['inbound_price'], data['outbound_price'], data.get('description', '')))
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Material code or name already exists'}), 400
    finally:
        conn.close()

@app.route('/api/materials/<int:material_id>', methods=['PUT'])
@admin_required
def api_update_material(material_id):
    """Update an existing material"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE materials 
            SET code = ?, name = ?, inbound_price = ?, outbound_price = ?, description = ?
            WHERE id = ?
        ''', (data['code'], data['name'], data['inbound_price'], data['outbound_price'], data.get('description', ''), material_id))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Material code or name already exists'}), 400
    finally:
        conn.close()

@app.route('/api/materials/<int:material_id>', methods=['DELETE'])
@admin_required
def api_delete_material(material_id):
    """Delete a material (soft delete)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE materials SET is_active = 0 WHERE id = ?', (material_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

print('✅ Materials API routes registered')
    
    # Auto-populate default materials if none exist
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0] == 0:
        print('📦 No materials found. Adding default materials...')
        default_materials = [
            ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
            ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines, office paper'),
            ('K6', 'White Office Paper', 1.20, 0.60, 'Clean white printer paper'),
            ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
            ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
            ('CU1', 'Copper Bright', 140.00, 110.00, 'Clean bright copper wire'),
            ('CU2', 'Copper #1', 130.00, 100.00, 'Clean copper pipe'),
            ('BR1', 'Yellow Brass', 65.00, 45.00, 'Clean yellow brass fittings'),
            ('ST1', 'Steel Cans', 2.20, 1.50, 'Food cans, tin containers'),
            ('ST2', 'Stainless Steel', 15.00, 10.00, '304 stainless steel scrap'),
            ('PL1', 'PET Plastic', 4.50, 2.50, 'Clear plastic bottles'),
            ('PL2', 'HDPE Plastic', 3.80, 2.00, 'Milk bottles, detergent'),
            ('GL1', 'Clear Glass', 0.60, 0.30, 'Clear glass bottles'),
            ('GL2', 'Brown Glass', 0.50, 0.25, 'Brown/amber glass'),
            ('PB1', 'Lead', 22.00, 15.00, 'Lead sheeting, weights'),
            ('BT1', 'Li-Ion Batteries', 30.00, 20.00, 'Lithium-ion batteries'),
            ('CB1', 'Circuit Boards', 45.00, 30.00, 'Green circuit boards'),
            ('TR1', 'Car Tires', 2.00, 1.00, 'Passenger car tires'),
            ('EL1', 'Electric Motors', 12.00, 7.00, 'Copper wound motors'),
            ('CAT1', 'Catalytic Converters', 250.00, 150.00, 'Catalytic converters'),
        ]
        for m in default_materials:
            try:
                cursor.execute('''
                    INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', m)
                print(f'  ✓ Added: {m[0]} - {m[1]}')
            except Exception as e:
                print(f'  ✗ Error adding {m[0]}: {e}')
        print(f'✅ Added {len(default_materials)} default materials')
