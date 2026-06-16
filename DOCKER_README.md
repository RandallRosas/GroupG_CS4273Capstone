# Docker Deployment Guide

Complete offline deployment guide for the EMS Call Analysis Tool. All models are pre-downloaded during image build, so deployment requires no internet connection.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Build Images (One-Time, Online)](#build-images-one-time-online)
- [Deploy (Offline)](#deploy-offline)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **System Requirements:**
  - CPU: Modern CPU with 8+ cores.
  - RAM: 64GB+ Recommended
  - Disk: ~60GB for images (all models included)
- **Ports:** 3000 (frontend), 5001 (backend)

---

## Build Images (One-Time, Online)

**Note:** This step requires internet connection and is done once. The resulting images contain all models and can be deployed offline.

### Build All Services

```bash
cd GroupG_CS4273Capstone
docker-compose build
```

**Build time:** 20-30 minutes (downloads all models: WhisperX ~3GB, Ollama ~4.7GB, SentenceTransformer ~90MB)

### Save Images for Offline Deployment

```bash
# Save images to tar files
docker save callanalysistool-backend:latest | gzip > backend-image.tar.gz
docker save callanalysistool-frontend:latest | gzip > frontend-image.tar.gz

# Or use docker-compose
docker-compose save | gzip > all-images.tar.gz
```

### Load Images on Target Machine

```bash
# Load images (no internet required)
docker load < backend-image.tar.gz
docker load < frontend-image.tar.gz

# Or from single archive
gunzip -c all-images.tar.gz | docker load
```

---

## Deploy (Offline)

### Start Services

```bash
cd GroupG_CS4273Capstone
docker-compose up -d
```

### Verify Deployment

```bash
# Check services
docker-compose ps

# Test backend
curl http://localhost:5001/api/health

# Open frontend
# http://localhost:3000
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

---

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
services:
  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=http://your-backend-url:5001
  
  backend:
    environment:
      - FLASK_ENV=production
      - OLLAMA_HOST=http://localhost:11434
      - DOCKER_CONTAINER=true
      # Offline mode (models pre-downloaded)
      - TRANSFORMERS_OFFLINE=1
      - HF_HUB_OFFLINE=1
```

### Data Persistence

Volumes are mounted from host:

- `./backend/data:/app/data:ro` - Protocol questions (read-only)
- `./backend/output:/app/output` - Transcription results (read-write)

Access data:

```bash
# View output
ls -la CallAnalysisTool/backend/output/

# Container shell
docker-compose exec backend bash
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :5001  # Mac/Linux
netstat -ano | findstr :5001  # Windows

# Change port in docker-compose.yml or stop conflicting service
```

### Services Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
```

### Ollama Not Ready

```bash
# Verify model loaded
docker-compose exec backend ollama list

# Restart if needed
docker-compose restart backend
```

### Frontend Can't Connect

1. Verify backend: `curl http://localhost:5001/api/health`
2. Check `NEXT_PUBLIC_API_URL` in docker-compose.yml
3. Review browser console for errors

### Out of Memory/Disk

```bash
# Clean Docker
docker system prune -a
docker volume prune

# Check usage
docker system df
docker stats
```

### Performance

- **Slow transcription:** CPU-only inference (expected)
- **High memory:** Models use 40-60GB combined (normal)
- Monitor: `docker stats`
