from app import create_app, db
from app.models import User, Material

app = create_app()
with app.app_context():
    # Create admin user (username: admin, password: admin123)
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', full_name='Yard Manager', is_admin=True)
        db.session.add(admin)
    
    # Add material types
    materials = [
        ('Cardboard', 1.50),
        ('Mixed Paper', 0.80),
        ('Aluminium Cans', 12.00),
        ('Steel/Tin Cans', 2.20),
        ('Plastic (PET)', 4.50),
        ('Glass', 0.60),
    ]
    for name, price in materials:
        if not Material.query.filter_by(name=name).first():
            db.session.add(Material(name=name, price_per_kg=price))
    
    db.session.commit()
    print("Database seeded with default user and materials.")