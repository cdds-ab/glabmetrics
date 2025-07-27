# GitLab Statistics Analyzer - Usage Guide

## 🎯 Simplified CLI with Enhanced KPI Analysis (v2.0)

The tool now features a **streamlined CLI interface** with **P1-P6 Enhanced KPI Analysis enabled by default**. Experience intelligent defaults, auto-generated paths, and smart incremental updates.

### 🚀 Quick Start

#### 🚀 First Run (Initial Data Collection)
```bash
# Complete P1-P6 analysis with auto-generated paths
pdm run glabmetrics https://gitlab.example.com admin-token --refresh-data --verbose

# Output automatically saved to:
# - .generated/gitlab-example-com.html (report)
# - .generated/gitlab-example-com.json (data cache)
# - .generated/gitlab-example-com-perf.json (performance stats)

# Expected output:
# 🎯 Running Enhanced KPI Analysis (Parallel)...
# ✅ ISSUE metrics collected (8.2s)
# ✅ MR metrics collected (12.1s)
# ✅ CI metrics collected (15.3s)
# ✅ SUBMODULE metrics collected (9.7s)
# 🚀 Parallel collection completed in 18.4s
#
# 🚨 TOP CRITICAL ISSUES FOUND:
# 1. 🚨 Binary Files Killing GitLab Performance
#    CRITICAL: 3 repositories with massive binary files cause web UI timeouts
#    💡 Quick fix: IMMEDIATE: Migrate to Git LFS
```

#### ⚡ Subsequent Runs (Incremental Updates)
```bash
# Default behavior: intelligent incremental updates
pdm run glabmetrics https://gitlab.example.com admin-token

# Alternative: use the 'analyze' shortcut
pdm run analyze https://gitlab.example.com admin-token

# Smart behavior:
# - If cache exists: runs incremental update automatically
# - If no cache: guides user to use --refresh-data for initial collection

# Force incremental update (only changed repositories)
pdm run glabmetrics https://gitlab.example.com admin-token --incremental
```

## 🎯 Enhanced KPI Analysis (Default Behavior)

### P1-P6 Analyzer Overview

| Analyzer | Focus Area | Key Metrics | Expected Impact |
|----------|------------|-------------|-----------------|
| **P1: Issues** | Backlog health | Resolution times, workflow efficiency | 60% faster issue resolution |
| **P2: Code Review** | MR quality | Lead times, approval bottlenecks | 50% reduction in lead time |
| **P3: CI/CD** | Pipeline insights | Success rates, runner usage | 40% improvement in pipeline reliability |
| **P4: Configuration** | Best practices | Security scans, caching optimization | 80% better CI configuration scores |
| **P5: Network** | Submodule analysis | Dependency graphs, circular detection | Elimination of circular dependencies |
| **P6: Performance** | Optimization | Caching recommendations, large files | 70% repository size reduction |

### 📋 Critical Issues Detection

The tool automatically detects and prioritizes critical issues:

```bash
🚨 TOP CRITICAL ISSUES FOUND:

1. 🚨 Binary Files Killing GitLab Performance
   CRITICAL: 3 repositories with massive binary files cause web UI timeouts
   📁 Affected: friendlycore-rootfs, FriendlycoreBuildsystem
   💡 Quick fix: IMMEDIATE: Migrate to Git LLS

2. 📦 Repository Sprawl Wasting Resources
   HIGH: 156 inactive repositories waste 6.2GB and slow maintenance by 60%
   📁 Affected: obsolete1/old-project, _delete_temp-repo
   💡 Quick fix: WEEK 1: Archive 23 pre-marked repos

3. 🔧 Active Development Without CI/CD
   MEDIUM: 23 active repositories lack automation, increasing bug risk by 300%
   💡 Quick fix: WEEK 1: Deploy CI templates for top 5 active repos
```

### Basic Analysis Mode
```bash
# Disable Enhanced KPIs for faster basic analysis
pdm run glabmetrics https://gitlab.example.com admin-token --basic
```

### Manual Cache Management
```bash
# Weekly/monthly full refresh recommended
pdm run analyze https://gitlab.example.com admin-token --refresh-data --verbose
```

## 📊 Performance Gains

| Operation | Before | After (with cache) |
|-----------|--------|-------------------|
| Large GitLab (500+ repos) | 45+ minutes | **< 30 seconds** |
| Medium GitLab (100+ repos) | 15+ minutes | **< 10 seconds** |
| Small GitLab (< 50 repos) | 5+ minutes | **< 5 seconds** |

## 🔧 Simplified CLI Options

### Core Arguments
- `GITLAB_URL` - GitLab instance URL (e.g., https://gitlab.example.com)
- `ADMIN_TOKEN` - Admin access token with `api`, `read_api`, `read_repository` scopes

### Options
- `-o, --output TEXT` - Output HTML file path (default: auto-generated from URL)
- `-d, --data-file TEXT` - Data cache file path (default: auto-generated from URL)
- `-v, --verbose` - Enable verbose output with performance statistics
- `-r, --refresh-data` - Force complete data refresh (conflicts with --incremental)
- `-i, --incremental` - Force incremental update (conflicts with --refresh-data)
- `-w, --workers INTEGER` - Number of parallel workers (default: CPU count)
- `--basic` - Disable Enhanced KPIs (basic analysis only)

### Auto-Generated Paths
```bash
# URL: https://gitlab.example.com
# Auto-generated paths:
# - Report: .generated/gitlab-example-com.html
# - Data: .generated/gitlab-example-com.json
# - Performance: .generated/gitlab-example-com-perf.json
```

## 💡 Usage Patterns

### Development/Testing
```bash
# Quick iterations with basic analysis
pdm run glabmetrics https://gitlab.example.com token --basic --verbose
```

### Production Reports
```bash
# Full Enhanced KPI analysis (default behavior)
pdm run analyze https://gitlab.example.com token --verbose --refresh-data
```

### CI/CD Integration
```bash
# Weekly automated reports with custom paths
pdm run glabmetrics $GITLAB_URL $ADMIN_TOKEN \
  --output "reports/weekly-$(date +%Y-%m-%d).html" \
  --data-file "cache/gitlab_cache.json" \
  --refresh-data
```

### Available PDM Scripts
```bash
# Two equivalent ways to run the analyzer
pdm run glabmetrics $GITLAB_URL $ADMIN_TOKEN --verbose
pdm run analyze $GITLAB_URL $ADMIN_TOKEN --refresh-data

# Both scripts execute: python -m glabmetrics.main
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

# Subsequent runs - automatic incremental updates
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
pdm run analyze https://gitlab.example.com token --verbose

# Performance data automatically saved as separate JSON file
# Example: .generated/gitlab-example-com-perf.json
```

### Worker Configuration
```bash
# Adjust parallel workers (default: CPU count)
pdm run glabmetrics https://gitlab.example.com token --workers 8
```

## 🚨 Important Notes

1. **Default Behavior**: Enhanced KPIs and intelligent incremental updates enabled by default
2. **Auto-Generated Paths**: Files automatically saved to `.generated/` directory
3. **Performance Data**: Separate JSON file with performance statistics always created
4. **Mutually Exclusive Flags**: Cannot use `--refresh-data` and `--incremental` together
5. **Cache Management**: Smart user guidance when cache is missing
6. **Token Permissions**: Admin token required for complete system statistics
7. **GitLab Version**: Optimized for GitLab 17.x+ (works with 13.x+)

## 🔧 Troubleshooting

### Cache Issues
```bash
# Force cache refresh if data seems stale
rm .generated/gitlab-example-com.json
pdm run analyze https://gitlab.example.com token --refresh-data
```

### Performance Issues
```bash
# Check GitLab API rate limits
curl -H "Private-Token: your-token" https://gitlab.example.com/api/v4/user

# Use basic analysis for faster execution
pdm run glabmetrics https://gitlab.example.com token --basic
```

### Worker Optimization
```bash
# Reduce workers for high-latency connections
pdm run glabmetrics https://gitlab.example.com token --workers 4

# Check performance stats
pdm run analyze https://gitlab.example.com token --verbose
```
