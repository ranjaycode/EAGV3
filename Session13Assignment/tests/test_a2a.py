import pytest
import hmac
import hashlib
import json
from glc_v3.a2a import AgentCard, A2AServiceHandler, A2AMessage


def test_a2a_card_and_push_signature():
    card = AgentCard(
        name="Test Agent",
        description="A2A unit test agent",
        version="1.0.0",
        supportedInterfaces=[{"url": "http://localhost", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        capabilities={},
        skills=[]
    )
    handler = A2AServiceHandler(card)

    msg = A2AMessage(role="user", content="Hello A2A")
    task = handler.send_message_sync(context_id="c1", message=msg)
    assert task.status.value == "completed"

    payload = {"task_id": task.task_id, "status": "completed"}
    secret = "a2a_secret"
    sig = hmac.new(secret.encode("utf-8"), json.dumps(payload, sort_keys=True).encode("utf-8"), hashlib.sha256).hexdigest()

    # Valid push
    res = handler.receive_async_push(payload, signature=sig, idempotency_key="k1", secret=secret)
    assert res["status"] == "accepted"

    # Duplicate push suppression
    res_dup = handler.receive_async_push(payload, signature=sig, idempotency_key="k1", secret=secret)
    assert res_dup["status"] == "duplicate_suppressed"
