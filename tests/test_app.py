import copy
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)

# Snapshot the initial activities data so we can reset between tests
_BASE_ACTIVITIES = copy.deepcopy(activities)


def reset_activities_state():
    """Reset the global in-memory activities to the base snapshot."""
    activities.clear()
    activities.update(copy.deepcopy(_BASE_ACTIVITIES))


def setup_function(_func):
    # Runs before each test function
    reset_activities_state()


def test_get_activities_returns_data():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Check a couple of known activities exist
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Structure sanity
    chess = data["Chess Club"]
    assert "description" in chess and "participants" in chess and "max_participants" in chess


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    activity = "Chess Club"

    # Sign up
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json()["message"]

    # Verify via GET
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]


def test_signup_duplicate_is_error():
    activity = "Programming Class"
    email = _BASE_ACTIVITIES[activity]["participants"][0]

    # Already registered; second signup should fail
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up for this activity"


def test_unregister_removes_participant():
    activity = "Gym Class"
    # Ensure one known participant exists
    email = _BASE_ACTIVITIES[activity]["participants"][0]

    # Unregister
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert f"Unregistered {email} from {activity}" in resp.json()["message"]

    # Verify removal
    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]


def test_unregister_nonexistent_is_404():
    activity = "Basketball Team"
    email = "notregistered@mergington.edu"

    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Student not registered for this activity"


def test_signup_when_activity_full():
    # Use Tennis Club which has max_participants of 10
    activity = "Tennis Club"
    
    # Fill the activity to max capacity
    activities[activity]["participants"] = [f"student{i}@mergington.edu" for i in range(10)]
    
    # Try to add one more
    resp = client.post(f"/activities/{activity}/signup", params={"email": "overflow@mergington.edu"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Activity is full"


def test_signup_nonexistent_activity():
    email = "newstudent@mergington.edu"
    activity = "NonExistentActivity"

    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_from_nonexistent_activity():
    email = "student@mergington.edu"
    activity = "NonExistentActivity"

    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
