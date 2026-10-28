"""HTTP smoke checks through nginx on the isolated Compose verification project."""
import json
from pathlib import Path
import httpx

BASE = "http://127.0.0.1:13000"
ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    with httpx.Client(base_url=BASE, timeout=30) as client:
        response = client.get("/")
        assert response.status_code == 200 and 'id="root"' in response.text
        checks.append("frontend HTML served by nginx")
        health = client.get("/api/v1/health")
        assert health.status_code == 200 and health.json()["model_loaded"] is True
        checks.append("backend lifespan, PostgreSQL and real artifact ready")
        preflight = client.options("/api/v1/predictions/", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Private-Network": "true"})
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-private-network"] == "true"
        checks.append("CORS/PNA preflight including Authorization")
        login = client.post("/api/v1/auth/login", json={"username": "admin@huit.edu.vn", "password": "admin"})
        assert login.status_code == 200
        tokens = login.json()
        headers = {"Authorization": "Bearer " + tokens["access_token"]}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
        assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
        checks.append("login, authenticated me, invalid JWT and refresh through nginx")
        # Fixture account only in the isolated verification stack; never uses the working DB.
        accounts = client.get("/api/v1/admin/users", headers=headers).json()
        if not any(user["email"] == "task5-browser@example.com" for user in accounts):
            created = client.post("/api/v1/admin/users", headers=headers, json={
                "email": "task5-browser@example.com", "password": "Task5-browser!",
                "full_name": "Task 5 Browser B", "role_codes": ["ADMIN"]})
            assert created.status_code == 200, created.text
        features = dict(code_module="AAA", gender="M", highest_education="HE Qualification",
                        age_band="0-35", studied_credits=60, date_registration=0,
                        total_clicks_to_t=280, clicks_resource_to_t=180, clicks_url_to_t=50,
                        active_days_to_t=32, active_day_ratio=.4, days_since_last_activity=2,
                        clicks_recent_7=25, clicks_recent_30=100, assessments_submitted_to_t=8,
                        late_submissions_to_t=1, submission_rate=.8)
        prediction = client.post("/api/v1/predictions/", headers=headers, json={"features": features})
        assert prediction.status_code == 200, prediction.text
        provenance = prediction.json()["provenance"]
        assert provenance["model_id"] and provenance["model_sha256"]
        assert provenance["features"] == features
        checks.append("real artifact inference and exact input/model provenance through nginx")
    result = {"base_url": BASE, "passed": len(checks), "checks": checks,
              "model_sha256": provenance["model_sha256"], "model_version": provenance["model_version"]}
    destination = ROOT / "reports/test-results/task5-stack.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
