# 🚀 Worker Scaling Guide

This guide details the comprehensive setup for Celery worker scaling to optimize the performance of your face recognition pipeline.

## **Celery Worker Setup**

### Default Configuration

- **Containers**: 2 workers
- **Concurrency**: 4 threads each
- **Total Capacity**: 8 concurrent tasks
- **Queue Backend**: Redis

### Scaling Information

| Configuration | Workers | Threads | Total Tasks |
|---------------|---------|---------|-------------|
| Light Load    | 1-2     | 4       | 4-8         |
| Medium Load   | 3-4     | 4       | 12-16       |
| Heavy Load    | 5-8     | 4       | 20-32       |
| Maximum       | 10      | 4       | 40          |

### Environment Variables

```env
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_POOL=threads
CELERY_WORKER_REPLICAS=2
```

## **Scaling Instructions**

### Using Provided Script

```bash
# Initial setup
chmod +x scripts/scale_workers.sh

# Scale workers
./scripts/scale_workers.sh scale 3  # Medium load

# Check worker status
./scripts/scale_workers.sh status

# Restart all workers
./scripts/scale_workers.sh restart
```

### Manual Docker Compose Scaling

```bash
# Scale workers
cd /path/to/project

# Manual scaling
 docker-compose up -d --scale celery=5

# View logs
 docker-compose logs -f celery
```

## **Performance Considerations**

| Load Type   | Memory per Worker | CPU Usage | Recommended |
|-------------|-------------------|-----------|-------------|
| Light       | ~500MB            | Low       | Dev/Test    |
| Medium      | ~1GB              | Moderate  | Production  |
| Heavy       | ~2GB              | High      | Bulk Import |

### Monitoring with Flower

- **URL**: http://localhost/flower

- **Monitor**: Active tasks, processed tasks, queue length

## **Troubleshooting Tips**

### Common Issues

- **High Memory Usage**: Scale workers down, decrease concurrency
- **Task Queue Delay**: Increase worker count, check Redis

### Tools

- **Docker Stats**: Monitor memory/CPU
  ```bash
  docker stats
  ```

- **Redis CLI**: Check queue length
  ```bash
  docker-compose exec redis redis-cli llen celery
  ```

