# Stage 1: build the frontend
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

# Stage 2: python runtime, serves API + built frontend as one service
FROM python:3.11-slim
WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY --from=frontend /build/dist frontend/dist

WORKDIR /srv/backend
EXPOSE 8000
# --proxy-headers + --forwarded-allow-ips: behind Render/Railway's proxy,
# request.client must be the real visitor IP or rate limiting is useless.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
