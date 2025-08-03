from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    email_opt_in = db.Column(db.Boolean, default=True)

    assignments = db.relationship("Assignment", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # Event Details
    alternate_travel = db.Column(db.Text)
    accommodation_name = db.Column(db.String(150), nullable=True)
    accommodation_address = db.Column(db.String(255), nullable=True)
    accommodation_airbnb_link = db.Column(db.String, nullable=True)
    rental_car_info = db.Column(db.String(255))
    coach_name = db.Column(db.String(100))
    coach_email = db.Column(db.String(100))
    coach_phone = db.Column(db.String(50))
    style = db.Column(db.String(50), nullable=True)
    cheer_level = db.Column(db.String(50), nullable=True)
    team_info = db.Column(db.Text, nullable=True)
    schedule_file = db.Column(db.String(255), nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    assignments = db.relationship("Assignment", back_populates="event")
    itinerary_details = db.relationship("ItineraryDetail", back_populates="event", uselist=False)
    event_days = db.relationship("EventDay", backref="event", lazy=True)
    flights = db.relationship("FlightInfo", back_populates="event")


class FlightInfo(db.Model):
    __tablename__ = "flight_info"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)

    flight_departure_datetime = db.Column(db.DateTime, nullable=True)
    flight_return_datetime = db.Column(db.DateTime, nullable=True)
    flight_airline = db.Column(db.String(100), nullable=True)
    flight_bag_info = db.Column(db.String(255), nullable=True)
    flight_confirmation_code = db.Column(db.String(100), nullable=True)

    event = db.relationship("Event", back_populates="flights")


class EventDay(db.Model):
    __tablename__ = "event_days"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    user = db.relationship("User", back_populates="assignments")
    event = db.relationship("Event", back_populates="assignments")


class ItineraryDetail(db.Model):
    __tablename__ = "itinerary_details"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    flight_info = db.Column(db.Text)
    rental_car_info = db.Column(db.Text)
    hotel_info = db.Column(db.Text)
    pay_details = db.Column(db.Text)
    schedule_notes = db.Column(db.Text)

    event = db.relationship("Event", back_populates="itinerary_details")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
