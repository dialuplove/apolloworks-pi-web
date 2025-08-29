"""Integration tests for FastAPI endpoints."""

import os
import tempfile
import time
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Set test environment variables before importing main
os.environ['EDGE_SIGNING_SECRET'] = 'test-secret-key'
os.environ['HLS_ROOT'] = tempfile.mkdtemp()

from main import app
from token_validator import TokenValidator


class TestAPI:
    """Integration tests for API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.secret = 'test-secret-key'
        self.validator = TokenValidator(self.secret)
        self.hls_root = Path(os.environ['HLS_ROOT'])
        
        # Create test HLS files
        self.create_test_files()
    
    def create_test_files(self):
        """Create test HLS files in temporary directory."""
        # Create m3u8 file
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
segment001.ts
#EXTINF:10.0,
segment002.ts
#EXT-X-ENDLIST
"""
        (self.hls_root / "stream.m3u8").write_text(m3u8_content)
        
        # Create test .ts files
        (self.hls_root / "segment001.ts").write_bytes(b"fake ts content 1")
        (self.hls_root / "segment002.ts").write_bytes(b"fake ts content 2")
    
    def generate_valid_token(self, path: str, exp_offset: int = 3600) -> tuple[int, str]:
        """Generate valid token parameters.
        
        Args:
            path: Request path
            exp_offset: Seconds from now for expiration
            
        Returns:
            Tuple of (exp, sig)
        """
        exp = int(time.time()) + exp_offset
        sig = self.validator._compute_signature(path, exp)
        return exp, sig
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/healthz")
        
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require authentication."""
        # Should work without any query parameters
        response = self.client.get("/healthz")
        assert response.status_code == 200
    
    def test_m3u8_serving_with_valid_token(self):
        """Test successful m3u8 file serving with valid token."""
        path = "/live/stream.m3u8"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 200
        assert "segment001.ts" in response.text
        assert "segment002.ts" in response.text
    
    def test_m3u8_content_type_and_headers(self):
        """Test proper Content-Type and Cache-Control headers for m3u8."""
        path = "/live/stream.m3u8"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.apple.mpegurl"
        assert response.headers["cache-control"] == "no-store"
    
    def test_m3u8_expired_token_rejection(self):
        """Test m3u8 serving with expired token."""
        path = "/live/stream.m3u8"
        exp, sig = self.generate_valid_token(path, -3600)  # 1 hour ago
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 410
        assert response.json() == {"error": "expired"}
    
    def test_m3u8_invalid_signature_rejection(self):
        """Test m3u8 serving with invalid signature."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600
        sig = "invalid-signature"
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 403
        assert response.json() == {"error": "forbidden"}
    
    def test_m3u8_missing_parameters(self):
        """Test m3u8 serving with missing parameters."""
        path = "/live/stream.m3u8"
        
        # Missing both parameters
        response = self.client.get(path)
        assert response.status_code == 400
        assert response.json() == {"error": "missing_parameters"}
        
        # Missing sig parameter
        exp = int(time.time()) + 3600
        response = self.client.get(f"{path}?exp={exp}")
        assert response.status_code == 400
        assert response.json() == {"error": "missing_parameters"}
        
        # Missing exp parameter
        response = self.client.get(f"{path}?sig=test-sig")
        assert response.status_code == 400
        assert response.json() == {"error": "missing_parameters"}
    
    def test_m3u8_file_not_found(self):
        """Test m3u8 serving when file doesn't exist."""
        # Remove the test file
        (self.hls_root / "stream.m3u8").unlink()
        
        path = "/live/stream.m3u8"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 404
        assert response.json() == {"detail": "File not found"}
    
    def test_ts_serving_with_valid_token(self):
        """Test successful .ts file serving with valid token."""
        path = "/live/segment001.ts"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 200
        assert response.content == b"fake ts content 1"
    
    def test_ts_content_type_and_headers(self):
        """Test proper Content-Type and Cache-Control headers for .ts files."""
        path = "/live/segment001.ts"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp2t"
        assert response.headers["cache-control"] == "public, max-age=10, immutable"
    
    def test_ts_different_segments(self):
        """Test serving different .ts segments."""
        # Test segment001
        path1 = "/live/segment001.ts"
        exp1, sig1 = self.generate_valid_token(path1)
        response1 = self.client.get(f"{path1}?exp={exp1}&sig={sig1}")
        
        assert response1.status_code == 200
        assert response1.content == b"fake ts content 1"
        
        # Test segment002
        path2 = "/live/segment002.ts"
        exp2, sig2 = self.generate_valid_token(path2)
        response2 = self.client.get(f"{path2}?exp={exp2}&sig={sig2}")
        
        assert response2.status_code == 200
        assert response2.content == b"fake ts content 2"
    
    def test_ts_expired_token_rejection(self):
        """Test .ts serving with expired token."""
        path = "/live/segment001.ts"
        exp, sig = self.generate_valid_token(path, -3600)  # 1 hour ago
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 410
        assert response.json() == {"error": "expired"}
    
    def test_ts_invalid_signature_rejection(self):
        """Test .ts serving with invalid signature."""
        path = "/live/segment001.ts"
        exp = int(time.time()) + 3600
        sig = "invalid-signature"
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 403
        assert response.json() == {"error": "forbidden"}
    
    def test_ts_missing_parameters(self):
        """Test .ts serving with missing parameters."""
        path = "/live/segment001.ts"
        
        # Missing both parameters
        response = self.client.get(path)
        assert response.status_code == 400
        assert response.json() == {"error": "missing_parameters"}
    
    def test_ts_file_not_found(self):
        """Test .ts serving when file doesn't exist."""
        path = "/live/nonexistent.ts"
        exp, sig = self.generate_valid_token(path)
        
        response = self.client.get(f"{path}?exp={exp}&sig={sig}")
        
        assert response.status_code == 404
        assert response.json() == {"detail": "File not found"}
    
    def test_path_case_insensitive_signature(self):
        """Test that path case doesn't affect signature validation."""
        # Generate signature with lowercase path
        lower_path = "/live/segment001.ts"
        exp, sig = self.generate_valid_token(lower_path)
        
        # Test with uppercase path - should work due to normalization
        upper_path = "/live/SEGMENT001.ts"
        response = self.client.get(f"{upper_path}?exp={exp}&sig={sig}")
        
        # Note: This will fail because the file doesn't exist with uppercase name
        # But the signature validation should pass (we'd get 404, not 403)
        assert response.status_code == 404  # File not found, not forbidden
    
    def test_invalid_expiration_format(self):
        """Test handling of invalid expiration format."""
        path = "/live/stream.m3u8"
        sig = "test-signature"
        
        response = self.client.get(f"{path}?exp=invalid&sig={sig}")
        
        assert response.status_code == 400
        assert response.json() == {"error": "invalid_expiration"}
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.hls_root, ignore_errors=True)