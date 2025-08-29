# hulagirl-web

A FastAPI-based HLS (HTTP Live Streaming) server with HMAC-SHA256 token authentication. Serves HLS manifest files (.m3u8) and transport stream segments (.ts) with secure, time-limited access tokens.

## Features

- **Token-based Authentication**: HMAC-SHA256 signatures with expiration timestamps
- **HLS Support**: Serves .m3u8 manifest files and .ts segment files
- **Proper Caching**: Appropriate Cache-Control headers for different content types
- **Health Monitoring**: `/healthz` endpoint for container health checks
- **Security**: Read-only file access, non-root container execution
- **ARM64 Support**: Optimized for ARM64 architecture

## API Endpoints

### Health Check
```
GET /healthz
```
Returns: `{"ok": true}` (no authentication required)

### HLS Manifest
```
GET /live/stream.m3u8?exp=<timestamp>&sig=<signature>
```
- **Content-Type**: `application/vnd.apple.mpegurl`
- **Cache-Control**: `no-store`

### Transport Stream Segments
```
GET /live/{segment}.ts?exp=<timestamp>&sig=<signature>
```
- **Content-Type**: `video/mp2t`
- **Cache-Control**: `public, max-age=10, immutable`

## Token Authentication

All `/live/*` endpoints require token authentication via query parameters:

- `exp`: Unix timestamp for token expiration
- `sig`: HMAC-SHA256 signature (base64url encoded, unpadded)

### Signature Computation

```python
import hmac
import hashlib
import base64

def generate_signature(secret: str, path: str, exp: int) -> str:
    # Normalize path to lowercase
    normalized_path = path.lower()
    
    # Create message: path + exp
    message = f"{normalized_path}{exp}".encode('utf-8')
    
    # Compute HMAC-SHA256
    signature = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()
    
    # Encode as base64url without padding
    encoded = base64.urlsafe_b64encode(signature).decode('ascii')
    return encoded.rstrip('=')

# Example usage
secret = "your-edge-signing-secret"
path = "/live/stream.m3u8"
exp = 1640995200  # Unix timestamp
sig = generate_signature(secret, path, exp)
```

### Error Responses

- **400 Bad Request**: Missing or invalid parameters
  ```json
  {"error": "missing_parameters"}
  ```

- **403 Forbidden**: Invalid signature
  ```json
  {"error": "forbidden"}
  ```

- **410 Gone**: Expired token
  ```json
  {"error": "expired"}
  ```

- **404 Not Found**: File not found
  ```json
  {"detail": "File not found"}
  ```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EDGE_SIGNING_SECRET` | Yes | - | HMAC signing key for token validation |
| `HLS_ROOT` | No | `/var/hulagirl/live` | Directory containing HLS files |

### Example Configuration

```bash
export EDGE_SIGNING_SECRET="your-secret-key-here"
export HLS_ROOT="/path/to/hls/files"
```

## Development Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hulagirl-web
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export EDGE_SIGNING_SECRET="test-secret-key"
   export HLS_ROOT="/var/hulagirl/live"
   ```

4. Create test HLS files:
   ```bash
   mkdir -p /var/hulagirl/live
   echo "#EXTM3U" > /var/hulagirl/live/stream.m3u8
   echo "fake content" > /var/hulagirl/live/segment001.ts
   ```

5. Run the application:
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000`

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run with coverage
pip install pytest-cov
pytest --cov=. --cov-report=html
```

## Container Deployment

### Building the Container

```bash
# Build for ARM64
docker build --platform linux/arm64 -t hulagirl-web:latest .

# Build for current platform
docker build -t hulagirl-web:latest .
```

### Running the Container

```bash
# Basic run with environment variables
docker run -d \
  --name hulagirl-web \
  -p 8000:8000 \
  -e EDGE_SIGNING_SECRET="your-secret-key" \
  -v /path/to/hls/files:/var/hulagirl/live:ro \
  hulagirl-web:latest

# With custom HLS root
docker run -d \
  --name hulagirl-web \
  -p 8000:8000 \
  -e EDGE_SIGNING_SECRET="your-secret-key" \
  -e HLS_ROOT="/custom/hls/path" \
  -v /path/to/hls/files:/custom/hls/path:ro \
  hulagirl-web:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  hulagirl-web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - EDGE_SIGNING_SECRET=your-secret-key-here
      - HLS_ROOT=/var/hulagirl/live
    volumes:
      - /path/to/hls/files:/var/hulagirl/live:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    restart: unless-stopped
```

### Health Checks

The container includes a built-in health check that monitors the `/healthz` endpoint:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{json .State.Health}}' hulagirl-web
```

## Security Considerations

### Token Security

- Use a cryptographically secure random string for `EDGE_SIGNING_SECRET`
- Keep the signing secret confidential and rotate it regularly
- Set appropriate expiration times for tokens (not too long)
- Signatures include the full request path to prevent path traversal

### Container Security

- Runs as non-root user (`app:app`)
- HLS files mounted read-only
- Minimal base image (python:3.11-slim)
- No unnecessary system packages

### Example Secret Generation

```python
import secrets
import base64

# Generate a secure random secret
secret_bytes = secrets.token_bytes(32)
secret = base64.urlsafe_b64encode(secret_bytes).decode('ascii')
print(f"EDGE_SIGNING_SECRET={secret}")
```

## Monitoring and Logging

### Health Monitoring

```bash
# Check application health
curl http://localhost:8000/healthz

# Expected response
{"ok": true}
```

### Log Levels

The application logs important events:

- **INFO**: Normal operations, request handling
- **WARN**: Authentication failures, missing files  
- **ERROR**: Configuration issues, system errors

### Metrics

Consider integrating with monitoring systems to track:

- Request count and response times
- Authentication success/failure rates
- File serving performance
- Error rates by endpoint

## Troubleshooting

### Common Issues

1. **"EDGE_SIGNING_SECRET environment variable is required"**
   - Ensure the environment variable is set before starting the application

2. **"HLS_ROOT directory does not exist"**
   - Create the directory or update the `HLS_ROOT` environment variable
   - Ensure the directory is accessible by the application user

3. **403 Forbidden errors**
   - Verify signature computation matches the server implementation
   - Check that the path is normalized to lowercase
   - Ensure base64url encoding is unpadded

4. **410 Gone errors**
   - Check that the expiration timestamp is in the future
   - Verify system clocks are synchronized

5. **404 Not Found errors**
   - Ensure HLS files exist in the configured directory
   - Check file permissions and accessibility

### Debug Mode

For development, you can run with debug logging:

```bash
# Run with debug output
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import main
"
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]