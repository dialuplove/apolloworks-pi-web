"""Token validation module for HLS streaming authentication."""

import base64
import hashlib
import hmac
import time
from typing import Optional


class ValidationResult:
    """Result of token validation."""
    
    def __init__(self, is_valid: bool, error_type: Optional[str] = None, status_code: Optional[int] = None):
        self.is_valid = is_valid
        self.error_type = error_type
        self.status_code = status_code


class TokenValidator:
    """Validates HMAC-SHA256 signed tokens for HLS stream access."""
    
    def __init__(self, signing_secret: str):
        """Initialize validator with signing secret.
        
        Args:
            signing_secret: HMAC signing key
        """
        self.signing_secret = signing_secret.encode('utf-8')
    
    def validate_request(self, path: str, exp: int, sig: str) -> ValidationResult:
        """Validate a request with token parameters.
        
        Args:
            path: Request path (e.g., "/live/stream.m3u8")
            exp: Expiration timestamp (Unix time)
            sig: Base64URL encoded signature (unpadded)
            
        Returns:
            ValidationResult with validation status and error details
        """
        # Check expiration first
        if self._is_expired(exp):
            return ValidationResult(False, "expired", 410)
        
        # Compute expected signature
        expected_sig = self._compute_signature(path, exp)
        
        # Compare signatures
        if sig != expected_sig:
            return ValidationResult(False, "forbidden", 403)
        
        return ValidationResult(True)
    
    def _compute_signature(self, path: str, exp: int) -> str:
        """Compute HMAC-SHA256 signature for path and expiration.
        
        Args:
            path: Request path in lowercase
            exp: Expiration timestamp
            
        Returns:
            Base64URL encoded signature (unpadded)
        """
        # Normalize path to lowercase
        normalized_path = path.lower()
        
        # Create message: path + exp
        message = f"{normalized_path}{exp}".encode('utf-8')
        
        # Compute HMAC-SHA256
        signature = hmac.new(self.signing_secret, message, hashlib.sha256).digest()
        
        # Encode as base64url without padding
        encoded = base64.urlsafe_b64encode(signature).decode('ascii')
        return encoded.rstrip('=')
    
    def _is_expired(self, exp: int) -> bool:
        """Check if token has expired.
        
        Args:
            exp: Expiration timestamp (Unix time)
            
        Returns:
            True if token has expired
        """
        return time.time() > exp