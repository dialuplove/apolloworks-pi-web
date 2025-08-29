# Use Python 3.11 slim image for ARM64
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py token.py deps.py ./

# Create HLS mount point directory
RUN mkdir -p /var/hulagirl/live && chown app:app /var/hulagirl/live

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check using the /healthz endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

# Set default environment variables
ENV HLS_ROOT=/var/hulagirl/live
ENV PORT=8000
ENV HOST=0.0.0.0

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]