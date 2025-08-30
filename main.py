"""FastAPI HLS streaming server with token authentication."""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from deps import get_token_validator
from token import TokenValidator
from typing import Annotated


def get_hls_root():
    """Get the current HLS root directory."""
    return os.getenv('HLS_ROOT', '/var/hulagirl/live')


def validate_environment():
    """Validate required environment variables and configuration."""
    edge_secret = os.getenv('EDGE_SIGNING_SECRET')
    if not edge_secret:
        print("ERROR: EDGE_SIGNING_SECRET environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    hls_root = get_hls_root()
    hls_path = Path(hls_root)
    if not hls_path.exists():
        print(f"ERROR: HLS_ROOT directory does not exist: {hls_root}", file=sys.stderr)
        sys.exit(1)
    
    if not hls_path.is_dir():
        print(f"ERROR: HLS_ROOT is not a directory: {hls_root}", file=sys.stderr)
        sys.exit(1)


# Only validate environment if not in test mode
if not os.getenv('PYTEST_CURRENT_TEST'):
    validate_environment()

# Create FastAPI application
app = FastAPI(
    title="hulagirl-web",
    description="HLS streaming server with token authentication",
    version="1.0.0"
)


@app.get("/healthz")
async def health_check():
    """Health check endpoint for monitoring and container health checks.
    
    Returns:
        dict: Health status response
    """
    return {"ok": True}


@app.get("/live/stream.m3u8")
async def serve_m3u8(
    exp: Annotated[int, Query(description="Token expiration timestamp")] = None,
    sig: Annotated[str, Query(description="Token signature")] = None
):
    """Serve HLS manifest file with token validation.
    
    Args:
        exp: Expiration timestamp from query parameters
        sig: Signature from query parameters
        
    Returns:
        FileResponse: The m3u8 file with appropriate headers
        
    Raises:
        HTTPException: If token validation fails or file not found
    """
    # Validate token
    validate_token_for_path("/live/stream.m3u8", exp, sig)
    
    # Serve file
    file_path = Path(get_hls_root()) / "stream.m3u8"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-store"}
    )


@app.get("/live/{segment}.ts")
async def serve_ts_segment(
    segment: str,
    exp: Annotated[int, Query(description="Token expiration timestamp")] = None,
    sig: Annotated[str, Query(description="Token signature")] = None
):
    """Serve HLS transport stream segment with token validation.
    
    Args:
        segment: Segment filename (without .ts extension)
        exp: Expiration timestamp from query parameters
        sig: Signature from query parameters
        
    Returns:
        FileResponse: The .ts file with appropriate headers
        
    Raises:
        HTTPException: If token validation fails or file not found
    """
    # Construct request path for validation
    request_path = f"/live/{segment}.ts"
    
    # Validate token
    validate_token_for_path(request_path, exp, sig)
    
    # Serve file
    file_path = Path(get_hls_root()) / f"{segment}.ts"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp2t",
        headers={"Cache-Control": "public, max-age=10, immutable"}
    )


def validate_token_for_path(request_path: str, exp: int = None, sig: str = None):
    """Helper function to validate token parameters.
    
    Args:
        request_path: The request path for signature validation
        exp: Expiration timestamp from query parameters
        sig: Signature from query parameters
        
    Raises:
        HTTPException: If token validation fails
    """
    # Check for missing parameters
    if exp is None or sig is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_parameters"}
        )
    
    # Get validator and validate token
    validator = get_token_validator()
    result = validator.validate_request(request_path, exp, sig)
    
    if not result.is_valid:
        raise HTTPException(
            status_code=result.status_code,
            detail={"error": result.error_type}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)