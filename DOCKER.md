# HardRAG API - Docker Deployment

## Build and Run

### Local Development

```bash
# Start with docker-compose
docker-compose up

# Or build and run manually
docker build -t hardrag-api .
docker run -p 8000:8000 --env-file .env hardrag-api
```

API will be available at `http://localhost:8000`

### Production

```bash
# Build for production
docker build -t hardrag-api:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  --name hardrag-api \
  --env-file .env.production \
  --restart unless-stopped \
  hardrag-api:latest
```

## Environment Variables

Required environment variables (set in `.env`):

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Logs

```bash
# View logs
docker logs hardrag-api

# Follow logs
docker logs -f hardrag-api
```

## Deployment Platforms

### Railway

1. Create new project on Railway
2. Connect GitHub repo
3. Set environment variables
4. Deploy automatically

### Render

1. Create new Web Service
2. Connect GitHub repo
3. Set environment variables
4. Deploy

### Docker Hub

```bash
# Tag image
docker tag hardrag-api:latest yourusername/hardrag-api:latest

# Push to Docker Hub
docker push yourusername/hardrag-api:latest
```

## Performance

- **Cold start**: ~2-3 seconds
- **Average response time**: 50-200ms (depending on guardrails)
- **Memory usage**: ~300MB
- **Recommended**: 512MB RAM minimum, 1GB for production
