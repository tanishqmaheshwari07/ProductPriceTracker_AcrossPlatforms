from flask import Flask
import os

def create_app():
    # Calculate base directory (root of the project)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    # Configure SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'priceai.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from app.database.models import db
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Import routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
