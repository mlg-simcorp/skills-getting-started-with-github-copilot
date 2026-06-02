import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Reset the in-memory activity store before each test to avoid cross-test pollution.
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)


def test_signup_for_activity_adds_participant():
    activity_name = "Science Club"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity_returns_404():
    response = client.post("/activities/Unknown%20Club/signup", params={"email": "student@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_existing_participant_returns_400():
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_unsubscribes_student():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_from_nonexistent_activity_returns_404():
    response = client.delete("/activities/Unknown%20Club/participants", params={"email": "student@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_missing_participant_returns_404():
    response = client.delete("/activities/Chess%20Club/participants", params={"email": "not.registered@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
