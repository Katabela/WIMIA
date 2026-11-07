from flask import Blueprint, current_app, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models import Event, User, Assignment, EventDay, FlightInfo, db
from app.utils import admin_required
from app.email import send_email
from datetime import datetime
import os
import secrets
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_schedule_file(file):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    safe_name = secure_filename(file.filename)
    extension = safe_name.rsplit('.', 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, stored_name))
    return stored_name

def parse_datetime(value):
    return datetime.fromisoformat(value) if value else None

def parse_event_days(form):
    starts = form.getlist("event_start_times")
    ends = form.getlist("event_end_times")
    if not starts or len(starts) != len(ends):
        raise ValueError("Add at least one complete event day.")

    days = []
    for start_value, end_value in zip(starts, ends):
        start = parse_datetime(start_value)
        end = parse_datetime(end_value)
        if not start or not end:
            raise ValueError("Every event day needs a start and end time.")
        if end <= start:
            raise ValueError("Each event day must end after it starts.")
        days.append((start, end))
    return days

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    subquery = (
        db.session.query(
            EventDay.event_id,
            db.func.min(EventDay.start_datetime).label("first_day")
        )
        .group_by(EventDay.event_id)
        .subquery()
    )

    events = (
        db.session.query(Event)
        .join(subquery, Event.id == subquery.c.event_id)
        .order_by(subquery.c.first_day)
        .all()
    )

    users = User.query.all()
    return render_template("admin/dashboard.html", events=events, users=users)


@admin_bp.route("/event/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_event():
    if request.method == "POST":
        try:
            event_days = parse_event_days(request.form)
        except ValueError as error:
            flash(str(error), "danger")
            return render_template(
                "admin/add_event.html",
                users=User.query.filter_by(role="employee").all(),
            ), 400

        event = Event(
            name=request.form["name"],
            location=request.form["location"],
            alternate_travel=request.form.get("alternate_travel"),
            rental_car_info=request.form.get("rental_car_info"),
            coach_name=request.form.get("coach_name"),
            coach_email=request.form.get("coach_email"),
            coach_phone=request.form.get("coach_phone"),
            accommodation_name=request.form.get("accommodation_name"),
            accommodation_address=request.form.get("accommodation_address"),
            accommodation_airbnb_link=request.form.get("accommodation_airbnb_link") or None,
            style=request.form["style"],
            cheer_level=request.form["cheer_level"],
            team_info=request.form["team_info"],
            created_by=current_user.id,
        )


        file = request.files.get("schedule_file")
        stored_name = save_schedule_file(file)
        if stored_name:
            event.schedule_file = stored_name

        db.session.add(event)
        db.session.flush()

        for i, (start_dt, end_dt) in enumerate(event_days, start=1):
            db.session.add(EventDay(
                event_id=event.id,
                day_number=i,
                start_datetime=start_dt,
                end_datetime=end_dt
            ))

        selected_user_ids = request.form.getlist("assigned_users")
        for user_id in selected_user_ids:
            user = User.query.get(int(user_id))
            if user and not Assignment.query.filter_by(event_id=event.id, user_id=user.id).first():
                db.session.add(Assignment(event_id=event.id, user_id=user.id))
                send_email(
                    to_email=user.email,
                    subject=f"You've been assigned to: {event.name}",
                    template_name="event_assignment_email.html",
                    fullname=user.fullname,
                    event=event,
                    domain_url=os.environ.get("DOMAIN_URL")
                )

        new_invite_email = request.form.get("new_invite_email")
        if new_invite_email:
            user = User.query.filter_by(email=new_invite_email).first()
            if not user:
                temp_password = secrets.token_urlsafe(8)
                user = User(
                    fullname="Invited Coach",
                    email=new_invite_email,
                    role="employee"
                )
                user.set_password(temp_password)
                db.session.add(user)
                db.session.flush()

                send_email(
                    to_email=new_invite_email,
                    subject="You've been invited to WIMIA",
                    template_name="invite_email.html",
                    fullname="Invited Coach",
                    temp_password=temp_password,
                    domain_url=os.environ.get("DOMAIN_URL")
                )

            if not Assignment.query.filter_by(event_id=event.id, user_id=user.id).first():
                db.session.add(Assignment(event_id=event.id, user_id=user.id))
                send_email(
                    to_email=user.email,
                    subject=f"You've been assigned to: {event.name}",
                    template_name="event_assignment_email.html",
                    fullname=user.fullname,
                    event=event,
                    domain_url=os.environ.get("DOMAIN_URL"),
                    temp_password=temp_password if 'temp_password' in locals() else None
                )

            # Save flight info entries
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
                    flight_departure_datetime=parse_datetime(flight_departures[i]),
                    flight_return_datetime=parse_datetime(flight_returns[i]),
                    flight_airline=flight_airlines[i],
                    flight_bag_info=flight_bags[i],
                    flight_confirmation_code=flight_codes[i]
                ))

        db.session.commit()
        flash("Event created successfully and notifications sent!", "success")
        return redirect(url_for("admin.dashboard"))

    users = User.query.filter_by(role="employee").all()
    return render_template("admin/add_event.html", users=users)


@admin_bp.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    users = User.query.filter_by(role="employee").all()

    if request.method == "POST":
        try:
            event_days = parse_event_days(request.form)
        except ValueError as error:
            flash(str(error), "danger")
            return render_template(
                "admin/edit_event.html",
                event=event,
                users=users,
            ), 400

        event.name = request.form.get("name")
        event.location = request.form.get("location")
        event.alternate_travel = request.form.get("alternate_travel")
        event.rental_car_info = request.form.get("rental_car_info")
        event.coach_name = request.form.get("coach_name")
        event.coach_email = request.form.get("coach_email")
        event.coach_phone = request.form.get("coach_phone")
        event.accommodation_name = request.form.get("accommodation_name")
        event.accommodation_address = request.form.get("accommodation_address")
        event.accommodation_airbnb_link = request.form.get("accommodation_airbnb_link") or None
        event.style = request.form.get("style")
        event.cheer_level = request.form.get("cheer_level")
        event.team_info = request.form.get("team_info")


        file = request.files.get("schedule_file")
        stored_name = save_schedule_file(file)
        if stored_name:
            event.schedule_file = stored_name

        for day in event.event_days:
            db.session.delete(day)

        for i, (start_dt, end_dt) in enumerate(event_days, start=1):
            db.session.add(EventDay(
                event_id=event.id,
                day_number=i,
                start_datetime=start_dt,
                end_datetime=end_dt
            ))

        selected_user_ids = {int(uid) for uid in request.form.getlist("assigned_users")}
        existing_assignments = {a.user_id for a in event.assignments}

        for assignment in event.assignments[:]:
            if assignment.user_id not in selected_user_ids:
                db.session.delete(assignment)

        for uid in selected_user_ids - existing_assignments:
            user = User.query.get(uid)
            db.session.add(Assignment(event_id=event.id, user_id=uid))
            send_email(
                to_email=user.email,
                subject=f"You've been assigned to: {event.name}",
                template_name="event_assignment_email.html",
                fullname=user.fullname,
                event=event,
                domain_url=os.environ.get("DOMAIN_URL")
            )

        for assignment in event.assignments:
            user = assignment.user
            send_email(
                to_email=user.email,
                subject=f"Event updated: {event.name}",
                template_name="event_update_email.html",
                fullname=user.fullname,
                event=event,
                domain_url=os.environ.get("DOMAIN_URL")
            )

            # Replace flight info
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
                    flight_departure_datetime=parse_datetime(flight_departures[i]),
                    flight_return_datetime=parse_datetime(flight_returns[i]),
                    flight_airline=flight_airlines[i],
                    flight_bag_info=flight_bags[i],
                    flight_confirmation_code=flight_codes[i]
                ))


        db.session.commit()
        flash("Event updated and notifications sent!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/edit_event.html", event=event, users=users)


@admin_bp.route("/event/<int:event_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/event/<int:event_id>/assign", methods=["GET", "POST"])
@login_required
@admin_required
def assign_user(event_id):
    event = Event.query.get_or_404(event_id)
    users = User.query.all()
    if request.method == "POST":
        user_id = int(request.form["user_id"])
        existing = Assignment.query.filter_by(event_id=event.id, user_id=user_id).first()
        if existing:
            flash("User already assigned to this event.", "warning")
        else:
            db.session.add(Assignment(event_id=event.id, user_id=user_id))
            db.session.commit()
            flash("User assigned to event.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/assign_user.html", event=event, users=users)

@admin_bp.route("/send-signup-link", methods=["GET", "POST"])
@login_required
@admin_required
def send_signup_link():
    if request.method == "POST":
        email = request.form.get("email")
        if email:
            user = User.query.filter_by(email=email).first()
            if not user:
                temp_password = secrets.token_urlsafe(8)
                user = User(
                    fullname="Invited Coach",
                    email=email,
                    role="employee"
                )
                user.set_password(temp_password)
                db.session.add(user)
                db.session.flush()

                send_email(
                    to_email=email,
                    subject="You've been invited to WIMIA",
                    template_name="invite_email.html",
                    fullname="Invited Coach",
                    temp_password=temp_password,
                    domain_url=os.environ.get("DOMAIN_URL")
                )

                db.session.commit()
                flash("Sign-up link sent successfully!", "success")
            else:
                flash("User already exists.", "warning")
        else:
            flash("Please enter an email address.", "danger")

    return render_template("admin/send_signup_link.html")
