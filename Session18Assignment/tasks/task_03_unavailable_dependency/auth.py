"""
auth.py - HMAC Signature generator.
"""
import hmac
import hashlib
import os

def generate_signature(message: str) -> str:
    """
    Generates SHA256 HMAC signature for message using environment variable API_SECRET_KEY.
    Raises RuntimeError if API_SECRET_KEY is missing.
    """
    secret_key = os.environ.get("API_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("API_SECRET_KEY environment variable is missing")
    
    return hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
