# NeighborNet AI — Production Deployment Guide (Phase 5)

## 1. Overview & Architecture

NeighborNet AI is architected for containerized deployment using Docker Compose or standalone Linux servers. It requires:
- **Backend**: Python 3.13 + Django 6.1 + Gunicorn
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **Frontend**: Nginx serving pre-built Vite React application or static files
- **Cache/Broker (Optional)**: Redis for background optimization worker tasks

No paid proprietary cloud services are required. The entire stack can run on on-premise hardware, standard Linux VPS, or zero-cost hosting tiers.

---

## 2. Environment Configuration (`.env.production`)

Create `.env.production` in the project root:

```ini
# Django Core Settings
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=generate-a-strong-random-50-character-secret-key-here
DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost,127.0.0.1

# Database Configuration (PostgreSQL with PostGIS)
DB_ENGINE=django.contrib.gis.db.backends.postgis
DB_NAME=neighbornet_db
DB_USER=neighbornet_user
DB_PASSWORD=strong-production-db-password
DB_HOST=postgres
DB_PORT=5432

# CORS & CSRF Trusted Origins
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Frontend Configuration
VITE_DATA_SOURCE=api
VITE_API_URL=https://yourdomain.com/api/v1
```

---

## 3. Docker Compose Production Deployment

The repository includes a production-ready `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:16-3.4
    container_name: neighbornet_db
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME:-neighbornet_db}
      POSTGRES_USER: ${DB_USER:-neighbornet_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-neighbornet_user} -d ${DB_NAME:-neighbornet_db}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: neighbornet_backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env.production
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"
    ports:
      - "8000:8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: neighbornet_frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/usr/share/nginx/html/static:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  pgdata:
  static_volume:
  media_volume:
```

### Launch Commands:
```bash
# 1. Build and launch containers in background
docker compose up -d --build

# 2. Verify container health
docker compose ps

# 3. View backend logs
docker compose logs -f backend
```

---

## 4. Bare-Metal / Standard Linux VPS Deployment

For deployment directly on an Ubuntu/Debian server:

### Step 1: System Packages & PostGIS
```bash
sudo apt update && sudo apt install -y python3.13 python3.13-venv python3-pip postgresql-16 postgresql-16-postgis-3 nginx
```

### Step 2: Database Initialization
```bash
sudo -u postgres psql -c "CREATE USER neighbornet_user WITH PASSWORD 'strong-db-password';"
sudo -u postgres psql -c "CREATE DATABASE neighbornet_db OWNER neighbornet_user;"
sudo -u postgres psql -d neighbornet_db -c "CREATE EXTENSION postgis;"
```

### Step 3: Backend Setup
```bash
cd /opt/neighbornet/backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 4: Frontend Build
```bash
cd /opt/neighbornet/frontend
npm ci
npm run build
# Copy dist files to web server root:
sudo cp -r dist/* /var/www/neighbornet/
```

### Step 5: Systemd Gunicorn Service (`/etc/systemd/system/neighbornet.service`)
```ini
[Unit]
Description=NeighborNet AI Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/neighbornet/backend
Environment="PATH=/opt/neighbornet/backend/venv/bin"
EnvironmentFile=/opt/neighbornet/.env.production
ExecStart=/opt/neighbornet/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now neighbornet.service
```

---

## 5. Health Checks & Verification

- **System Diagnostics**:
  ```bash
  python manage.py check --deploy
  ```
- **Live Health Endpoint**:
  ```bash
  curl -i http://localhost:8000/api/v1/health/
  # Expected: HTTP 200 OK {"status": "healthy", "database": "connected"}
  ```

---

## 6. Safe Backup & Disaster Recovery

- **Automated Nightly Backup**:
  ```bash
  pg_dump -U neighbornet_user -h localhost -d neighbornet_db -F c -b -v -f /backups/neighbornet_$(date +%Y%m%d).dump
  ```
- **Database Restoration**:
  ```bash
  pg_restore -U neighbornet_user -h localhost -d neighbornet_db -v /backups/neighbornet_20261015.dump
  ```
