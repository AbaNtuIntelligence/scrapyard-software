from flask_login import UserMixin
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    id_number = db.Column(db.String(20), unique=True)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "Cardboard", "Aluminium Cans"
    price_per_kg = db.Column(db.Float, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ticket_number = db.Column(db.String(20), unique=True)
    
    seller = db.relationship('Seller', backref='transactions')
    material = db.relationship('Material', backref='transactions')