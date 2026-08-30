import pytest
from auth import generate_signature

def test_signature_generation():
    """Requires API_SECRET_KEY fixture from conftest.py or environment."""
    sig = generate_signature("user-payload-101")
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA256 hex digest length
