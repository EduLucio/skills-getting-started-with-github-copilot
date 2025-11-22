import os
import importlib.util
import urllib.parse
import pytest

from fastapi.testclient import TestClient


def load_app():
    # Load FastAPI app from src/app.py by file path so tests don't depend on package layout
    repo_root = os.path.dirname(os.path.dirname(__file__))
    app_path = os.path.join(repo_root, "src", "app.py")
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


@pytest.fixture(scope="module")
def client():
    app = load_app()
    with TestClient(app) as c:
        yield c


def test_get_activities(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    # Expect at least one known activity from the seeded data
    assert "Chess Club" in data


def test_signup_and_cleanup(client):
    activity = "Chess Club"
    email = "test.signup@example.com"

    # Ensure email is not present; if present remove it first
    res = client.get("/activities")
    participants = res.json()[activity]["participants"]
    if email in participants:
        client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")

    # Sign up
    res = client.post(f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}")
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")

    # Verify participant added
    res = client.get("/activities")
    assert email in res.json()[activity]["participants"]

    # Cleanup: remove the participant
    res = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")
    assert res.status_code == 200


def test_delete_nonexistent_returns_404(client):
    activity = "Chess Club"
    email = "this-user-does-not-exist@example.com"

    # Ensure absent
    res = client.get("/activities")
    if email in res.json()[activity]["participants"]:
        client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")

    # Attempt delete
    res = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")
    assert res.status_code == 404
