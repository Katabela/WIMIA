from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User
from app.email import send_email
import random
import uuid

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        remember = request.form.get("remember") == "on"

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid email or password", "danger")
    return render_template("auth/login.html", user=current_user)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        fullname = request.form.get("fullname")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        remember = request.form.get("remember") == "on"
        email_opt_in = request.form.get("email_opt_in") == "on"

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register"))

        verification_code = str(random.randint(100000, 999999))
        temp_user_uuid = str(uuid.uuid4())

        session[temp_user_uuid] = {
            "email": email,
            "fullname": fullname,
            "password": password,
            "email_opt_in": email_opt_in,
            "verification_code": verification_code,
        }

        send_email(
            email,
            "Verify Your Email",
            "verification_email.html",
            verification_code=verification_code,
        )

        flash("A verification code has been sent to your email.", "info")
        return redirect(
            url_for("auth.verify_email", id=temp_user_uuid, remember="on" if remember else "off")
        )

    return render_template("auth/register.html", user=current_user)

@auth.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    temp_user_id = request.args.get("id")
    temp_user = session.get(temp_user_id)

    if not temp_user:
        flash("Session expired. Please register again.", "danger")
        return redirect(url_for("auth.register"))

    remember = request.args.get("remember") == "on"

    if request.method == "POST":
        code = request.form.get("code")
        if temp_user["verification_code"] == code:
            new_user = User(
                email=temp_user["email"],
                fullname=temp_user["fullname"],
                email_opt_in=temp_user["email_opt_in"],
            )
            new_user.set_password(temp_user["password"])
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=remember)
            session.pop(temp_user_id, None)
            flash("Your email has been verified, and you are now logged in!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid verification code. Please try again.", "danger")

    return render_template("auth/verify_email.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("main.index"))

