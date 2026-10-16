import uuid
from fastapi.testclient import TestClient
from main import app
from matching import CAN_RECEIVE_FROM, distance_km

client = TestClient(app)


# ---- Matching logic ----
def test_o_negative_can_give_to_everyone():
    for group, donors in CAN_RECEIVE_FROM.items():
        assert "O-" in donors


def test_o_negative_receives_only_from_o_negative():
    assert CAN_RECEIVE_FROM["O-"] == ["O-"]


def test_ab_positive_receives_from_all_groups():
    assert len(CAN_RECEIVE_FROM["AB+"]) == 8


def test_distance_is_zero_for_same_point():
    assert distance_km(12.29, 76.63, 12.29, 76.63) == 0


def test_distance_mysuru_to_bengaluru():
    d = distance_km(12.2958, 76.6394, 12.9716, 77.5946)
    assert 120 < d < 150


# ---- API ----
def test_home_page():
    assert client.get("/").status_code == 200


def test_register_login_and_me():
    email = f"ci_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/auth/register", json={
        "name": "CI User", "email": email, "phone": "9999999999",
        "password": "test1234", "role": "donor",
    })
    assert r.status_code == 201

    r = client.post("/auth/login", data={"username": email, "password": "test1234"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_me_requires_login():
    assert client.get("/auth/me").status_code == 401


def test_wrong_password_is_rejected():
    r = client.post("/auth/login", data={"username": "nobody@example.com", "password": "wrong"})
    assert r.status_code == 401