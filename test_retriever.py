import pytest

from app.retriever import Retriever


@pytest.fixture(scope="module")
def retriever():
    return Retriever()


@pytest.mark.parametrize(
    "query, expected_doc",
    [
        ("cannot ssh into my ec2 instance connection timed out", "compute-troubleshooting"),
        ("s3 bucket returns 403 access denied on upload", "storage-troubleshooting"),
        ("application load balancer 502 bad gateway targets unhealthy", "networking-troubleshooting"),
        ("unexpected charges on my monthly bill", "billing-troubleshooting"),
        ("rds too many connections and high cpu", "database-troubleshooting"),
        ("cloudwatch alarm insufficient data sns email not received", "monitoring-troubleshooting"),
        ("lost mfa device assume role not authorized", "iam-troubleshooting"),
    ],
)
def test_top_document_is_relevant(retriever, query, expected_doc):
    hits = retriever.search(query, k=3)
    assert hits, "expected at least one hit"
    assert hits[0].doc_id == expected_doc


# The scenario-level chunking is what makes the *steps* relevant, not just the page.
@pytest.mark.parametrize(
    "doc_id, query, expected_scenario_fragment, expected_step_fragment",
    [
        ("networking-troubleshooting", "ALB returns 502 bad gateway and targets are unhealthy", "Load balancer", "keep-alive"),
        ("networking-troubleshooting", "private subnet instances cannot reach the internet NAT gateway", "NAT gateway", "NAT Gateway"),
        ("networking-troubleshooting", "my domain is not resolving to the load balancer route 53", "Route 53", "name servers"),
        ("networking-troubleshooting", "vpc peering is active but traffic is not flowing", "peering", "both"),
        ("storage-troubleshooting", "browser upload blocked with a cors error", "CORS", "CORS configuration"),
        ("storage-troubleshooting", "i deleted an object by mistake in a versioned bucket", "Recover deleted", "delete marker"),
        ("iam-troubleshooting", "we pushed an access key to github", "Leaked access keys", "Deactivate"),
        ("iam-troubleshooting", "i lost my mfa device and cannot log in", "MFA", "resync"),
        ("iam-troubleshooting", "assume role is not authorized in the other account", "AssumeRole", "trust policy"),
        ("database-troubleshooting", "too many connections error from mysql", "Too many connections", "RDS Proxy"),
        ("database-troubleshooting", "dynamodb throttling provisioned throughput exceeded", "DynamoDB", "on-demand"),
        ("monitoring-troubleshooting", "alarm fires but i never get the email", "no email", "Confirmed"),
        ("compute-troubleshooting", "lambda function timed out after 3 seconds", "Lambda", "REPORT"),
    ],
)
def test_best_scenario_is_selected(
    retriever, doc_id, query, expected_scenario_fragment, expected_step_fragment
):
    scenario = retriever.scenario_for(doc_id, query)
    assert scenario is not None
    assert expected_scenario_fragment.lower() in scenario.scenario.lower()
    assert any(expected_step_fragment.lower() in s.lower() for s in scenario.steps)


def test_steps_are_limited_and_clean(retriever):
    steps = retriever.steps_for("compute-troubleshooting", "cannot ssh into my ec2 instance", limit=3)
    assert len(steps) == 3
    assert all("**" not in s and "`" not in s for s in steps)


def test_category_boost_promotes_matching_docs(retriever):
    plain = retriever.search("access denied", k=7)
    boosted = retriever.search("access denied", k=7, category="storage")
    plain_score = next(h.score for h in plain if h.doc_id == "storage-troubleshooting")
    boosted_score = next(h.score for h in boosted if h.doc_id == "storage-troubleshooting")
    assert boosted_score > plain_score


def test_lists_all_articles(retriever):
    assert len(retriever.list_articles()) == 7


def test_unrelated_query_returns_nothing(retriever):
    assert retriever.search("zzzz qqqq xxxx") == []
