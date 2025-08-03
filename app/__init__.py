from dotenv import load_dotenv
from flask import Flask
from app.extensions import db, mail, login_manager, migrate
from app.routes.auth import auth
from app.routes.web import web 
from app.routes import admin
from app.models import User, Event, Assignment
from app.email import send_email
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os, atexit

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.jinja_env.globals.update(enumerate=enumerate)

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

    # ✅ Scheduler: Daily reminder check
    def check_and_send_reminders():
        with app.app_context():
            today = datetime.utcnow().date()
            events = Event.query.all()

            for event in events:
                if not event.start_date:
                    continue

                days_until = (event.start_date - today).days
                if days_until in [14, 3]:
                    for assignment in event.assignments:
                        user = assignment.user
                        if user and user.email:
                            send_email(
                                to_email=user.email,
                                subject=f"📣 Reminder: Event in {days_until} day(s) - {event.name}",
                                template_name="event_reminder.html",
                                fullname=user.fullname,
                                event=event,
                                days_left=days_until
                            )

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_send_reminders, trigger="interval", days=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app
