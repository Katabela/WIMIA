from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models import Event, User, Assignment, db
from app.utils import admin_required
from app.email import send_email
from datetime import datetime
import os
import secrets

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def parse_datetime(value):
    return datetime.fromisoformat(value) if value else None

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    events = Event.query.all()
    users = User.query.all()
    return render_template("admin/dashboard.html", events=events, users=users)


@admin_bp.route("/event/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_event():
    if request.method == "POST":
        event = Event(
            name=request.form["name"],
            location=request.form["location"],
            start_date=request.form["start_date"],
            end_date=request.form["end_date"],
            flight_departure_datetime=parse_datetime(request.form.get("flight_departure_datetime")),
            flight_return_datetime=parse_datetime(request.form.get("flight_return_datetime")),
            flight_airline=request.form.get("flight_airline"),
            flight_bag_info=request.form.get("flight_bag_info"),
            flight_confirmation_code=request.form.get("flight_confirmation_code"),
            accommodation_name=request.form.get("accommodation_name"),
            accommodation_address=request.form.get("accommodation_address"),
            accommodation_airbnb_link=request.form.get("accommodation_airbnb_link") or None,
            style=request.form["style"],
            cheer_level=request.form["cheer_level"],
            team_info=request.form["team_info"],
            created_by=current_user.id,
        )
        db.session.add(event)
        db.session.commit()

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
        event.name = request.form.get("name")
        event.location = request.form.get("location")
        event.start_date = request.form.get("start_date")
        event.end_date = request.form.get("end_date")
        event.flight_departure_datetime = parse_datetime(request.form.get("flight_departure_datetime"))
        event.flight_return_datetime = parse_datetime(request.form.get("flight_return_datetime"))
        event.flight_airline = request.form.get("flight_airline")
        event.flight_bag_info = request.form.get("flight_bag_info")
        event.flight_confirmation_code = request.form.get("flight_confirmation_code")
        event.accommodation_name = request.form.get("accommodation_name")
        event.accommodation_address = request.form.get("accommodation_address")
        event.accommodation_airbnb_link=request.form.get("accommodation_airbnb_link") or None
        event.style = request.form.get("style")
        event.cheer_level = request.form.get("cheer_level")
        event.team_info = request.form.get("team_info")

        selected_user_ids = {int(uid) for uid in request.form.getlist("assigned_users")}
        existing_assignments = {a.user_id for a in event.assignments}

        # Remove unselected users
        for assignment in event.assignments[:]:
            if assignment.user_id not in selected_user_ids:
                db.session.delete(assignment)

        # Add new users
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

        # Notify all assigned users of updates
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
