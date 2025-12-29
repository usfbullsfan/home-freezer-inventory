from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db, User, Category, Setting
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)

    # Configuration
    if test_config is None:
        # Production configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freezer_inventory.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    else:
        # Test configuration
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    JWTManager(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.items import items_bp
    from routes.categories import categories_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(items_bp, url_prefix='/api/items')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'}), 200

    # Initialize database and create default data (skip in test mode)
    if not app.config.get('TESTING', False):
        with app.app_context():
            try:
                # Print database location for debugging
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                abs_db_path = os.path.abspath(db_path)
                print(f"Database will be created at: {abs_db_path}")

                db.create_all()
                print("Database tables created successfully")
            except Exception as e:
                print(f"ERROR creating database: {e}")
                import traceback
                traceback.print_exc()

            # Create default admin user if none exists
            if not User.query.filter_by(role='admin').first():
                admin = User(username='admin', role='admin')
                admin.set_password('admin123')  # Change this in production!
                db.session.add(admin)
                print("Created default admin user (username: admin, password: admin123)")

            # Create default categories if none exist
            # Based on USDA/FDA freezer storage guidelines for food quality
            # Note: Food stored at 0°F is safe indefinitely; these dates are for quality only
            if not Category.query.first():
                default_categories = [
                    # Beef - USDA recommends 12 months for steaks/roasts, 3-4 months for ground
                    {'name': 'Beef, Steak', 'days': 365, 'system': True},
                    {'name': 'Beef, Roast', 'days': 365, 'system': True},
                    {'name': 'Beef, Ground', 'days': 120, 'system': True},
                    # Pork - USDA recommends 4-6 months for roasts/chops, 3-4 months for ground
                    {'name': 'Pork, Roast', 'days': 180, 'system': True},
                    {'name': 'Pork, Chops', 'days': 180, 'system': True},
                    {'name': 'Pork, Ground', 'days': 120, 'system': True},
                    # Poultry - USDA recommends 9 months for parts, 3-4 months for ground
                    {'name': 'Chicken', 'days': 270, 'system': True},
                    {'name': 'Turkey', 'days': 270, 'system': True},
                    {'name': 'Chicken, Ground', 'days': 120, 'system': True},
                    {'name': 'Turkey, Ground', 'days': 120, 'system': True},
                    # Other proteins
                    {'name': 'Fish', 'days': 180, 'system': True},
                    # Produce - USDA recommends 8-12 months for blanched vegetables and frozen fruits
                    {'name': 'Vegetables', 'days': 300, 'system': True},
                    {'name': 'Fruits', 'days': 300, 'system': True},
                    # Frozen prepared foods - USDA recommends 3-4 months for frozen dinners/entrees
                    {'name': 'Ice Cream', 'days': 60, 'system': True},
                    {'name': 'Appetizers', 'days': 90, 'system': True},
                    {'name': 'Entrees', 'days': 90, 'system': True},
                    {'name': 'Leftovers', 'days': 90, 'system': True},
                    {'name': 'Staples', 'days': 90, 'system': True},
                ]

                for cat_data in default_categories:
                    category = Category(
                        name=cat_data['name'],
                        default_expiration_days=cat_data['days'],
                        is_system=cat_data['system']
                    )
                    db.session.add(category)

                print(f"Created {len(default_categories)} default categories")

            # Create system-wide settings if they don't exist
            # System settings use user_id = None
            enable_images_setting = Setting.query.filter_by(
                user_id=None,
                setting_name='enable_image_fetching'
            ).first()

            if not enable_images_setting:
                enable_images_setting = Setting(
                    user_id=None,
                    setting_name='enable_image_fetching',
                    setting_value='true'
                )
                db.session.add(enable_images_setting)
                print("Created system setting: enable_image_fetching = true")

            db.session.commit()

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*50)
    print("Freezer Inventory Tracker API")
    print("="*50)
    print("Server running on http://localhost:5001")
    print("Default admin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  ⚠️  CHANGE THESE IN PRODUCTION!")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
