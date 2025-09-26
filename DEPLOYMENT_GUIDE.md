# 🚀 Deployment Guide - Production Setup

## Overview

Complete deployment guide for the grocery price scraper platform across different environments and cloud providers.

## 🏗️ Architecture Overview

### Production Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │  Container Orch │    │   Data Storage  │
│                 │    │                 │    │                 │
│  • SSL Term     │◄──►│  • Frontend     │◄──►│  • MongoDB      │
│  • Rate Limit   │    │  • Backend API  │    │  • File Storage │
│  • Health Check │    │  • Workers      │    │  • Backups      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Monitoring    │              │
         └──────────────►│                 │◄─────────────┘
                        │ • Logs          │
                        │ • Metrics       │
                        │ • Alerts        │
                        └─────────────────┘
```

## 🐳 Docker Deployment

### 1. Dockerfile - Backend
```dockerfile
# /app/Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY backend/ ./backend/
COPY grocery_price_scraper/ ./grocery_price_scraper/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/test || exit 1

# Run application
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Dockerfile - Frontend
```dockerfile
# /app/Dockerfile.frontend
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source code
COPY frontend/ .

# Build application
RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: grocery-mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: grocery_scraper
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    ports:
      - "27017:27017"
    networks:
      - grocery-network

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: grocery-backend
    restart: unless-stopped
    environment:
      MONGO_URL: mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/grocery_scraper?authSource=admin
      DB_NAME: grocery_scraper
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    networks:
      - grocery-network
    volumes:
      - ./grocery_price_scraper/data:/app/grocery_price_scraper/data
      - ./logs:/app/logs

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: grocery-frontend
    restart: unless-stopped
    environment:
      REACT_APP_BACKEND_URL: ${BACKEND_URL}
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - grocery-network

  redis:
    image: redis:7-alpine
    container_name: grocery-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - grocery-network
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:

networks:
  grocery-network:
    driver: bridge
```

### 4. Environment Configuration
```bash
# .env.production
MONGO_PASSWORD=your_secure_mongo_password
JWT_SECRET_KEY=your_super_secure_jwt_secret_key_minimum_32_chars
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

### 5. Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    server {
        listen 80;
        server_name _;

        # Frontend routes
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Add security headers
            add_header X-Frame-Options "SAMEORIGIN" always;
            add_header X-XSS-Protection "1; mode=block" always;
            add_header X-Content-Type-Options "nosniff" always;
        }

        # API routes
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout settings
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

## ☁️ Cloud Deployment

### 1. AWS Deployment

#### ECS Fargate Setup
```yaml
# aws-ecs-task-definition.json
{
  "family": "grocery-scraper",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/grocery-backend:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGO_URL",
          "value": "mongodb+srv://user:pass@cluster.mongodb.net/grocery_scraper"
        }
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:jwt-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/grocery-scraper",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### CloudFormation Template
```yaml
# cloudformation-template.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Grocery Price Scraper Infrastructure'

Parameters:
  DomainName:
    Type: String
    Default: yourdomain.com
  
  CertificateArn:
    Type: String
    Description: SSL Certificate ARN

Resources:
  # VPC and Networking
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: grocery-scraper-alb
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: grocery-scraper-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      ServiceName: grocery-scraper-service
      TaskDefinition: !Ref ECSTaskDefinition
      LaunchType: FARGATE
      DesiredCount: 2
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref ECSSecurityGroup
          Subnets:
            - !Ref PublicSubnet1
            - !Ref PublicSubnet2
          AssignPublicIp: ENABLED

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
```

### 2. Google Cloud Deployment

#### Cloud Run Setup
```yaml
# cloud-run-backend.yml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: grocery-backend
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/grocery-backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: mongo-url
              key: url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: key
        resources:
          limits:
            cpu: 2
            memory: 4Gi
```

#### Terraform Configuration
```hcl
# terraform/main.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_run_service" "backend" {
  name     = "grocery-backend"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/grocery-backend:latest"
        
        ports {
          container_port = 8001
        }

        env {
          name = "MONGO_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret_version.mongo_url.secret
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "4Gi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_domain_mapping" "backend" {
  location = var.region
  name     = "api.${var.domain_name}"

  spec {
    route_name = google_cloud_run_service.backend.name
  }
}

# Frontend - Cloud Storage + CDN
resource "google_storage_bucket" "frontend" {
  name     = "${var.project_id}-frontend"
  location = "US"

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_compute_backend_bucket" "frontend" {
  name        = "frontend-backend"
  bucket_name = google_storage_bucket.frontend.name
}
```

### 3. Kubernetes Deployment

#### Kubernetes Manifests
```yaml
# k8s/namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: grocery-scraper

---
# k8s/configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: grocery-scraper
data:
  CORS_ORIGINS: "https://yourdomain.com"
  DB_NAME: "grocery_scraper"

---
# k8s/secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: grocery-scraper
type: Opaque
data:
  MONGO_URL: <base64-encoded-mongo-url>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>

---
# k8s/backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: grocery-scraper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/grocery-backend:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /api/test
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/test
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
# k8s/backend-service.yml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: grocery-scraper
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8001
  type: ClusterIP

---
# k8s/frontend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: grocery-scraper
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/grocery-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

---
# k8s/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: grocery-scraper
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: app-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
```

## 🔧 Configuration Management

### 1. Environment-Specific Configs

#### Production Environment
```bash
# .env.production
NODE_ENV=production
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/grocery_scraper
JWT_SECRET_KEY=super_secure_production_key_minimum_32_characters
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=info
RATE_LIMIT_MAX=1000
RATE_LIMIT_WINDOW=3600
```

#### Staging Environment
```bash
# .env.staging
NODE_ENV=staging
MONGO_URL=mongodb+srv://user:password@staging-cluster.mongodb.net/grocery_scraper_staging
JWT_SECRET_KEY=staging_jwt_secret_key_minimum_32_characters
CORS_ORIGINS=https://staging.yourdomain.com
LOG_LEVEL=debug
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=3600
```

### 2. Configuration Validation
```python
# backend/config.py
import os
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    mongo_url: str
    db_name: str = "grocery_scraper"
    jwt_secret_key: str
    cors_origins: str = "http://localhost:3000"
    log_level: str = "info"
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters')
        return v
    
    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.cors_origins.split(',')]

    class Config:
        env_file = ".env"

settings = Settings()
```

## 📊 Monitoring & Logging

### 1. Prometheus + Grafana Setup
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'grocery-backend'
    static_configs:
      - targets: ['backend:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'grocery-frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/metrics'
    scrape_interval: 30s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Application Metrics
```python
# backend/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'HTTP request duration'
)

ACTIVE_SCRAPING_TASKS = Gauge(
    'active_scraping_tasks', 
    'Number of active scraping tasks'
)

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(), 
        media_type="text/plain"
    )
```

### 3. Centralized Logging
```yaml
# logging/filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
  - add_docker_metadata:
      host: "unix:///var/run/docker.sock"

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

setup.kibana:
  host: "kibana:5601"
```

## 🔒 Security Hardening

### 1. Network Security
```yaml
# Security Groups (AWS)
SecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Application security group
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        CidrIp: 0.0.0.0/0
      - IpProtocol: tcp
        FromPort: 80
        ToPort: 80
        CidrIp: 0.0.0.0/0
    SecurityGroupEgress:
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        CidrIp: 0.0.0.0/0
      - IpProtocol: tcp
        FromPort: 27017
        ToPort: 27017
        DestinationSecurityGroupId: !Ref DatabaseSecurityGroup
```

### 2. Application Security
```python
# backend/security.py
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer
import jwt
import hashlib
import secrets

security = HTTPBearer()

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Input validation
from pydantic import BaseModel, validator
import re

class SecureInput(BaseModel):
    @validator('*', pre=True)
    def sanitize_input(cls, v):
        if isinstance(v, str):
            # Basic XSS prevention
            v = re.sub(r'<script.*?</script>', '', v, flags=re.IGNORECASE)
            v = re.sub(r'javascript:', '', v, flags=re.IGNORECASE)
        return v

# HTTPS enforcement
@app.middleware("http")
async def https_redirect(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url, status_code=301)
    return await call_next(request)
```

## 🚀 CI/CD Pipeline

### 1. GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
    
    - name: Run tests
      run: |
        pytest backend/tests/
    
    - name: Setup Node
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install frontend dependencies
      run: |
        cd frontend && yarn install
    
    - name: Run frontend tests
      run: |
        cd frontend && yarn test --coverage

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Build and push backend image
      run: |
        docker build -f Dockerfile.backend -t grocery-backend .
        docker tag grocery-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/grocery-backend:latest
        aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com
        docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/grocery-backend:latest
    
    - name: Build and deploy frontend
      run: |
        cd frontend
        yarn build
        aws s3 sync build/ s3://${{ secrets.S3_BUCKET }} --delete
        aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} --paths "/*"
    
    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster grocery-scraper-cluster --service grocery-scraper-service --force-new-deployment
```

### 2. Deployment Scripts
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Starting deployment..."

# Build images
echo "📦 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend python scripts/migrate.py

# Deploy services
echo "🚢 Deploying services..."
docker-compose -f docker-compose.prod.yml up -d

# Health check
echo "🔍 Performing health check..."
sleep 30
curl -f http://localhost/api/test || exit 1

# Cleanup old images
echo "🧹 Cleaning up..."
docker system prune -f

echo "✅ Deployment completed successfully!"
```

## 📋 Maintenance & Backup

### 1. Database Backup Script
```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
MONGO_URI="mongodb://user:pass@localhost:27017/grocery_scraper"

echo "📦 Starting backup at $DATE"

# MongoDB backup
mongodump --uri="$MONGO_URI" --out="$BACKUP_DIR/mongo_$DATE"

# SQLite backup
cp /app/grocery_price_scraper/data/grocery_prices.db "$BACKUP_DIR/sqlite_$DATE.db"

# Compress backup
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" "$BACKUP_DIR/mongo_$DATE" "$BACKUP_DIR/sqlite_$DATE.db"

# Upload to cloud storage (AWS S3)
aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz" "s3://your-backup-bucket/backups/"

# Cleanup local backups older than 7 days
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: backup_$DATE.tar.gz"
```

### 2. Health Monitoring
```python
# scripts/health_check.py
import requests
import sys
import time

def check_health():
    endpoints = [
        {"url": "http://localhost/api/test", "name": "Backend API"},
        {"url": "http://localhost/", "name": "Frontend"},
        {"url": "http://localhost/api/auth/status", "name": "Auth System"}
    ]
    
    all_healthy = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint["url"], timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint['name']}: Healthy")
            else:
                print(f"❌ {endpoint['name']}: Unhealthy (Status: {response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"❌ {endpoint['name']}: Error - {str(e)}")
            all_healthy = False
    
    return all_healthy

if __name__ == "__main__":
    if check_health():
        print("🎉 All systems healthy!")
        sys.exit(0)
    else:
        print("🚨 Some systems are unhealthy!")
        sys.exit(1)
```

This comprehensive deployment guide covers all aspects of production deployment, from containerization to cloud deployment, monitoring, and maintenance.