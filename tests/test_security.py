from pathlib import Path

import pytest
from werkzeug.datastructures import MultiDict

from app.extensions import db
from app.models import Assignment, Event, User
from app.routes.admin import parse_event_days
from tests.conftest import login_as


def make_user(email, role="employee"):
    user = User(fullname="Test User", email=email, role=role)
    user.set_password("correct horse battery staple")
    db.session.add(user)
    db.session.commit()
    return user


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_employee_cannot_open_legacy_event_editor(app, client):
    with app.app_context():
        employee = make_user("employee@example.com")
        employee_id = employee.id

    login_as(client, employee_id)

    assert client.get("/event/new").status_code == 403
    assert client.post("/event/new").status_code == 405


def test_admin_legacy_event_url_redirects_to_guarded_editor(app, client):
    with app.app_context():
        admin = make_user("admin@example.com", role="admin")
        admin_id = admin.id

    login_as(client, admin_id)

    response = client.get("/event/new")
    assert response.status_code == 308
    assert response.headers["Location"].endswith("/admin/event/add")


def test_post_without_csrf_token_is_rejected(client):
    response = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "bad"},
    )
    assert response.status_code == 400


def test_event_day_must_end_after_it_starts():
    form = MultiDict(
        [
            ("event_start_times", "2026-11-07T12:00"),
            ("event_end_times", "2026-11-07T11:00"),
        ]
    )

    with pytest.raises(ValueError, match="end after"):
        parse_event_days(form)


def test_schedule_download_requires_assignment(app, tmp_path):
    with app.app_context():
        assigned = make_user("assigned@example.com")
        unassigned = make_user("unassigned@example.com")
        event = Event(name="Nationals", location="Orlando", schedule_file="schedule.pdf")
        db.session.add(event)
        db.session.flush()
        db.session.add(Assignment(user_id=assigned.id, event_id=event.id))
        db.session.commit()
        event_id = event.id
        assigned_id = assigned.id
        unassigned_id = unassigned.id

        upload_dir = Path(app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True)
        (upload_dir / "schedule.pdf").write_bytes(b"test schedule")

    unassigned_client = app.test_client()
    login_as(unassigned_client, unassigned_id)
    assert unassigned_client.get(f"/event/{event_id}/schedule").status_code == 403

    assigned_client = app.test_client()
    login_as(assigned_client, assigned_id)
    response = assigned_client.get(f"/event/{event_id}/schedule")
    assert response.status_code == 200
    assert response.data == b"test schedule"
