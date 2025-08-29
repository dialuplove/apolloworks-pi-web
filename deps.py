"""FastAPI dependencies for token validation."""

import os
from typing import Annotated
from fastapi import Depends, HTTPException, Query
from token_validator import TokenValidator


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


def validate_token(
    request_path: str,
    exp: Annotated[int, Query(description="Token expiration timestamp")] = None,
    sig: Annotated[str, Query(description="Token signature")] = None,
    validator: TokenValidator = Depends(get_token_validator)
) -> None:
    """Validate token parameters for HLS requests.
    
    Args:
        request_path: The request path for signature validation
        exp: Expiration timestamp from query parameters
        sig: Signature from query parameters
        validator: Token validator dependency
        
    Raises:
        HTTPException: If token validation fails
    """
    # Check for missing parameters
    if exp is None or sig is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_parameters"}
        )
    
    # Validate token
    result = validator.validate_request(request_path, exp, sig)
    
    if not result.is_valid:
        raise HTTPException(
            status_code=result.status_code,
            detail={"error": result.error_type}
        )