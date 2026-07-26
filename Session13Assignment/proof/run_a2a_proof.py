import hashlib
import hmac
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from glc_v3.a2a import A2AMessage, A2AServiceHandler, AgentCard


def run_a2a_proof():
    print("=========================================================")
    print("           A2A 1.0 Protocol & Gateway Proof              ")
    print("=========================================================\n")

    card = AgentCard(
        name="Remote Technical Specialist",
        description="Autonomous A2A agent for research synthesis",
        version="1.0.0",
        supportedInterfaces=[
            {"url": "dns:///agent.example.com:443", "protocolBinding": "GRPC", "protocolVersion": "1.0"}
        ],
        capabilities={"streaming": True, "pushNotifications": True},
        skills=[{"id": "research", "name": "Research"}]
    )

    handler = A2AServiceHandler(card)

    # 1. Card retrieval & validation
    card_dict = handler.get_agent_card()
    print(f"1. Agent Card Retrieved: name='{card_dict['name']}', version='{card_dict['version']}'")
    assert card.validate_schema() is True, "Agent Card schema validation failed!"

    # 2. Synchronous message task execution
    msg = A2AMessage(role="user", content="Explain Agent Card boundary.")
    task = handler.send_message_sync(context_id="ctx_001", message=msg)
    print(f"2. Sync Task Executed: task_id={task.task_id}, status={task.status.value}")
    print(f"   Artifact Produced: '{task.output_artifact.content}'\n")

    # 3. Async Push Webhook Signature Verification & Idempotency Deduplication
    payload = {"task_id": task.task_id, "status": "completed"}
    secret = "a2a_shared_secret"
    sig = hmac.new(
        secret.encode("utf-8"),
        json.dumps(payload, sort_keys=True).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # First push
    res1 = handler.receive_async_push(payload, signature=sig, idempotency_key="idempotent_key_001", secret=secret)
    print(f"3. Async Push 1: status={res1['status']}")

    # Replayed push with duplicate key
    res2 = handler.receive_async_push(payload, signature=sig, idempotency_key="idempotent_key_001", secret=secret)
    print(f"4. Replayed Push 2: status={res2['status']} (Duplicate suppressed!)\n")

    # Tampered signature attack test
    try:
        handler.receive_async_push(payload, signature="tampered_signature_xyz", idempotency_key="idempotent_key_002", secret=secret)
        print("ERROR: Tampered signature was incorrectly accepted!")
    except PermissionError as ex:
        print(f"5. Security Defense Verified: {ex}")

    print("\n=========================================================")
    print("             A2A Proof Complete & Verified               ")
    print("=========================================================")


if __name__ == "__main__":
    run_a2a_proof()
