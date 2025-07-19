from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Event, Assignment  # Required for querying events

web = Blueprint("main", __name__)

@web.route("/")
def index():
    return render_template("index.html", user=current_user)

@web.route("/dashboard")
@login_required
def dashboard():
    # Show assigned events for employee users
    if current_user.role == "employee":
        assigned_event_ids = [a.event_id for a in current_user.assignments]
        events = Event.query.filter(Event.id.in_(assigned_event_ids)).all()
    elif current_user.role == "admin":
        # Show all events to admin
        events = Event.query.order_by(Event.start_date).all()
    else:
        events = []  # Or redirect for admin if needed

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

    # Ensure the current user is assigned to the event (unless admin)
    if current_user.role != "admin" and current_user.id not in [a.user_id for a in event.assignments]:
        abort(403)

    return render_template("event_detail.html", event=event)
