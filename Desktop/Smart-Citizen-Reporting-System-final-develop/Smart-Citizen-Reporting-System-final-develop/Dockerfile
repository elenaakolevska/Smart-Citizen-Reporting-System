# Image is multi-GB because requirements.txt pulls in torch + transformers.
# Set AI_ENABLED=false at runtime to skip model warmup and cut cold-start latency.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python deps in their own layer so they cache when only app code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source after deps for better layer caching.
COPY app/ ./app/
COPY scripts/ ./scripts/

# Run as a non-root user. /app needs to be writable for the uploads/ dir
# the app creates on startup.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
