# GitLab Statistics Analyzer - New Caching Functionality

## 🚀 Dramatically Improved Performance!

The tool has been extended with **JSON-based intermediate caching**. The first analysis takes the usual time, but subsequent report generations are **lightning fast**.

### 🎯 New Workflow

#### First Run (Full Collection)
```bash
# This will take 30+ minutes for large GitLab instances
pdm run glabmetrics https://gitlab.example.com admin-token \
  --output report.html \
  --verbose \
  --refresh-data
```

#### Subsequent Runs (Lightning Fast)
```bash
# Uses cached data - generates report in seconds!
pdm run glabmetrics https://gitlab.example.com admin-token \
  --output updated-report.html
```

#### When to Refresh Cache
```bash
# Weekly/monthly refresh recommended
pdm run glabmetrics https://gitlab.example.com admin-token \
  --refresh-data \
  --verbose
```

## 📊 Performance Gains

| Operation | Before | After (with cache) |
|-----------|--------|-------------------|
| Large GitLab (500+ repos) | 45+ minutes | **< 30 seconds** |
| Medium GitLab (100+ repos) | 15+ minutes | **< 10 seconds** |
| Small GitLab (< 50 repos) | 5+ minutes | **< 5 seconds** |

## 🔧 CLI Options

### Core Arguments
- `GITLAB_URL` - GitLab instance URL (e.g., https://gitlab.example.com)
- `ADMIN_TOKEN` - Admin access token with `api`, `read_api`, `read_repository` scopes

### Options
- `-o, --output TEXT` - Output HTML file path (default: gitlab_report.html)
- `-v, --verbose` - Enable verbose output with performance statistics
- `-r, --refresh-data` - Force refresh from GitLab API (ignore cache)
- `-d, --data-file TEXT` - Custom cache file path (default: gitlab_data.json)
- `--skip-binary-scan` - Skip binary file detection for faster collection

## 💡 Usage Patterns

### Development/Testing
```bash
# Quick iterations during development
pdm run glabmetrics https://gitlab.example.com token --skip-binary-scan
```

### Production Reports
```bash
# Full analysis with all metrics
pdm run glabmetrics https://gitlab.example.com token --verbose --refresh-data
```

### CI/CD Integration
```bash
# Weekly automated reports
pdm run glabmetrics $GITLAB_URL $ADMIN_TOKEN \
  --output "reports/weekly-$(date +%Y-%m-%d).html" \
  --data-file cache/gitlab_cache.json
```

## 🐳 Docker Usage

### Quick Start
```bash
docker run --rm -v $(pwd):/reports ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-token \
  --output /reports/report.html
```

### With Persistent Cache
```bash
# First run - creates cache
docker run --rm \
  -v $(pwd)/cache:/data \
  -v $(pwd)/reports:/reports \
  ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-token \
  --data-file /data/cache.json \
  --output /reports/initial-report.html \
  --refresh-data

# Subsequent runs - uses cache
docker run --rm \
  -v $(pwd)/cache:/data \
  -v $(pwd)/reports:/reports \
  ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-token \
  --data-file /data/cache.json \
  --output /reports/updated-report.html
```

## 🔍 Advanced Features

### Custom Cache Location
```bash
# Store cache in specific location
pdm run glabmetrics https://gitlab.example.com token \
  --data-file /path/to/custom/cache.json
```

### Performance Monitoring
```bash
# Verbose mode shows detailed API performance stats
pdm run glabmetrics https://gitlab.example.com token --verbose
```

### Binary File Detection
```bash
# Skip binary scanning for faster collection (may miss some storage metrics)
pdm run glabmetrics https://gitlab.example.com token --skip-binary-scan
```

## 🚨 Important Notes

1. **Cache Invalidation**: Cache is automatically invalidated after 24 hours
2. **Storage Requirements**: Cache files can be 10-100MB for large instances
3. **Token Permissions**: Admin token required for complete system statistics
4. **GitLab Version**: Optimized for GitLab 17.x+ (works with 13.x+)

## 🔧 Troubleshooting

### Cache Issues
```bash
# Force cache refresh if data seems stale
rm gitlab_data.json
pdm run glabmetrics https://gitlab.example.com token --refresh-data
```

### Performance Issues
```bash
# Check GitLab API rate limits
curl -H "Private-Token: your-token" https://gitlab.example.com/api/v4/user
```

### Memory Usage
```bash
# For very large instances, consider binary scan skip
pdm run glabmetrics https://gitlab.example.com token --skip-binary-scan
```