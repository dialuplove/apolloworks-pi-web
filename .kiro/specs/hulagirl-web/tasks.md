# Implementation Plan

- [x] 1. Set up project structure and core token validator


  - Create project directory structure with main.py, token.py, deps.py, tests/, Dockerfile, README
  - Implement TokenValidator class with HMAC-SHA256 signature computation using unpadded base64url encoding
  - Ensure path normalization to lowercase and signature computation excludes host/query parameters
  - _Requirements: 4.4, 4.5, 4.6, 5.1, 5.2_

- [x] 2. Implement and test token validation logic

- [x] 2.1 Create TokenValidator with signature computation

  - Write TokenValidator class with validate_request() method
  - Implement _compute_signature() using HMAC-SHA256 and unpadded base64url encoding
  - Implement _is_expired() method for time-based validation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 2.2 Write comprehensive unit tests for token validator


  - Test valid signature computation with various paths and expiration times
  - Test invalid signature rejection with tampered signatures
  - Test expired token rejection with past timestamps
  - Test path normalization to lowercase for signature computation
  - Test unpadded base64url encoding compliance
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 3. Create FastAPI application with dependency injection

- [x] 3.1 Implement dependency injection for token validation


  - Create deps.py with get_token_validator() dependency
  - Implement token parameter extraction from query string
  - Handle missing parameters with 400 Bad Request response
  - _Requirements: 4.1, 8.1_

- [x] 3.2 Implement main FastAPI application structure


  - Create main.py with FastAPI app initialization
  - Implement environment variable validation for EDGE_SIGNING_SECRET and HLS_ROOT
  - Set up application startup validation and error handling
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 4. Implement health endpoint

  - Create GET /healthz endpoint returning {"ok": true} with 200 status
  - Ensure no authentication required for health checks
  - Write unit tests for health endpoint response
  - _Requirements: 1.1, 1.2_

- [x] 5. Implement HLS manifest serving

- [x] 5.1 Create m3u8 file serving endpoint

  - Implement GET /live/stream.m3u8 with token validation dependency
  - Serve files from HLS_ROOT with read-only access
  - Set Content-Type to application/vnd.apple.mpegurl
  - Set Cache-Control to no-store
  - Handle file not found with 404 response
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5.2 Write tests for m3u8 serving


  - Test successful file serving with valid tokens
  - Test proper Content-Type and Cache-Control headers
  - Test 404 response for missing files
  - Test authentication error responses (410 expired, 403 forbidden)
  - _Requirements: 7.5, 7.6, 7.7_

- [x] 6. Implement transport stream segment serving

- [x] 6.1 Create .ts file serving endpoint

  - Implement GET /live/{segment}.ts with token validation dependency
  - Serve .ts files from HLS_ROOT with read-only access
  - Set Content-Type to video/mp2t
  - Set Cache-Control to "public, max-age=10, immutable"
  - Handle file not found with 404 response
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6.2 Write tests for .ts file serving

  - Test successful segment serving with valid tokens
  - Test proper Content-Type and Cache-Control headers for .ts files
  - Test 404 response for missing segment files
  - Test authentication error responses with various token scenarios
  - _Requirements: 7.5, 7.6, 7.7_

- [x] 7. Create integration tests with temporary HLS directory

  - Set up temporary HLS directory with sample .m3u8 and .ts files
  - Test complete request flow from authentication to file serving
  - Test all HTTP status codes (200, 400, 403, 404, 410)
  - Verify all Content-Type and Cache-Control headers are set correctly
  - _Requirements: 7.5, 7.6, 7.7_

- [x] 8. Implement containerization

- [x] 8.1 Create ARM64 Dockerfile


  - Use python:3.11-slim base image for ARM64
  - Install uvicorn[standard] and application dependencies
  - Create non-root user for application execution
  - Set up read-only volume mount point for HLS_ROOT
  - Configure /healthz endpoint for container health checks
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8.2 Write container build and deployment documentation


  - Document container build process with ARM64 support
  - Provide example docker run commands with read-only HLS_ROOT mount
  - Document required environment variables and their usage
  - Include health check configuration examples
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 9. Create comprehensive documentation


  - Write README with setup, configuration, and run instructions
  - Document token generation process for testing and integration
  - Provide example environment variable configurations
  - Include API endpoint documentation with request/response examples
  - _Requirements: 8.1, 8.2, 8.3, 8.4_