import copy
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_state(tmp_path, monkeypatch):
    teachers_file = tmp_path / "teachers.json"
    teachers_file.write_text(
        json.dumps({"teachers": [{"username": "teacher", "password": "secret"}]})
    )
    monkeypatch.setenv("TEACHERS_FILE", str(teachers_file))
    app_module.activities = copy.deepcopy(app_module.DEFAULT_ACTIVITIES)
    app_module.teachers = app_module.load_teachers()
    yield
    app_module.activities = copy.deepcopy(app_module.DEFAULT_ACTIVITIES)
    app_module.teachers = app_module.load_teachers()


def test_signup_requires_teacher_login():
    client = TestClient(app_module.app)

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@test.com"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Teacher login required"


def test_teacher_login_allows_signup():
    client = TestClient(app_module.app)

    login_response = client.post(
        "/auth/login",
        json={"username": "teacher", "password": "secret"},
    )

    assert login_response.status_code == 200

    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@test.com"},
    )

    assert signup_response.status_code == 200
    assert "student@test.com" in app_module.activities["Chess Club"]["participants"]
