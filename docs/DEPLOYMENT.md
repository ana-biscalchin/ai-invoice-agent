# 🚀 Deployment Guide - AI Invoice Agent

> **Guia de deploy para microserviço de agentes de IA em finanças pessoais**

## 📖 Contexto de Deploy

Este projeto de **estudo sobre agentes de IA** é projetado para deploy como microserviço stateless, preparado para integração em uma aplicação maior de gestão de finanças pessoais. O deploy pode ser feito em diversos ambientes, desde desenvolvimento local até produção cloud.

## 🎯 Estratégias de Deploy

### **Ambientes Suportados**

- **Local Development**: Docker Compose
- **Cloud Container**: Google Cloud Run, AWS Fargate
- **Kubernetes**: Qualquer cluster K8s
- **VPS Tradicional**: Docker + nginx proxy

### **Características do Deploy**

- ✅ **Stateless**: Sem persistência local
- ✅ **Container-first**: Dockerizado por padrão
- ✅ **Health checks**: Liveness e readiness
- ✅ **Environment-based config**: 12-factor app
- ✅ **Auto-scaling**: Horizontal scaling ready

## 🐳 Docker Deployment

### **Dockerfile Strategy**

```dockerfile
# Multi-stage build para otimizar tamanho
FROM python:3.11-slim as builder
# Build dependencies...

FROM python:3.11-slim as runtime
# Runtime dependencies apenas
COPY --from=builder /app /app
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Build Local**

```bash
# Build da imagem
docker build -t ai-invoice-agent:latest .

# Test local
docker run --env-file .env -p 8000:8000 ai-invoice-agent:latest

# Health check
curl http://localhost:8000/health
```

### **Docker Compose (Development)**

```yaml
# docker-compose.yml
version: "3.8"

services:
  ai-invoice-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DEFAULT_AI_PROVIDER=openai
    env_file:
      - .env
    volumes:
      - ./app:/app/app # Hot reload
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Opcional: nginx proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ai-invoice-agent
    restart: unless-stopped
```

### **Deploy Commands**

```bash
# Development
docker-compose up -d

# Production build
docker-compose -f docker-compose.prod.yml up -d

# Logs
docker-compose logs -f ai-invoice-agent

# Scale horizontalmente (se necessário)
docker-compose up -d --scale ai-invoice-agent=3
```

## ☁️ Cloud Deployment

### **Google Cloud Run**

#### **1. Setup**

```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### **2. Build & Deploy**

```bash
# Build na cloud
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-invoice-agent

# Deploy
gcloud run deploy ai-invoice-agent \
  --image gcr.io/YOUR_PROJECT_ID/ai-invoice-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 100 \
  --set-env-vars ENVIRONMENT=production,DEBUG=false \
  --set-env-vars DEFAULT_AI_PROVIDER=openai

# Configure secrets
gcloud run services update ai-invoice-agent \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --set-secrets DEEPSEEK_API_KEY=deepseek-key:latest
```

#### **3. Custom Domain (Opcional)**

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service ai-invoice-agent \
  --domain api.your-finance-app.com \
  --region us-central1
```

### **AWS Fargate**

#### **1. ECR Setup**

```bash
# Create repository
aws ecr create-repository --repository-name ai-invoice-agent

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t ai-invoice-agent .
docker tag ai-invoice-agent:latest \
  YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-invoice-agent:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-invoice-agent:latest
```

#### **2. ECS Task Definition**

```json
{
  "family": "ai-invoice-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ai-invoice-agent",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-invoice-agent:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "ENVIRONMENT", "value": "production" },
        { "name": "DEBUG", "value": "false" },
        { "name": "DEFAULT_AI_PROVIDER", "value": "openai" }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:openai-api-key"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-invoice-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### **3. Service & Load Balancer**

```bash
# Create service
aws ecs create-service \
  --cluster your-cluster \
  --service-name ai-invoice-agent \
  --task-definition ai-invoice-agent:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=YOUR_TG_ARN,containerName=ai-invoice-agent,containerPort=8000
```

## ⚓ Kubernetes Deployment

### **Deployment Manifest**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-invoice-agent
  labels:
    app: ai-invoice-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-invoice-agent
  template:
    metadata:
      labels:
        app: ai-invoice-agent
    spec:
      containers:
        - name: ai-invoice-agent
          image: your-registry/ai-invoice-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: ENVIRONMENT
              value: "production"
            - name: DEBUG
              value: "false"
            - name: DEFAULT_AI_PROVIDER
              value: "openai"
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: ai-provider-secrets
                  key: openai-api-key
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ai-invoice-agent-service
spec:
  selector:
    app: ai-invoice-agent
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-invoice-agent-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/client-max-body-size: "10m"
spec:
  tls:
    - hosts:
        - api.your-finance-app.com
      secretName: ai-invoice-agent-tls
  rules:
    - host: api.your-finance-app.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ai-invoice-agent-service
                port:
                  number: 80
```

### **Secrets Management**

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-provider-secrets
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  deepseek-api-key: <base64-encoded-key>
```

### **Deploy Commands**

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=ai-invoice-agent
kubectl get svc ai-invoice-agent-service
kubectl get ingress ai-invoice-agent-ingress

# Logs
kubectl logs -l app=ai-invoice-agent -f

# Scale
kubectl scale deployment ai-invoice-agent --replicas=5
```

## 🏗️ Infrastructure as Code

### **Terraform (AWS)**

```hcl
# terraform/main.tf
resource "aws_ecs_cluster" "ai_invoice_cluster" {
  name = "ai-invoice-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_service" "ai_invoice_agent" {
  name            = "ai-invoice-agent"
  cluster         = aws_ecs_cluster.ai_invoice_cluster.id
  task_definition = aws_ecs_task_definition.ai_invoice_agent.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.ai_invoice_agent.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ai_invoice_agent.arn
    container_name   = "ai-invoice-agent"
    container_port   = 8000
  }
}

resource "aws_lb_target_group" "ai_invoice_agent" {
  name     = "ai-invoice-agent-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}
```

### **Deploy Terraform**

```bash
# Initialize
terraform init

# Plan
terraform plan -var-file="production.tfvars"

# Apply
terraform apply -var-file="production.tfvars"

# Destroy (if needed)
terraform destroy -var-file="production.tfvars"
```

## 🔧 Environment Configuration

### **Environment Variables**

```bash
# Production Environment (.env.prod)
ENVIRONMENT=production
DEBUG=false

# AI Providers (pelo menos um obrigatório)
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-prod-key-here
DEEPSEEK_API_KEY=prod-key-here

# Performance & Security
MAX_FILE_SIZE=10485760
TIMEOUT_SECONDS=60
CORS_ORIGINS=https://your-finance-app.com

# Monitoring (opcional)
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
```

### **Secrets Management**

#### **Google Cloud Secret Manager**

```bash
# Create secrets
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-deepseek-key" | gcloud secrets create deepseek-api-key --data-file=-

# Grant access to Cloud Run
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### **AWS Secrets Manager**

```bash
# Create secrets
aws secretsmanager create-secret \
  --name "ai-invoice-agent/openai-api-key" \
  --secret-string "sk-your-openai-key"

aws secretsmanager create-secret \
  --name "ai-invoice-agent/deepseek-api-key" \
  --secret-string "your-deepseek-key"
```

#### **Kubernetes Secrets**

```bash
# Create from literal
kubectl create secret generic ai-provider-secrets \
  --from-literal=openai-api-key='sk-your-openai-key' \
  --from-literal=deepseek-api-key='your-deepseek-key'

# Create from file
kubectl create secret generic ai-provider-secrets \
  --from-file=openai-api-key=./openai-key.txt \
  --from-file=deepseek-api-key=./deepseek-key.txt
```

## 📊 Monitoring & Observability

### **Health Check Endpoints**

```python
# Configure load balancer health checks
# Liveness probe: GET /health
# Readiness probe: GET /health/ready
# Startup probe: GET /health (with longer timeout)
```

### **Application Metrics**

```python
# app/main.py - adicionar middleware de metrics
from prometheus_client import Counter, Histogram
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()

    REQUEST_DURATION.observe(time.time() - start_time)
    return response
```

### **Logging Configuration**

```python
# app/main.py - structured logging
import structlog
import logging

# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO if ENVIRONMENT == "production" else logging.DEBUG,
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.WriteLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

### **External Monitoring**

```python
# Sentry integration (opcional)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=ENVIRONMENT,
    )
```

## 🔒 Security Considerations

### **Container Security**

```dockerfile
# Dockerfile - security best practices
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy and install dependencies as root
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only=main

# Copy application code
COPY app/ ./app/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Network Security**

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-invoice-agent-netpol
spec:
  podSelector:
    matchLabels:
      app: ai-invoice-agent
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-system
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to: [] # Allow all outbound (AI APIs)
      ports:
        - protocol: TCP
          port: 443
```

### **API Security**

```python
# app/main.py - production security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.your-finance-app.com"]
    )

# Add security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## 🚀 CI/CD Pipeline

### **GitHub Actions**

```yaml
# .github/workflows/deploy.yml
name: Deploy AI Invoice Agent

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run tests
        run: poetry run pytest
      - name: Run linting
        run: |
          poetry run black --check app/
          poetry run ruff check app/

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Setup Google Cloud
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push to GCR
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-invoice-agent:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ai-invoice-agent \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-invoice-agent:${{ github.sha }} \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

## 📈 Scaling Considerations

### **Horizontal Scaling**

```python
# Stateless design permite easy horizontal scaling
# Auto-scaling baseado em:
# - CPU utilization (>70%)
# - Memory utilization (>80%)
# - Request latency (>2s)
# - Custom metrics (queue length, etc.)
```

### **Performance Optimization**

```python
# app/main.py - production optimizations
app = FastAPI(
    docs_url=None if ENVIRONMENT == "production" else "/docs",
    redoc_url=None if ENVIRONMENT == "production" else "/redoc",
)

# Configure uvicorn for production
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4 if ENVIRONMENT == "production" else 1,
        access_log=ENVIRONMENT != "production",
    )
```

## 🎓 Deployment Best Practices

### **Checklist de Deploy**

- ✅ **Secrets**: API keys em secret managers
- ✅ **Health checks**: Liveness e readiness configurados
- ✅ **Resource limits**: CPU/memory adequados
- ✅ **Security**: HTTPS, security headers, network policies
- ✅ **Monitoring**: Logs estruturados, metrics, alerts
- ✅ **Backup**: Strategy para disaster recovery
- ✅ **Testing**: Deploy em staging primeiro

### **Rollback Strategy**

```bash
# Google Cloud Run - rollback automático
gcloud run services replace-traffic ai-invoice-agent --to-revisions=PREVIOUS=100

# Kubernetes - rollback
kubectl rollout undo deployment/ai-invoice-agent

# AWS ECS - update service to previous task definition
aws ecs update-service --cluster your-cluster --service ai-invoice-agent --task-definition previous-version
```

---

Este guia de deploy prepara o **AI Invoice Agent** para produção como componente especializado em um sistema maior de gestão financeira, demonstrando boas práticas de DevOps e deployment de microserviços baseados em containers.
