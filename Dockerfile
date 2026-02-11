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

# Admin credentials
ENV ADMIN_USER=admin
ENV ADMIN_PASS=trico2026!
ENV DB_PATH=/app/data/trico.db

# Facebook Conversion API
ENV FB_PIXEL_ID=2095934291260128
ENV FB_ACCESS_TOKEN=EAAWzrJVNYx0BQr2wVNTXZB7E8YW0Sj2o9opMDcePaBAPkVLncJ55iyZC3Se74me2OGo3DhpGMfUCHHaYzeNefeHTsbsRYcJZBAzbVI6lQUhq9gZC3MuQkpP31NQyAJzKo6vp4tTqhDld9JuVWjsGgIcQcF0CLUZB1p1NquUZBnZCI0Pcl2l5CnDz9ccZAHoDcwZDZD

# Create data directory for SQLite
RUN mkdir -p /app/data
VOLUME /app/data

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
    # Trico 2x49 landing page \
    location /trico2x/ { \
        alias /var/www/html/trico2x/; \
        index index.html; \
        try_files $uri $uri/ /trico2x/index.html; \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
    } \
    \
    # Admin panel \
    location /admin { \
        alias /var/www/html; \
        try_files /admin.html =404; \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
    } \
    \
    # Health check endpoint \
    location /health { \
        proxy_pass http://localhost:8000/health; \
    } \
}' > /etc/nginx/sites-available/default

# Link nginx config
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create nginx log directory
RUN mkdir -p /var/log/nginx

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start both services
CMD ["/start.sh"]
