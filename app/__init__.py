from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.utils.logger import setup_logging
from app.config.config_manager import load_config
from app.api.routes import api_bp

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Загрузка конфигурации
    config = load_config()
    app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['url']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Настройка логирования
    setup_logging(config['logging'])
    
    # Регистрация blueprint'ов
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app