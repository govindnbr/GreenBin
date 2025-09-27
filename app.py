from flask import Flask
from flask_login import LoginManager
from models.models import db, User

# Import blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.api import api_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recycling_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create sample data if database is empty
        if User.query.count() == 0:
            create_sample_data()
    
    return app

def create_sample_data():
    """Create sample data for demonstration"""
    from werkzeug.security import generate_password_hash
    from models.models import TrashBin, QRCode, generate_qr_code
    
    # Create sample user
    user = User(
        username='demo_user',
        email='demo@example.com',
        password_hash=generate_password_hash('password123'),
        phone='+1234567890',
        total_points=150
    )
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        phone='+1234567891',
        total_points=0,
        is_admin=True
    )
    
    # Create sample trash bins
    bins = [
        TrashBin(bin_id='BIN001', location='Main Street Park', current_load=75),
        TrashBin(bin_id='BIN002', location='City Mall', current_load=45),
        TrashBin(bin_id='BIN003', location='University Campus', current_load=90),
        TrashBin(bin_id='BIN004', location='Shopping Center', current_load=30),
    ]
    
    db.session.add(user)
    db.session.add(admin)
    for bin in bins:
        db.session.add(bin)
    
    db.session.commit()
    
    # Create sample QR codes
    for bin in bins:
        for i in range(5):  # 5 QR codes per bin
            qr = QRCode(
                code=generate_qr_code(),
                trash_bin_id=bin.id,
                plastic_type='bottle',
                points_value=10
            )
            db.session.add(qr)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
