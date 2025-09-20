# Multi-stage build for optimal image size
FROM python:3.11-slim as backend-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Frontend builder stage
FROM node:20-alpine as frontend-builder

WORKDIR /app

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 qwencoder && \
    mkdir -p /app /home/qwencoder/.cache && \
    chown -R qwencoder:qwencoder /app /home/qwencoder/.cache

WORKDIR /app

# Copy Python packages from builder
COPY --from=backend-builder --chown=qwencoder:qwencoder /root/.local /home/qwencoder/.local

# Copy backend code
COPY --chown=qwencoder:qwencoder backend/ ./backend/
COPY --chown=qwencoder:qwencoder model_service/ ./model_service/
COPY --chown=qwencoder:qwencoder terminal_service/ ./terminal_service/

# Copy built frontend
COPY --from=frontend-builder --chown=qwencoder:qwencoder /app/.next ./frontend/.next
COPY --from=frontend-builder --chown=qwencoder:qwencoder /app/public ./frontend/public
COPY --from=frontend-builder --chown=qwencoder:qwencoder /app/package.json ./frontend/

# Switch to non-root user
USER qwencoder

# Set environment variables
ENV PATH="/home/qwencoder/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV MODEL_CACHE_DIR="/home/qwencoder/.cache/huggingface"

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start script
COPY --chown=qwencoder:qwencoder docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]