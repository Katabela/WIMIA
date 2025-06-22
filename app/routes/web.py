from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.extensions import db
# from app.models import Notes  # Optional: only if you’re using Notes again

web = Blueprint("main", __name__)

@web.route("/")
def index():
    return render_template("index.html", user=current_user)

@web.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

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
