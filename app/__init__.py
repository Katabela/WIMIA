from dotenv import load_dotenv
from flask import Flask
from app.extensions import csrf, db, mail, login_manager, migrate
from app.routes.auth import auth
from app.routes.web import web 
from app.routes import admin
from app.models import User

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be configured")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL or DATABASE_URI must be configured")
    app.jinja_env.globals.update(enumerate=enumerate)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    migrate.init_app(app, db)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(web)
    app.register_blueprint(admin.admin_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
