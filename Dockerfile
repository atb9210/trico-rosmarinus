# Multi-stage build for frontend + backend in one container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for backend
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ /app/

# Set environment variables (can be overridden by Dokploy)
ENV WORLDFILIA_API_KEY=cDLJTb14RzaP7SzsLfdP7Q
ENV WORLDFILIA_SOURCE_ID=57308485b8777
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

# Copy frontend files to nginx directory
COPY . /var/www/html/

# Configure nginx to serve frontend and proxy API requests
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    \
    # Frontend static files \
    location / { \
        root /var/www/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
        add_header Pragma "no-cache"; \
        add_header Expires "0"; \
    } \
    \
    # API proxy to backend \
    location /api/ { \
        proxy_pass http://localhost:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_connect_timeout 30s; \
        proxy_send_timeout 30s; \
        proxy_read_timeout 30s; \
    } \
    \
    # Health check endpoint \
    location /health { \
        proxy_pass http://localhost:8000/health; \
    } \
}' > /etc/nginx/sites-available/default

# Remove default nginx config
RUN rm /etc/nginx/sites-enabled/default

# Create startup script
RUN echo '#!/bin/bash \
echo "Starting Trico Rosmarinus API..." \
\
# Start FastAPI backend in background \
uvicorn main:app --host 0.0.0.0 --port 8000 & \
\
# Wait for backend to start \
sleep 2 \
\
# Test backend health \
curl -f http://localhost:8000/health || exit 1 \
\
echo "Backend is healthy, starting nginx..." \
\
# Start nginx in foreground \
nginx -g "daemon off;"' > /start.sh && chmod +x /start.sh

# Create nginx log directory
RUN mkdir -p /var/log/nginx

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start both services
CMD ["/start.sh"]
