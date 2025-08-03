from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Event, Assignment, EventDay, User, FlightInfo
from datetime import datetime
import os
from werkzeug.utils import secure_filename

web = Blueprint("main", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@web.route("/")
def index():
    return render_template("index.html", user=current_user)

@web.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "employee":
        assigned_event_ids = [a.event_id for a in current_user.assignments]
        subquery = (
            db.session.query(EventDay.event_id, db.func.min(EventDay.start_datetime).label("first_day"))
            .group_by(EventDay.event_id)
            .subquery()
        )
        events = (
            db.session.query(Event)
            .join(subquery, Event.id == subquery.c.event_id)
            .filter(Event.id.in_(assigned_event_ids))
            .order_by(subquery.c.first_day)
            .all()
        )
    elif current_user.role == "admin":
        subquery = (
            db.session.query(EventDay.event_id, db.func.min(EventDay.start_datetime).label("first_day"))
            .group_by(EventDay.event_id)
            .subquery()
        )
        events = (
            db.session.query(Event)
            .join(subquery, Event.id == subquery.c.event_id)
            .order_by(subquery.c.first_day)
            .all()
        )
    else:
        events = []

    return render_template("dashboard.html", user=current_user, events=events)

@web.route("/settings", methods=["GET"])
@login_required
def settings():
    return render_template("settings.html", user=current_user)

@web.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    current_user.fullname = request.form.get("fullname", current_user.fullname)
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("main.settings"))

@web.route("/event/<int:event_id>")
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.role != "admin" and current_user.id not in [a.user_id for a in event.assignments]:
        abort(403)
    return render_template("event_detail.html", event=event)

@web.route("/event/new", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "POST":
        event = Event(
            name=request.form["name"],
            location=request.form["location"],
            alternate_travel=request.form.get("alternate_travel"),
            rental_car_info=request.form.get("rental_car_info"),
            coach_name=request.form.get("coach_name"),
            coach_email=request.form.get("coach_email"),
            coach_phone=request.form.get("coach_phone"),
            style=request.form.get("style"),
            cheer_level=request.form.get("cheer_level"),
            team_info=request.form.get("team_info"),
            created_by=current_user.id
        )

        file = request.files.get("schedule_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            event.schedule_file = filename

        db.session.add(event)
        db.session.commit()

        start_times = request.form.getlist("event_start_times")
        end_times = request.form.getlist("event_end_times")
        for i, (start_str, end_str) in enumerate(zip(start_times, end_times), start=1):
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            db.session.add(EventDay(event_id=event.id, day_number=i, start_datetime=start_dt, end_datetime=end_dt))

        # Assign coaches
        assigned_user_ids = request.form.getlist("assigned_users")
        for uid in assigned_user_ids:
            db.session.add(Assignment(user_id=int(uid), event_id=event.id))

        # Save flight info entries (if any)
        flight_emails = request.form.getlist("flight_email")
        flight_names = request.form.getlist("flight_name")
        flight_departures = request.form.getlist("flight_departure_datetime")
        flight_returns = request.form.getlist("flight_return_datetime")
        flight_airlines = request.form.getlist("flight_airline")
        flight_bags = request.form.getlist("flight_bag_info")
        flight_codes = request.form.getlist("flight_confirmation_code")

        for i in range(len(flight_emails)):
            if flight_emails[i]:  # Avoid blank entries
                db.session.add(FlightInfo(
                    event_id=event.id,
                    email=flight_emails[i],
                    name=flight_names[i],
                    flight_departure_datetime=datetime.fromisoformat(flight_departures[i]) if flight_departures[i] else None,
                    flight_return_datetime=datetime.fromisoformat(flight_returns[i]) if flight_returns[i] else None,
                    flight_airline=flight_airlines[i],
                    flight_bag_info=flight_bags[i],
                    flight_confirmation_code=flight_codes[i]
                ))


        db.session.commit()
        flash("Event created successfully!")
        return redirect(url_for("main.dashboard"))

    return render_template("event_form.html", event=None, users=User.query.all())

@web.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == "POST":
        event.name = request.form["name"]
        event.location = request.form["location"]
        event.alternate_travel = request.form.get("alternate_travel")
        event.rental_car_info = request.form.get("rental_car_info")
        event.coach_name = request.form.get("coach_name")
        event.coach_email = request.form.get("coach_email")
        event.coach_phone = request.form.get("coach_phone")
        event.style = request.form.get("style")
        event.cheer_level = request.form.get("cheer_level")
        event.team_info = request.form.get("team_info")

        file = request.files.get("schedule_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            event.schedule_file = filename

        # Delete and replace EventDays
        EventDay.query.filter_by(event_id=event.id).delete()
        start_times = request.form.getlist("event_start_times")
        end_times = request.form.getlist("event_end_times")
        for i, (start_str, end_str) in enumerate(zip(start_times, end_times), start=1):
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            db.session.add(EventDay(event_id=event.id, day_number=i, start_datetime=start_dt, end_datetime=end_dt))

        # Update assignments
        Assignment.query.filter_by(event_id=event.id).delete()
        assigned_user_ids = request.form.getlist("assigned_users")
        for uid in assigned_user_ids:
            db.session.add(Assignment(user_id=int(uid), event_id=event.id))
        
        # Delete and replace FlightInfo entries
        FlightInfo.query.filter_by(event_id=event.id).delete()

        flight_emails = request.form.getlist("flight_email")
        flight_names = request.form.getlist("flight_name")
        flight_departures = request.form.getlist("flight_departure_datetime")
        flight_returns = request.form.getlist("flight_return_datetime")
        flight_airlines = request.form.getlist("flight_airline")
        flight_bags = request.form.getlist("flight_bag_info")
        flight_codes = request.form.getlist("flight_confirmation_code")

        for i in range(len(flight_emails)):
            if flight_emails[i]:
                db.session.add(FlightInfo(
                    event_id=event.id,
                    email=flight_emails[i],
                    name=flight_names[i],
                    flight_departure_datetime=datetime.fromisoformat(flight_departures[i]) if flight_departures[i] else None,
                    flight_return_datetime=datetime.fromisoformat(flight_returns[i]) if flight_returns[i] else None,
                    flight_airline=flight_airlines[i],
                    flight_bag_info=flight_bags[i],
                    flight_confirmation_code=flight_codes[i]
                ))


        db.session.commit()
        flash("Event updated successfully!")
        return redirect(url_for("main.dashboard"))

    return render_template("event_form.html", event=event, users=User.query.all())

@web.route("/privacy")
def privacy():
    return render_template("privacy.html")
