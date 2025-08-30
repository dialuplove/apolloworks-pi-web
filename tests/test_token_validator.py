"""Unit tests for TokenValidator."""

import time
import pytest
from token import TokenValidator


class TestTokenValidator:
    """Test cases for TokenValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.secret = "test-secret-key"
        self.validator = TokenValidator(self.secret)
    
    def test_valid_signature_computation(self):
        """Test valid signature computation with various paths."""
        # Test with m3u8 file
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600  # 1 hour from now
        sig = self.validator._compute_signature(path, exp)
        
        result = self.validator.validate_request(path, exp, sig)
        assert result.is_valid is True
        assert result.error_type is None
        assert result.status_code is None
    
    def test_valid_signature_with_ts_file(self):
        """Test valid signature with .ts segment file."""
        path = "/live/segment001.ts"
        exp = int(time.time()) + 1800  # 30 minutes from now
        sig = self.validator._compute_signature(path, exp)
        
        result = self.validator.validate_request(path, exp, sig)
        assert result.is_valid is True
    
    def test_invalid_signature_rejection(self):
        """Test rejection of invalid signatures."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600
        
        # Use wrong signature
        wrong_sig = "invalid-signature"
        result = self.validator.validate_request(path, exp, wrong_sig)
        
        assert result.is_valid is False
        assert result.error_type == "forbidden"
        assert result.status_code == 403
    
    def test_tampered_signature_rejection(self):
        """Test rejection of tampered signatures."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600
        sig = self.validator._compute_signature(path, exp)
        
        # Tamper with signature
        tampered_sig = sig[:-1] + "X"
        result = self.validator.validate_request(path, exp, tampered_sig)
        
        assert result.is_valid is False
        assert result.error_type == "forbidden"
        assert result.status_code == 403
    
    def test_expired_token_rejection(self):
        """Test rejection of expired tokens."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) - 3600  # 1 hour ago (expired)
        sig = self.validator._compute_signature(path, exp)
        
        result = self.validator.validate_request(path, exp, sig)
        
        assert result.is_valid is False
        assert result.error_type == "expired"
        assert result.status_code == 410
    
    def test_path_normalization_lowercase(self):
        """Test path normalization to lowercase for signature computation."""
        exp = int(time.time()) + 3600
        
        # Generate signature with lowercase path
        lower_path = "/live/stream.m3u8"
        sig = self.validator._compute_signature(lower_path, exp)
        
        # Test with uppercase path - should work due to normalization
        upper_path = "/LIVE/STREAM.M3U8"
        result = self.validator.validate_request(upper_path, exp, sig)
        
        assert result.is_valid is True
    
    def test_path_normalization_mixed_case(self):
        """Test path normalization with mixed case."""
        exp = int(time.time()) + 3600
        
        # Generate signature with lowercase path
        lower_path = "/live/segment001.ts"
        sig = self.validator._compute_signature(lower_path, exp)
        
        # Test with mixed case path
        mixed_path = "/Live/Segment001.TS"
        result = self.validator.validate_request(mixed_path, exp, sig)
        
        assert result.is_valid is True
    
    def test_unpadded_base64url_encoding(self):
        """Test that signatures use unpadded base64url encoding."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600
        sig = self.validator._compute_signature(path, exp)
        
        # Signature should not contain padding characters
        assert '=' not in sig
        
        # Should be valid base64url characters only
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        assert all(c in valid_chars for c in sig)
    
    def test_signature_consistency(self):
        """Test that same inputs produce same signature."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 3600
        
        sig1 = self.validator._compute_signature(path, exp)
        sig2 = self.validator._compute_signature(path, exp)
        
        assert sig1 == sig2
    
    def test_different_paths_different_signatures(self):
        """Test that different paths produce different signatures."""
        exp = int(time.time()) + 3600
        
        sig1 = self.validator._compute_signature("/live/stream.m3u8", exp)
        sig2 = self.validator._compute_signature("/live/segment001.ts", exp)
        
        assert sig1 != sig2
    
    def test_different_expiration_different_signatures(self):
        """Test that different expiration times produce different signatures."""
        path = "/live/stream.m3u8"
        exp1 = int(time.time()) + 3600
        exp2 = int(time.time()) + 7200
        
        sig1 = self.validator._compute_signature(path, exp1)
        sig2 = self.validator._compute_signature(path, exp2)
        
        assert sig1 != sig2
    
    def test_edge_case_just_expired(self):
        """Test token that just expired."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) - 1  # 1 second ago
        sig = self.validator._compute_signature(path, exp)
        
        result = self.validator.validate_request(path, exp, sig)
        
        assert result.is_valid is False
        assert result.error_type == "expired"
        assert result.status_code == 410
    
    def test_edge_case_just_valid(self):
        """Test token that is just still valid."""
        path = "/live/stream.m3u8"
        exp = int(time.time()) + 1  # 1 second from now
        sig = self.validator._compute_signature(path, exp)
        
        result = self.validator.validate_request(path, exp, sig)
        
        assert result.is_valid is True