# Requirements Document

## Introduction

The hulagirl-web application is a FastAPI-based HTTP Live Streaming (HLS) server that provides secure access to live video streams. The application serves HLS manifest files (.m3u8) and transport stream segments (.ts) with token-based authentication and appropriate caching headers. It includes health monitoring endpoints and is designed for containerized deployment with ARM64 support.

## Requirements

### Requirement 1

**User Story:** As a monitoring system, I want to check the application health status, so that I can ensure the service is running properly.

#### Acceptance Criteria

1. WHEN a GET request is made to /healthz THEN the system SHALL return HTTP 200 with JSON response {"ok": true}
2. WHEN the health endpoint is accessed THEN the system SHALL respond without requiring authentication

### Requirement 2

**User Story:** As a video streaming client, I want to access HLS manifest files, so that I can initiate video playback.

#### Acceptance Criteria

1. WHEN a valid GET request is made to /live/stream.m3u8 with proper authentication THEN the system SHALL serve the file from /var/hulagirl/live/stream.m3u8
2. WHEN serving m3u8 files THEN the system SHALL set Content-Type header to application/vnd.apple.mpegurl
3. WHEN serving m3u8 files THEN the system SHALL set Cache-Control header to no-store
4. WHEN the requested m3u8 file does not exist THEN the system SHALL return HTTP 404

### Requirement 3

**User Story:** As a video streaming client, I want to access HLS transport stream segments, so that I can download and play video content.

#### Acceptance Criteria

1. WHEN a valid GET request is made to /live/{segment}.ts with proper authentication THEN the system SHALL serve the corresponding .ts file from /var/hulagirl/live/
2. WHEN serving .ts files THEN the system SHALL set Content-Type header to video/mp2t
3. WHEN serving .ts files THEN the system SHALL set Cache-Control header to "public, max-age=10, immutable"
4. WHEN the requested .ts file does not exist THEN the system SHALL return HTTP 404

### Requirement 4

**User Story:** As a content provider, I want to secure access to live streams with time-limited tokens, so that only authorized users can access the content within a specific timeframe.

#### Acceptance Criteria

1. WHEN a request is made to any /live/* endpoint THEN the system SHALL require exp and sig query parameters
2. WHEN the exp parameter represents a time in the past THEN the system SHALL return HTTP 410 with JSON {"error": "expired"}
3. WHEN the sig parameter does not match the computed signature THEN the system SHALL return HTTP 403 with JSON {"error": "forbidden"}
4. WHEN computing the signature THEN the system SHALL use HMAC-SHA256 with EDGE_SIGNING_SECRET and the exact lowercase request path plus exp value
5. WHEN encoding the signature THEN the system SHALL use base64url encoding without padding
6. WHEN the path for signature computation is used THEN it SHALL be the exact request path starting with "/live/" in lowercase

### Requirement 5

**User Story:** As a system administrator, I want to configure the application through environment variables, so that I can deploy it in different environments without code changes.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL read the EDGE_SIGNING_SECRET environment variable for token validation
2. WHEN the application starts THEN it SHALL read the HLS_ROOT environment variable with default value /var/hulagirl/live
3. WHEN HLS_ROOT is not accessible THEN the system SHALL log an error and fail to start
4. WHEN EDGE_SIGNING_SECRET is not provided THEN the system SHALL log an error and fail to start

### Requirement 6

**User Story:** As a system administrator, I want the application to run in a secure containerized environment, so that I can deploy it safely in production.

#### Acceptance Criteria

1. WHEN building the container THEN it SHALL use python:3.11-slim base image for ARM64 architecture
2. WHEN the container runs THEN it SHALL execute as a non-root user
3. WHEN the container starts THEN it SHALL use uvicorn with standard extras for serving the FastAPI application
4. WHEN the HLS_ROOT directory is mounted THEN it SHALL be mounted as read-only
5. WHEN container health is checked THEN it SHALL use the /healthz endpoint

### Requirement 7

**User Story:** As a developer, I want comprehensive test coverage, so that I can ensure the application works correctly and catch regressions.

#### Acceptance Criteria

1. WHEN running unit tests THEN the system SHALL test token validation with valid signatures
2. WHEN running unit tests THEN the system SHALL test token validation with invalid signatures
3. WHEN running unit tests THEN the system SHALL test token validation with expired tokens
4. WHEN running unit tests THEN the system SHALL test path normalization for signature computation
5. WHEN running integration tests THEN the system SHALL test file serving with a temporary HLS directory
6. WHEN running integration tests THEN the system SHALL test all endpoint responses and status codes
7. WHEN running integration tests THEN the system SHALL test proper Content-Type and Cache-Control headers

### Requirement 8

**User Story:** As a developer, I want clear documentation and setup instructions, so that I can understand how to run and deploy the application.

#### Acceptance Criteria

1. WHEN reviewing the project THEN it SHALL include a README file with run instructions
2. WHEN reviewing the project THEN it SHALL include example environment variable configurations
3. WHEN reviewing the project THEN it SHALL include container build and run commands
4. WHEN reviewing the project THEN it SHALL document the token generation process for testing