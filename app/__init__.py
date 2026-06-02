from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import sqlite3
import uuid
import random
import os
from app.scale_reader import scale_reader, get_mock_weight

# Add this function for mock weight testing
def get_mock_weight():
    """Generate mock weight for testing without hardware"""
    return round(random.uniform(0.5, 100.0), 2)

# Then add your API routes (find where your routes are and add these)
@app.route('/api/get_weight')
def api_get_weight():
    """Get weight from specified scale"""
    scale_id = request.args.get('scale', 'scale_1')
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    
    # Use mock mode for testing without hardware
    if use_mock:
        weight = get_mock_weight()
        return jsonify({
            'success': True,
            'weight': weight,
            'scale': scale_id,
            'mock': True
        })
    
    # For now, since we don't have hardware, always use mock mode
    # When you have hardware, you'll uncomment the serial reading code
    weight = get_mock_weight()
    return jsonify({
        'success': True,
        'weight': weight,
        'scale': scale_id,
        'mock': True,
        'message': 'Using mock mode - Connect hardware for real readings'
    })
    
    # TODO: Uncomment this when you have physical scale hardware
    """
    # Read from actual hardware
    try:
        import serial
        import serial.tools.list_ports
        
        # Get COM port from config or use default
        port = app.config.get('SCALE_PORT', 'COM3')
        baudrate = app.config.get('SCALE_BAUDRATE', 9600)
        
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        line = ser.readline().decode('ascii', errors='ignore').strip()
        ser.close()
        
        import re
        match = re.search(r"(\d+\.?\d*)", line)
        if match:
            weight = float(match.group(1))
            return jsonify({
                'success': True,
                'weight': weight,
                'scale': scale_id,
                'mock': False
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Could not parse weight from: {line}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    """

@app.route('/api/get_all_weights')
def api_get_all_weights():
    """Get weights from all scales (for dashboard)"""
    # Return mock weights for all 4 scales
    weights = {
        'scale_1': {'weight': get_mock_weight(), 'name': 'Main Gate Scale'},
        'scale_2': {'weight': get_mock_weight(), 'name': 'Secondary Scale'},
        'scale_3': {'weight': get_mock_weight(), 'name': 'Processing Scale'},
        'scale_4': {'weight': get_mock_weight(), 'name': 'Weighbridge Scale'}
    }
    return jsonify({'success': True, 'scales': weights})

@app.route('/api/available_ports')
def api_available_ports():
    """Get available COM ports for debugging"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        port_list = [{'port': port.device, 'description': port.description} for port in ports]
        return jsonify({'ports': port_list})
    except:
        return jsonify({'ports': [], 'message': 'PySerial not installed or no ports found'})

# Try to import config, fallback to environment variables
try:
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
except ImportError:
    # Fallback configuration for production without config.py
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'scrapyard-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scrapyard.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SCALE_PORT'] = os.environ.get('SCALE_PORT', 'COM3')
    app.config['SCALE_BAUDRATE'] = int(os.environ.get('SCALE_BAUDRATE', 9600))
    app.config['SCALE_TIMEOUT'] = int(os.environ.get('SCALE_TIMEOUT', 1))

app.secret_key = app.config.get('SECRET_KEY', 'scrapyard-secret-key-2026')

# Database setup - Use /tmp for Render's ephemeral storage
def get_db():
    if os.environ.get('RENDER'):
        db_path = '/tmp/scrapyard.db'
    else:
        db_path = 'scrapyard.db'
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables with material codes
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            id_number TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    # Create scale_config table
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
    
    # Create scale_calibration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scale_calibration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scale_id TEXT NOT NULL,
            calibration_date DATE NOT NULL,
            next_calibration_date DATE,
            certified_by TEXT,
            certificate_number TEXT,
            notes TEXT
        )
    ''')
    
    # Insert default scales if empty
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
    
    # Insert sample materials if none exist
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0] == 0:
        materials = [
            ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
            ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
            ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
            ('ST1', 'Steel/Tin Cans', 2.20, 1.50, 'Food cans, tin containers'),
            ('PL1', 'Plastic PET', 4.50, 2.50, 'Clear plastic bottles'),
            ('CU1', 'Copper', 120.00, 90.00, 'Clean copper wire'),
            ('BR1', 'Brass', 65.00, 45.00, 'Brass fittings'),
            ('AL2', 'Aluminium Scrap', 18.00, 12.00, 'Mixed aluminium scrap'),
            ('ST2', 'Stainless Steel', 15.00, 10.00, '304/316 stainless steel'),
            ('PB1', 'Lead', 22.00, 15.00, 'Lead batteries and weights'),
            ('GL1', 'Glass', 0.60, 0.30, 'Clear and coloured glass'),
            ('PL2', 'Plastic HDPE', 3.80, 2.00, 'Milk bottles, detergent containers')
        ]
        cursor.executemany('''
            INSERT INTO materials (code, name, inbound_price, outbound_price, description)
            VALUES (?, ?, ?, ?, ?)
        ''', materials)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Scale reading function
def get_current_weight(scale_id='scale_1'):
    """Read weight from scale - returns float or None"""
    # For testing without hardware, return random weight
    # Replace with actual serial reading when hardware is connected
    return round(random.uniform(0.5, 50.0), 2)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    cursor.execute('''
        SELECT t.*, s.full_name as seller_name, s.id_number as seller_id_number, 
               m.name as material_name, m.code as material_code
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
        if trans.get('timestamp'):
            time_str = trans['timestamp'][11:16] if len(trans['timestamp']) > 16 else trans['timestamp']
            trans['time_display'] = time_str
        else:
            trans['time_display'] = ''
        today_transactions.append(trans)
    
    cursor.execute('''
        SELECT COALESCE(SUM(weight_kg), 0) as total_weight, COALESCE(SUM(amount), 0) as total_amount
        FROM transactions
        WHERE DATE(timestamp) = ?
    ''', (today,))
    totals = cursor.fetchone()
    
    conn.close()
    
    return render_template('index.html', 
                         today_transactions=today_transactions,
                         today_weight=totals['total_weight'] or 0,
                         today_amount=totals['total_amount'] or 0,
                         active_page='dashboard')

@app.route('/new_transaction', methods=['GET', 'POST'])
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
        
        # Get material price based on direction
        if direction == 'inbound':
            cursor.execute('SELECT code, inbound_price as price FROM materials WHERE id = ?', (material_id,))
        else:
            cursor.execute('SELECT code, outbound_price as price FROM materials WHERE id = ?', (material_id,))
        
        material = cursor.fetchone()
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
        
        ticket_number = f"{direction[:3].upper()}{uuid.uuid4().hex[:5].upper()}"
        reference_number = f"{direction[:1]}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO transactions (ticket_number, reference_number, seller_id, material_id, material_code, weight_kg, amount, scale_id, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_number, reference_number, seller_id, material_id, material['code'], weight, amount, scale_id, direction))
        
        conn.commit()
        conn.close()
        
        flash(f'✓ {direction.upper()} Transaction saved! Ticket: {ticket_number}', 'success')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT id, code, name, inbound_price, outbound_price FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    
    # Get scales from database
    cursor.execute('SELECT * FROM scale_config WHERE is_active = 1 ORDER BY display_order')
    db_scales = cursor.fetchall()
    
    scales = {}
    for scale in db_scales:
        scales[scale['scale_id']] = {
            'name': scale['name'],
            'location': scale['location'],
            'capacity_kg': scale['capacity_kg']
        }
    
    default_scale = session.get('default_scale', 'scale_1')
    conn.close()
    
    return render_template('new_transaction.html', 
                         materials=materials, 
                         scales=scales,
                         default_scale=default_scale,
                         active_page='new_transaction')

@app.route('/reports')
def reports():
    period = request.args.get('period', 'daily')
    now = datetime.now()
    
    if period == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'monthly':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'yearly':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.code, m.name, COALESCE(SUM(t.weight_kg), 0) as weight, COALESCE(SUM(t.amount), 0) as amount
        FROM materials m
        LEFT JOIN transactions t ON m.id = t.material_id AND t.timestamp >= ?
        WHERE m.is_active = 1
        GROUP BY m.id, m.code, m.name
        ORDER BY m.code
    ''', (start_date,))
    
    summary = cursor.fetchall()
    
    cursor.execute('SELECT COALESCE(SUM(weight_kg), 0) as total_weight, COALESCE(SUM(amount), 0) as total_amount FROM transactions WHERE timestamp >= ?', (start_date,))
    totals = cursor.fetchone()
    
    conn.close()
    
    return render_template('reports.html', 
                         summary=summary,
                         total_weight=totals['total_weight'] or 0,
                         total_amount=totals['total_amount'] or 0,
                         period=period,
                         active_page='reports')

@app.route('/sellers')
def sellers():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*,
               COUNT(t.id) as transaction_count,
               COALESCE(SUM(t.amount), 0) as total_earned,
               MIN(t.timestamp) as first_transaction
        FROM sellers s
        LEFT JOIN transactions t ON s.id = t.seller_id
        GROUP BY s.id
        ORDER BY s.full_name
    ''')
    
    sellers = cursor.fetchall()
    conn.close()
    
    return render_template('sellers.html', sellers=sellers, active_page='sellers')

@app.route('/materials')
def materials():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    
    return render_template('materials.html', materials=materials, active_page='materials')

# ============ SCALE MANAGEMENT ROUTES ============

@app.route('/scales')
def scales_dashboard():
    """Scale management dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM scale_config WHERE is_active = 1 ORDER BY display_order')
    db_scales = cursor.fetchall()
    
    scales = {}
    for scale in db_scales:
        scales[scale['scale_id']] = {
            'name': scale['name'],
            'location': scale['location'],
            'capacity_kg': scale['capacity_kg'],
            'icon': 'fa-balance-scale',
            'is_active': scale['is_active']
        }
    
    conn.close()
    
    return render_template('scales_dashboard.html', 
                         scales=scales,
                         active_page='scales')

@app.route('/api/get_weight')
def api_get_weight():
    """Get weight from specified scale or default"""
    scale_id = request.args.get('scale', 'scale_1')
    weight = get_current_weight(scale_id)
    
    if weight is not None:
        return jsonify({
            'success': True, 
            'weight': weight,
            'scale': scale_id
        })
    else:
        return jsonify({
            'success': False, 
            'error': f'Could not read from {scale_id} scale'
        }), 500

@app.route('/api/get_all_weights')
def api_get_all_weights():
    """Get weights from all scales"""
    results = {}
    scales = ['scale_1', 'scale_2', 'scale_3', 'scale_4']
    for scale_id in scales:
        weight = get_current_weight(scale_id)
        if weight:
            results[scale_id] = {'weight': weight}
    return jsonify({'success': True, 'scales': results})

@app.route('/api/set_default_scale', methods=['POST'])
def api_set_default_scale():
    """Set default scale for the current session"""
    data = request.json
    scale_id = data.get('scale_id')
    
    session['default_scale'] = scale_id
    
    return jsonify({
        'success': True,
        'scale_id': scale_id,
        'scale_name': f'Scale {scale_id}'
    })

@app.route('/api/get_default_scale')
def api_get_default_scale():
    """Get user's default scale"""
    default_scale = session.get('default_scale', 'scale_1')
    return jsonify({'default_scale': default_scale})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
