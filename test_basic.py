"""Basic smoke test to verify the application works."""

import os
import tempfile
import time
from pathlib import Path

# Set test environment variables
os.environ['EDGE_SIGNING_SECRET'] = 'test-secret-key'
os.environ['HLS_ROOT'] = tempfile.mkdtemp()

from fastapi.testclient import TestClient
from main import app
from auth import TokenValidator

def test_health_endpoint():
    """Test that health endpoint works."""
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_token_validator():
    """Test that token validator works."""
    validator = TokenValidator('test-secret')
    path = "/live/stream.m3u8"
    exp = int(time.time()) + 3600
    sig = validator._compute_signature(path, exp)
    
    result = validator.validate_request(path, exp, sig)
    assert result.is_valid is True

if __name__ == "__main__":
    test_health_endpoint()
    test_token_validator()
    print("✅ Basic tests passed!")