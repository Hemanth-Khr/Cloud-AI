from app import config, responder


def test_draft_contains_steps_and_info_requests():
    draft = responder.build_draft_reply(
        "Cannot SSH", "compute", "high", ["Check the security group", "Check the NACL"], [], False
    )
    assert draft.startswith("Subject: [HIGH] Cannot SSH")
    assert "1. Check the security group" in draft
    assert "Instance ID(s)" in draft


def test_security_note_for_urgent_iam_tickets():
    draft = responder.build_draft_reply("Leaked key", "iam_security", "critical", [], [], False)
    assert "rotate" in draft.lower()


def test_low_confidence_routes_to_human():
    draft = responder.build_draft_reply("", "compute", "medium", [], [], True)
    assert "routed to a support engineer" in draft


def test_llm_disabled_without_key(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert responder.polish_with_llm("draft", "ticket") is None


def test_llm_failure_falls_back_to_none(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key")

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(responder.httpx, "post", boom)
    assert responder.polish_with_llm("draft", "ticket") is None


def test_llm_success_path(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"type": "text", "text": "  Polished reply  "}]}

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(responder.httpx, "post", fake_post)
    assert responder.polish_with_llm("draft", "my key is AKIAIOSFODNN7EXAMPLE") == "Polished reply"
    # Secrets must never be forwarded to the model.
    assert "AKIAIOSFODNN7EXAMPLE" not in captured["json"]["messages"][0]["content"]
