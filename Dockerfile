FROM python:3.11-slim

# Working directory
WORKDIR /app

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install build dependencies, install Python deps, then remove build deps to keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc build-essential libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# Copy application source
COPY ./app ./app

# Create a non-root user and give ownership of /app
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

# Expose application port
EXPOSE 8000

# Healthcheck uses the app's /health endpoint (requests is in requirements)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests, sys; r = requests.get('http://localhost:8000/health'); sys.exit(0 if r.status_code==200 else 1)"

# Switch to non-root user
USER appuser

# Run with a single worker by default; the platform can scale instances
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
