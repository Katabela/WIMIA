from flask import Blueprint, current_app, render_template, redirect, send_from_directory, url_for, request, flash, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Assignment, Event, EventDay

web = Blueprint("main", __name__)

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
    if current_user.role != "admin" and not Assignment.query.filter_by(
        event_id=event.id,
        user_id=current_user.id,
    ).first():
        abort(403)
    return render_template("event_detail.html", event=event)

@web.get("/event/<int:event_id>/schedule")
@login_required
def event_schedule(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.role != "admin" and not Assignment.query.filter_by(
        event_id=event.id,
        user_id=current_user.id,
    ).first():
        abort(403)
    if not event.schedule_file:
        abort(404)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        event.schedule_file,
        as_attachment=True,
    )

@web.get("/event/new")
@login_required
def add_event():
    if current_user.role != "admin":
        abort(403)
    return redirect(url_for("admin.add_event"), code=308)

@web.get("/event/<int:event_id>/edit")
@login_required
def edit_event(event_id):
    if current_user.role != "admin":
        abort(403)
    return redirect(url_for("admin.edit_event", event_id=event_id), code=308)

@web.route("/privacy")
def privacy():
    return render_template("privacy.html")
