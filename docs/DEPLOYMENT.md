# Deployment Guide - Google Cloud Run

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud CLI** installed and configured
3. **Docker** installed locally
4. **OpenAI API Key** for AI processing

## Setup Google Cloud

### 1. Install Google Cloud CLI

```bash
# Download and install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init
```

### 2. Enable Required APIs

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry API (if using)
gcloud services enable containerregistry.googleapis.com
```

### 3. Set Project

```bash
# List projects
gcloud projects list

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Environment Variables

### Local Development

Create a `.env` file:

```bash
cp env.example .env
```

Edit `.env` with your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Production (Google Cloud Run)

Set environment variables in Google Cloud Run:

```bash
gcloud run services update ai-invoice-agent \
  --set-env-vars OPENAI_API_KEY=sk-your-openai-api-key-here \
  --region us-central1
```

**⚠️ Security Note:** For production, use Google Secret Manager:

```bash
# Create secret
echo -n "sk-your-openai-api-key-here" | gcloud secrets create openai-api-key --data-file=-

# Grant access to Cloud Run service
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Deployment

### Option 1: Direct Deploy (Recommended)

```bash
# Deploy to Cloud Run
gcloud run deploy ai-invoice-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --max-instances 10
```

### Option 2: Build and Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-invoice-agent

# Deploy image
gcloud run deploy ai-invoice-agent \
  --image gcr.io/YOUR_PROJECT_ID/ai-invoice-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Configuration Options

### Resource Limits

```bash
gcloud run deploy ai-invoice-agent \
  --memory 2Gi \          # Memory limit
  --cpu 2 \               # CPU allocation
  --timeout 300 \         # Request timeout (seconds)
  --concurrency 80 \      # Concurrent requests per instance
  --max-instances 10      # Maximum instances
```

### Environment Variables

```bash
gcloud run deploy ai-invoice-agent \
  --set-env-vars \
    ENVIRONMENT=production,\
    AI_PROVIDER=openai,\
    MAX_FILE_SIZE=10485760
```

## Monitoring

### View Logs

```bash
# View recent logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-invoice-agent" --limit 50

# Stream logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=ai-invoice-agent"
```

### Metrics

Access Cloud Run metrics in Google Cloud Console:

- **CPU Utilization**
- **Memory Utilization**
- **Request Count**
- **Request Latency**
- **Error Rate**

## Scaling

### Automatic Scaling

Cloud Run automatically scales based on:

- **CPU utilization**
- **Memory usage**
- **Request volume**

### Manual Scaling

```bash
# Set minimum instances (always running)
gcloud run services update ai-invoice-agent \
  --min-instances 1 \
  --region us-central1

# Set maximum instances
gcloud run services update ai-invoice-agent \
  --max-instances 20 \
  --region us-central1
```

## Security

### Authentication

```bash
# Require authentication
gcloud run services update ai-invoice-agent \
  --no-allow-unauthenticated \
  --region us-central1
```

### IAM Roles

```bash
# Grant specific users access
gcloud run services add-iam-policy-binding ai-invoice-agent \
  --member="user:user@example.com" \
  --role="roles/run.invoker" \
  --region us-central1
```

## Troubleshooting

### Common Issues

1. **Build Failures**

   ```bash
   # Check build logs
   gcloud builds log BUILD_ID
   ```

2. **Runtime Errors**

   ```bash
   # Check service logs
   gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-invoice-agent" --limit 100
   ```

3. **Memory Issues**
   ```bash
   # Increase memory
   gcloud run services update ai-invoice-agent \
     --memory 4Gi \
     --region us-central1
   ```

### Health Checks

```bash
# Test health endpoint
curl https://ai-invoice-agent-xyz.run.app/health

# Test readiness
curl https://ai-invoice-agent-xyz.run.app/health/ready
```

## Cost Optimization

### Resource Tuning

```bash
# Optimize for cost
gcloud run deploy ai-invoice-agent \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --concurrency 100
```

### Monitoring Costs

```bash
# View cost breakdown
gcloud billing accounts list
gcloud billing projects describe YOUR_PROJECT_ID
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v0
        with:
          service: ai-invoice-agent
          region: us-central1
          image: gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-invoice-agent
```
