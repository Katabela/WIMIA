from flask import Flask
from app.extensions import db, mail, login_manager
from app.routes.auth import auth
from app.routes.web import web 
from app.models import Users
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(web)

    return app
