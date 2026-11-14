from app import config


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_triage_end_to_end(client):
    r = client.post(
        "/triage",
        json={
            "subject": "ALB 502 errors",
            "description": "Application load balancer returns 502 bad gateway and all targets are unhealthy in production.",
            "logs": "2026-11-14 ERROR 502 Bad Gateway from upstream\n2026-11-14 ERROR Connection refused 10.0.2.8:8080",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "networking"
    assert body["priority"] == "high"
    assert body["suggested_articles"][0]["id"] == "networking-troubleshooting"
    assert "load balancer" in body["matched_scenario"].lower()
    assert any("keep-alive" in s for s in body["suggested_steps"])
    assert body["log_analysis"]["findings"]
    assert body["draft_reply"].startswith("Subject: [HIGH]")
    assert body["reply_source"] == "template"


def test_triage_rejects_short_description(client):
    r = client.post("/triage", json={"description": "help"})
    assert r.status_code == 422


def test_llm_flag_falls_back_to_template_without_key(client, monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    r = client.post(
        "/triage",
        json={"description": "RDS database connection refused from the app", "use_llm": True},
    )
    assert r.status_code == 200
    assert r.json()["reply_source"] == "template"


def test_low_confidence_is_flagged_for_human_review(client, monkeypatch):
    monkeypatch.setattr(config, "MIN_CONFIDENCE", 0.99)
    r = client.post("/triage", json={"description": "something odd is happening with my account"})
    body = r.json()
    assert body["needs_human_review"] is True
    assert "routed to a support engineer" in body["draft_reply"]


def test_analyze_logs_endpoint(client):
    r = client.post("/analyze-logs", json={"logs": "ERROR No space left on device"})
    assert r.status_code == 200
    assert r.json()["findings"][0]["id"] == "disk_full"


def test_kb_listing(client):
    r = client.get("/kb")
    assert r.status_code == 200
    assert len(r.json()) == 7


def test_secrets_not_echoed_in_reply(client):
    r = client.post(
        "/triage",
        json={
            "description": "Leaked access key AKIAIOSFODNN7EXAMPLE was pushed to GitHub, please help",
            "subject": "Key AKIAIOSFODNN7EXAMPLE leaked",
        },
    )
    assert "AKIAIOSFODNN7EXAMPLE" not in r.text
