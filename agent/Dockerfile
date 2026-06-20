# Always-on agent host (Render/Railway/Fly). Includes git (FDE clone) + node
# (FDE validate + vercel CLI). Browserbase needs only the playwright package
# (the browser runs remotely), so no chromium download.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# git for the GitHub FDE clone; node + npm for FDE validate / vercel CLI.
RUN apt-get update \
  && apt-get install -y --no-install-recommends git curl ca-certificates \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt playwright

COPY . .

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
