"""End-to-end API tests. Requires fastapi and httpx (see requirements.txt)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from tests.conftest import REAL_JOB, SCAM_JOB  # noqa: E402


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def register(client, email="api@example.com"):
    response = client.post("/auth/register", json={"full_name": "Api User", "email": email, "password": "s3cret-pass"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["database"] is True and body["model_loaded"] is False


def test_model_info_and_performance_without_artifacts(client):
    info = client.get("/model-info").json()
    assert info["scoring_mode"] == "rules-only" and "description" in info["supported_input_fields"]
    assert client.get("/dashboard/model-performance").json() == {"available": False}


def test_predict_anonymous(client):
    response = client.post("/predict", json=SCAM_JOB)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == "Fraudulent" and body["analysis_id"] is None
    assert any(i["code"] == "upfront_payment" for i in body["risk_indicators"])


def test_predict_validation_errors(client):
    assert client.post("/predict", json={**REAL_JOB, "description": "too short"}).status_code == 422
    assert client.post("/predict", json={**REAL_JOB, "job_title": ""}).status_code == 422
    assert client.post("/predict", json={**REAL_JOB, "description": "x" * 10001}).status_code == 422


def test_predict_saves_history_only_for_signed_in_users(client):
    headers = register(client)
    saved = client.post("/predict", json={**SCAM_JOB, "save_history": True}, headers=headers).json()
    assert saved["analysis_id"] is not None
    anonymous = client.post("/predict", json={**SCAM_JOB, "save_history": True}).json()
    assert anonymous["analysis_id"] is None
    page = client.get("/history", headers=headers).json()
    assert page["total"] == 1 and page["items"][0]["id"] == saved["analysis_id"]


def test_history_requires_authentication(client):
    assert client.get("/history").status_code == 401
    assert client.get("/dashboard/stats").status_code == 401
    assert client.get("/history", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_history_is_private_between_users(client):
    alice, bob = register(client, "alice@example.com"), register(client, "bob@example.com")
    item_id = client.post("/predict", json={**SCAM_JOB, "save_history": True}, headers=alice).json()["analysis_id"]
    assert client.get(f"/history/{item_id}", headers=alice).status_code == 200
    assert client.get(f"/history/{item_id}", headers=bob).status_code == 404
    assert client.delete(f"/history/{item_id}", headers=bob).status_code == 404
    assert client.delete(f"/history/{item_id}", headers=alice).status_code == 204


def test_explain_and_save_flow(client):
    headers = register(client)
    result = client.post("/predict", json=SCAM_JOB).json()
    payload = {**SCAM_JOB, "prediction": result["prediction"], "fraud_probability": result["fraud_probability"],
               "risk_indicators": result["risk_indicators"]}
    explanation = client.post("/explain", json=payload).json()
    assert explanation["source"] == "template" and explanation["reasons"]
    saved = client.post("/history", json={**payload, "explanation": explanation, "model_used": result["model_used"]}, headers=headers)
    assert saved.status_code == 201
    assert client.get(f"/history/{saved.json()['id']}", headers=headers).json()["explanation"]["summary"]


def test_auth_errors(client):
    register(client)
    assert client.post("/auth/register", json={"full_name": "X Y", "email": "api@example.com", "password": "s3cret-pass"}).status_code == 409
    assert client.post("/auth/register", json={"full_name": "X Y", "email": "bad-email", "password": "s3cret-pass"}).status_code == 422
    assert client.post("/auth/register", json={"full_name": "X Y", "email": "n@example.com", "password": "short"}).status_code == 422
    assert client.post("/auth/login", json={"email": "api@example.com", "password": "wrong"}).status_code == 401
    ok = client.post("/auth/login", json={"email": "API@example.com", "password": "s3cret-pass"})
    assert ok.status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {ok.json()['access_token']}"})
    assert me.json()["email"] == "api@example.com" and "password_hash" not in me.json()


def test_login_is_rate_limited(client):
    codes = [client.post("/auth/login", json={"email": "x@example.com", "password": "nope"}).status_code for _ in range(12)]
    assert 429 in codes


def test_frontend_is_served_with_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200 and "JobGuard" in response.text
    assert "default-src 'self'" in response.headers["content-security-policy"]
