from app.log_analyzer import analyze_logs

SAMPLE = """\
2026-11-14T10:00:01Z ERROR Task timed out after 3.00 seconds
2026-11-14T10:00:02Z ERROR Connection refused to 10.0.1.5:5432
2026-11-14T10:00:03Z WARN An error occurred (AccessDenied) when calling the PutObject operation
2026-11-14T10:00:04Z ERROR Task timed out after 3.00 seconds
2026-11-14T10:00:05Z INFO healthy
"""


def test_detects_known_signatures():
    result = analyze_logs(SAMPLE)
    ids = {f["id"]: f for f in result["findings"]}
    assert ids["lambda_timeout"]["occurrences"] == 2
    assert "connection_refused" in ids
    assert "access_denied" in ids
    assert result["lines_scanned"] == 5
    assert result["error_line_count"] == 3


def test_findings_sorted_by_severity():
    findings = analyze_logs(SAMPLE)["findings"]
    ranks = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    scores = [ranks[f["severity"]] for f in findings]
    assert scores == sorted(scores, reverse=True)


def test_clean_logs_have_no_findings():
    result = analyze_logs("INFO started\nINFO listening on 8080\n")
    assert result["findings"] == []


def test_secrets_are_redacted_in_evidence():
    line = "ERROR AccessDenied for key AKIAIOSFODNN7EXAMPLE password=hunter2"
    example = analyze_logs(line)["findings"][0]["example"]
    assert "AKIAIOSFODNN7EXAMPLE" not in example
    assert "hunter2" not in example
