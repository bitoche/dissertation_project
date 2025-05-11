from flask import Flask
from flasgger import Swagger
from app.utils.logger import setup_logging
from app.config.config_manager import load_config
from app.api.routes import api_bp

def create_app():
    app = Flask(__name__)
    
    # Загрузка конфигурации
    config = load_config()
    
    # Настройка логирования
    setup_logging(config['logging'])
    
    # Инициализация Swagger
    app.config['SWAGGER'] = {
        'title': 'IFRS17 Calculator API',
        'uiversion': 3
    }
    Swagger(app)
    
    # Регистрация blueprint'ов
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app