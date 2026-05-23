from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
import os

login_manager = LoginManager()
mail = Mail()

def create_app():
    # Calculate base directory (root of the project)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    from config import Config
    app.config.from_object(Config)
    # Ensure SQLite uses absolute path under base_dir
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        db_name = app.config['SQLALCHEMY_DATABASE_URI'].split('sqlite:///')[-1]
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, db_name)
    
    from app.database.models import db, User
    db.init_app(app)
    
    # Init login and mail
    login_manager.init_app(app)
    login_manager.login_view = 'main.home'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    mail.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
    # Start Scheduler
    from app.tasks.scheduler import init_scheduler
    init_scheduler(app)
    
    # Import routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app

