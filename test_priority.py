import pytest

from app.priority import score_priority


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Production is completely down and customers are impacted.", "critical"),
        ("We accidentally pushed an access key to GitHub", "critical"),
        ("We accidentally pushed an AWS access key to a public GitHub repo", "critical"),
        ("Our secret key was exposed in a public repo", "critical"),
        ("How do I rotate access keys for my IAM user as a best practice", "low"),
        ("Possible security breach, data may be exposed.", "critical"),
        ("This is blocking our release today.", "high"),
        ("Hi team, Urgent: cannot SSH into my EC2 instance", "high"),
        ("Not urgent, asking for best practice.", "low"),
        ("Just a general question, no impact.", "low"),
        ("Workaround exists but it is inconvenient.", "medium"),
    ],
)
def test_priority_levels(text, expected):
    assert score_priority(text).level == expected


def test_security_tickets_default_to_high():
    result = score_priority("User is not authorized to perform ec2:RunInstances", "iam_security")
    assert result.level == "high"


def test_reasons_are_explained():
    result = score_priority("Production is down for all users")
    assert result.reasons and "critical" in result.reasons[0]
