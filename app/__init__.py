from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import sqlite3
import uuid
import random
import os

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
            price_per_kg REAL NOT NULL,
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers (id),
            FOREIGN KEY (material_id) REFERENCES materials (id)
        )
    ''')
    
    # Insert sample materials with codes if none exist
    cursor.execute('SELECT COUNT(*) FROM materials')
    if cursor.fetchone()[0] == 0:
        materials = [
            ('K4', 'Cardboard', 1.50, 'Corrugated cardboard boxes and sheets'),
            ('K5', 'Mixed Paper', 0.80, 'Newspapers, magazines, office paper'),
            ('AL1', 'Aluminium Cans', 25.00, 'Clean aluminium beverage cans'),
            ('ST1', 'Steel/Tin Cans', 2.20, 'Food cans, tin containers'),
            ('PL1', 'Plastic PET', 4.50, 'Clear plastic bottles (PET)'),
            ('PL2', 'Plastic HDPE', 3.80, 'Milk bottles, detergent containers'),
            ('GL1', 'Glass', 0.60, 'Clear and coloured glass bottles'),
            ('CU1', 'Copper', 120.00, 'Clean copper wire and pipe'),
            ('BR1', 'Brass', 65.00, 'Brass fittings and scrap'),
            ('AL2', 'Aluminium Scrap', 18.00, 'Mixed aluminium scrap'),
            ('ST2', 'Stainless Steel', 15.00, '304/316 stainless steel'),
            ('PB1', 'Lead', 22.00, 'Lead batteries and weights')
        ]
        cursor.executemany('INSERT INTO materials (code, name, price_per_kg, description) VALUES (?, ?, ?, ?)', materials)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Scale reading function
def get_current_weight():
    """Read weight from scale - returns float or None"""
    USE_MOCK_MODE = True
    
    if USE_MOCK_MODE:
        return round(random.uniform(0.5, 50.0), 2)
    
    return None

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
        weight = float(request.form['weight'])
        
        cursor.execute('SELECT code, price_per_kg FROM materials WHERE id = ?', (material_id,))
        material = cursor.fetchone()
        amount = weight * material['price_per_kg']
        
        cursor.execute('SELECT id FROM sellers WHERE id_number = ?', (id_number,))
        seller = cursor.fetchone()
        
        if seller:
            seller_id = seller['id']
        else:
            cursor.execute('INSERT INTO sellers (full_name, id_number, phone) VALUES (?, ?, ?)',
                         (seller_name, id_number, phone))
            seller_id = cursor.lastrowid
        
        ticket_number = str(uuid.uuid4())[:8].upper()
        cursor.execute('''
            INSERT INTO transactions (ticket_number, seller_id, material_id, material_code, weight_kg, amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticket_number, seller_id, material_id, material['code'], weight, amount))
        
        conn.commit()
        conn.close()
        
        flash(f'✓ Transaction saved! Ticket: {ticket_number} | {material["code"]}: {weight}kg @ R{material["price_per_kg"]}/kg', 'success')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT id, code, name, price_per_kg FROM materials WHERE is_active = 1 ORDER BY code')
    materials = cursor.fetchall()
    conn.close()
    
    return render_template('new_transaction.html', materials=materials, active_page='new_transaction')

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

@app.route('/api/get_weight')
def api_get_weight():
    try:
        weight = get_current_weight()
        if weight is not None:
            return jsonify({'success': True, 'weight': weight})
        else:
            return jsonify({'success': False, 'error': 'Could not read from scale'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
