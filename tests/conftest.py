import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("config.Config.SECRET_KEY", "test-secret")
    monkeypatch.setattr("config.Config.SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr("config.Config.SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr("config.Config.UPLOAD_FOLDER", str(tmp_path / "uploads"))

    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login_as(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
