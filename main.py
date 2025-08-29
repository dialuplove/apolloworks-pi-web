"""FastAPI HLS streaming server with token authentication."""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from deps import validate_token


# Environment configuration
EDGE_SIGNING_SECRET = os.getenv('EDGE_SIGNING_SECRET')
HLS_ROOT = os.getenv('HLS_ROOT', '/var/hulagirl/live')


def validate_environment():
    """Validate required environment variables and configuration."""
    if not EDGE_SIGNING_SECRET:
        print("ERROR: EDGE_SIGNING_SECRET environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    hls_path = Path(HLS_ROOT)
    if not hls_path.exists():
        print(f"ERROR: HLS_ROOT directory does not exist: {HLS_ROOT}", file=sys.stderr)
        sys.exit(1)
    
    if not hls_path.is_dir():
        print(f"ERROR: HLS_ROOT is not a directory: {HLS_ROOT}", file=sys.stderr)
        sys.exit(1)


# Validate environment on startup
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
async def serve_m3u8(request: Request):
    """Serve HLS manifest file with token validation.
    
    Args:
        request: FastAPI request object
        
    Returns:
        FileResponse: The m3u8 file with appropriate headers
        
    Raises:
        HTTPException: If token validation fails or file not found
    """
    # Validate token
    await validate_token_dependency(request, "/live/stream.m3u8")
    
    # Serve file
    file_path = Path(HLS_ROOT) / "stream.m3u8"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-store"}
    )


@app.get("/live/{segment}.ts")
async def serve_ts_segment(segment: str, request: Request):
    """Serve HLS transport stream segment with token validation.
    
    Args:
        segment: Segment filename (without .ts extension)
        request: FastAPI request object
        
    Returns:
        FileResponse: The .ts file with appropriate headers
        
    Raises:
        HTTPException: If token validation fails or file not found
    """
    # Construct request path for validation
    request_path = f"/live/{segment}.ts"
    
    # Validate token
    await validate_token_dependency(request, request_path)
    
    # Serve file
    file_path = Path(HLS_ROOT) / f"{segment}.ts"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp2t",
        headers={"Cache-Control": "public, max-age=10, immutable"}
    )


async def validate_token_dependency(request: Request, request_path: str):
    """Helper function to validate token from request query parameters.
    
    Args:
        request: FastAPI request object
        request_path: The request path for signature validation
        
    Raises:
        HTTPException: If token validation fails
    """
    # Extract query parameters
    exp = request.query_params.get('exp')
    sig = request.query_params.get('sig')
    
    # Check for missing parameters
    if exp is None or sig is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_parameters"}
        )
    
    try:
        exp = int(exp)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_expiration"}
        )
    
    # Use dependency injection for validation
    validate_token(request_path, exp, sig)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)