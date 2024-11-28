import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv  # Импортируем dotenv

# Загружаем переменные окружения из .env
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '../templates')
    )
    # Используем значения из .env
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Второй аргумент - значение по умолчанию
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User  # Импортируем здесь, чтобы избежать циклического импорта
    return User.query.get(int(user_id))