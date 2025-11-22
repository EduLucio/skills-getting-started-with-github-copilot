import os
import importlib.util
import urllib.parse
import copy
import pytest

from fastapi.testclient import TestClient


def load_app_module():
    repo_root = os.path.dirname(os.path.dirname(__file__))
    app_path = os.path.join(repo_root, "src", "app.py")
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="function", autouse=True)
def restore_activities(app_module):
    """Garante que o dicionário `activities` seja restaurado após cada teste."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


@pytest.fixture(scope="module")
def app_module():
    return load_app_module()


@pytest.fixture(scope="module")
def client(app_module):
    with TestClient(app_module.app) as c:
        yield c


def test_resignup_returns_400(client, app_module):
    module = app_module
    activity = "Chess Club"
    # pick an existing participant
    existing = module.activities[activity]["participants"][0]

    res = client.post(f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(existing)}")
    assert res.status_code == 400
    assert "already" in res.json().get("detail", "").lower()


def test_capacity_enforced(client, app_module):
    module = app_module
    activity_name = "Tiny Club For Tests"
    # create a tiny activity with max_participants = 1
    module.activities[activity_name] = {
        "description": "A tiny test activity",
        "schedule": "Now",
        "max_participants": 1,
        "participants": []
    }

    email1 = "first@example.test"
    email2 = "second@example.test"

    # first signup should succeed
    res1 = client.post(f"/activities/{urllib.parse.quote(activity_name)}/signup?email={urllib.parse.quote(email1)}")
    assert res1.status_code == 200

    # second signup should fail with 400 and Activity is full
    res2 = client.post(f"/activities/{urllib.parse.quote(activity_name)}/signup?email={urllib.parse.quote(email2)}")
    assert res2.status_code == 400
    assert "full" in res2.json().get("detail", "").lower()


def test_signup_then_get_shows_participant(client, app_module):
    module = app_module
    activity = "Programming Class"
    email = "e2e.test.user@example.test"

    # ensure absent
    participants = client.get("/activities").json()[activity]["participants"]
    if email in participants:
        client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")

    # signup
    r = client.post(f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}")
    assert r.status_code == 200

    # now GET should show the new participant
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]

    # cleanup
    client.delete(f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}")
