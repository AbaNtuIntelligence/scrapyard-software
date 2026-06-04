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

    # Auto-populate materials if none exist
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0] == 0:
        print('📦 No materials found. Adding default materials...')
        materials = [
            ('K4', 'Cardboard', 1.50, 0.80, 'Corrugated cardboard boxes'),
            ('K5', 'Mixed Paper', 0.80, 0.40, 'Newspapers, magazines'),
            ('AL1', 'Aluminium Cans', 25.00, 18.00, 'Clean aluminium beverage cans'),
            ('CU1', 'Copper', 120.00, 90.00, 'Clean copper wire'),
            ('BR1', 'Brass', 65.00, 45.00, 'Brass fittings'),
            ('ST1', 'Steel', 2.20, 1.50, 'Steel scrap'),
        ]
        for m in materials:
            cursor.execute('''
                INSERT INTO materials (code, name, inbound_price, outbound_price, description, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', m)
        print(f'✅ Added {len(materials)} default materials')

    conn.commit()
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