from dotenv import load_dotenv
from flask import Flask
from app.extensions import db, mail, login_manager, migrate
from app.routes.auth import auth
from app.routes.web import web 
from app.routes import admin
from app.models import User
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(web)
    app.register_blueprint(admin.admin_bp)

    return app
