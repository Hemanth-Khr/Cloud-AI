import pandas as pd

from app.classifier import TicketClassifier
from app.config import EVAL_CSV


def test_predicts_obvious_ticket():
    clf = TicketClassifier()
    pred = clf.predict("My EC2 instance is unreachable and SSH times out")
    assert pred.label == "compute"
    assert 0.0 <= pred.confidence <= 1.0
    assert len(pred.alternatives) == 2


def test_accuracy_on_handwritten_tickets():
    """Independent set written by hand, not generated from the training templates."""
    clf = TicketClassifier()
    ev = pd.read_csv(EVAL_CSV)
    predicted = [clf.predict(t).label for t in ev["text"]]
    accuracy = sum(p == y for p, y in zip(predicted, ev["category"])) / len(ev)
    assert accuracy >= 0.85, f"accuracy dropped to {accuracy:.1%}"
