"""FastAPI dependencies for token validation."""

import os
from auth import TokenValidator


# Global validator instance
_validator: TokenValidator = None


def get_token_validator() -> TokenValidator:
    """Get the global token validator instance.
    
    Returns:
        TokenValidator instance
        
    Raises:
        RuntimeError: If validator is not initialized
    """
    global _validator
    if _validator is None:
        signing_secret = os.getenv('EDGE_SIGNING_SECRET')
        if not signing_secret:
            raise RuntimeError("EDGE_SIGNING_SECRET environment variable is required")
        _validator = TokenValidator(signing_secret)
    return _validator