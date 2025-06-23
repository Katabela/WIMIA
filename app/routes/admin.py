from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Event, User
from app.extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return redirect(url_for("web.index"))

    events = Event.query.order_by(Event.start_date.desc()).all()
    users = User.query.all()
    return render_template("admin/dashboard.html", events=events, users=users)

@admin_bp.route("/events/add")
@login_required
def add_event():
    if current_user.role != "admin":
        return redirect(url_for("web.index"))
    # render form to add event
    return "Add Event Page"

@admin_bp.route("/events/<int:event_id>/edit")
@login_required
def edit_event(event_id):
    if current_user.role != "admin":
        return redirect(url_for("web.index"))
    return f"Edit Event {event_id}"

@admin_bp.route("/events/<int:event_id>/delete")
@login_required
def delete_event(event_id):
    if current_user.role != "admin":
        return redirect(url_for("web.index"))
    # handle deletion
    return f"Deleted Event {event_id}"

@admin_bp.route("/assign")
@login_required
def assign_user():
    if current_user.role != "admin":
        return redirect(url_for("web.index"))
    return "Assign User to Event Page"

