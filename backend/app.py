from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db, User, Category
import os

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freezer_inventory.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')

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

    # Initialize database and create default data
    with app.app_context():
        db.create_all()

        # Create default admin user if none exists
        if not User.query.filter_by(role='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            print("Created default admin user (username: admin, password: admin123)")

        # Create default categories if none exist
        if not Category.query.first():
            default_categories = [
                {'name': 'Beef', 'days': 180, 'system': True},
                {'name': 'Pork', 'days': 180, 'system': True},
                {'name': 'Chicken', 'days': 270, 'system': True},
                {'name': 'Fish', 'days': 180, 'system': True},
                {'name': 'Ice Cream', 'days': 90, 'system': True},
                {'name': 'Appetizers', 'days': 180, 'system': True},
                {'name': 'Entrees', 'days': 180, 'system': True},
                {'name': 'Prepared Meals', 'days': 90, 'system': True},
                {'name': 'Staples', 'days': 365, 'system': True},
            ]

            for cat_data in default_categories:
                category = Category(
                    name=cat_data['name'],
                    default_expiration_days=cat_data['days'],
                    is_system=cat_data['system']
                )
                db.session.add(category)

            print(f"Created {len(default_categories)} default categories")

        db.session.commit()

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*50)
    print("Freezer Inventory Tracker API")
    print("="*50)
    print("Server running on http://localhost:5000")
    print("Default admin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  ⚠️  CHANGE THESE IN PRODUCTION!")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
