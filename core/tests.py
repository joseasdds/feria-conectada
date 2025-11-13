from django.test import Client

client = Client()

def test_health_ok():
    resp = client.get("/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data

def test_ready_status_code_is_200_or_503():
    resp = client.get("/ready/")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "dependencies" in data
    assert "database" in data["dependencies"]