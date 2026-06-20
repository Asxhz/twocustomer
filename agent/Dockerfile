# TwoCustomer control plane (FastAPI + Claude loop).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# uv for fast installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache \
    "fastapi>=0.115" "uvicorn[standard]>=0.32" "anthropic>=0.40" "httpx>=0.27" \
    "pydantic>=2.9" "pydantic-settings>=2.5" "python-dotenv>=1.0" \
    "sse-starlette>=2.1" "apscheduler>=3.10" "python-multipart>=0.0.9"

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
