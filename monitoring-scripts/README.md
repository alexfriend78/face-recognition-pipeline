# Monitoring Scripts

This directory contains monitoring and diagnostic scripts for the Face Recognition Pipeline running on headless servers.

## 📁 Available Scripts

### 🔍 `health-check.sh`
**Comprehensive health check for all services**

```bash
./monitoring-scripts/health-check.sh
```

**What it checks:**
- Docker container status
- HTTP endpoint availability
- Database connectivity and statistics
- Redis status and queue lengths
- System resources (disk, memory)
- Recent errors
- File processing status

**Use when:** You want a quick overview of system health.

---

### 💾 `check-database.sh`
**Detailed database analysis and statistics**

```bash
./monitoring-scripts/check-database.sh
```

**What it provides:**
- Database size and table statistics
- File upload and processing counts
- Face detection statistics
- Recent uploads and top files by face count
- Processing performance metrics
- Issue detection (failed/stuck files)

**Use when:** You want to analyze data processing and database content.

---

### 🔧 `monitor-services.sh`
**Real-time service monitoring and resource usage**

```bash
./monitoring-scripts/monitor-services.sh
```

**What it monitors:**
- Container resource usage (CPU, memory, network)
- Service-specific health checks
- Worker status and performance
- System resource consumption
- Service restart commands

**Use when:** You need to monitor resource usage and service performance.

---

### 📁 `check-file-processing.sh`
**File processing pipeline monitoring**

```bash
./monitoring-scripts/check-file-processing.sh
```

**What it tracks:**
- Files in watch/raw/processed folders
- Processing queue status
- Worker performance and statistics
- Stuck or failed processing jobs
- Processing rate and optimization tips

**Use when:** You want to monitor file upload and processing workflow.

---

### 🌐 `check-endpoints.sh`
**HTTP endpoint availability testing**

```bash
./monitoring-scripts/check-endpoints.sh
```

**What it tests:**
- All web service endpoints
- API availability
- Response times
- External accessibility
- Status code interpretation

**Use when:** You need to verify web service availability and accessibility.

---

## 🚀 Quick Start

### First Time Setup
```bash
# Make all scripts executable
chmod +x monitoring-scripts/*.sh
```

### Daily Monitoring
```bash
# Quick health check
./monitoring-scripts/health-check.sh

# Check for processing issues
./monitoring-scripts/check-file-processing.sh
```

### Troubleshooting
```bash
# When something seems wrong
./monitoring-scripts/monitor-services.sh

# When web services aren't accessible
./monitoring-scripts/check-endpoints.sh

# When database issues are suspected
./monitoring-scripts/check-database.sh
```

## 📊 Output and Logs

- Scripts use colored output for better readability
- Health check logs are saved to `logs/health-summary.log`
- All scripts are safe to run multiple times
- No scripts modify your system - they only read and report

## 🔧 Customization

Scripts can be easily modified:
- Edit color preferences in the script headers
- Adjust thresholds for warnings/errors
- Add custom checks specific to your environment
- Modify output format as needed

## 🆘 Common Issues

### Script Permission Denied
```bash
chmod +x monitoring-scripts/*.sh
```

### Docker Commands Fail
- Ensure Docker is running
- Check if user is in docker group: `groups $USER`
- Add user to docker group: `sudo usermod -aG docker $USER`

### Database Connection Fails
- Check if PostgreSQL container is running: `docker ps | grep postgres`
- Restart database: `docker-compose restart postgres`

### No Color Output
- Some terminals don't support colors
- Scripts will still work, just without color formatting

## 📋 Integration Ideas

### Cron Jobs
```bash
# Add to crontab for automated monitoring
# Daily health check at 6 AM
0 6 * * * /path/to/monitoring-scripts/health-check.sh >> /var/log/face-recognition-health.log 2>&1

# Hourly file processing check
0 * * * * /path/to/monitoring-scripts/check-file-processing.sh | grep -i warning >> /var/log/face-recognition-warnings.log
```

### Alerting
- Parse script output for error conditions
- Send notifications when issues are detected
- Integrate with monitoring systems like Nagios or Zabbix

### Dashboards
- Export metrics to Prometheus for visualization
- Create custom Grafana dashboards using script data
- Use log aggregation for trend analysis

---

For detailed usage instructions, see the main [MONITORING_HEADLESS_GUIDE.md](../MONITORING_HEADLESS_GUIDE.md)
