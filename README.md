# glabmetrics

[![GitHub Release](https://img.shields.io/github/v/release/cdds-ab/glabmetrics?sort=semver&logo=github)](https://github.com/cdds-ab/glabmetrics/releases)
[![CI/CD Pipeline](https://github.com/cdds-ab/glabmetrics/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/cdds-ab/glabmetrics/actions)
[![Test Coverage](https://img.shields.io/codecov/c/github/cdds-ab/glabmetrics/master?logo=codecov)](https://codecov.io/gh/cdds-ab/glabmetrics)
[![Code Quality](https://img.shields.io/codefactor/grade/github/cdds-ab/glabmetrics/master?logo=codefactor)](https://www.codefactor.io/repository/github/cdds-ab/glabmetrics)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/cdds-ab/glabmetrics/pkgs/container/glabmetrics)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensource)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/github/downloads/cdds-ab/glabmetrics/total?logo=github)](https://github.com/cdds-ab/glabmetrics/releases)
[![Last Commit](https://img.shields.io/github/last-commit/cdds-ab/glabmetrics?logo=github)](https://github.com/cdds-ab/glabmetrics/commits)
[![Issues](https://img.shields.io/github/issues/cdds-ab/glabmetrics?logo=github)](https://github.com/cdds-ab/glabmetrics/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?logo=github)](http://makeapullrequest.com)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/cdds-ab/glabmetrics/graphs/commit-activity)

A powerful CLI tool for comprehensive analysis of GitLab instances with detailed HTML reporting and optimization recommendations for DevOps consultants.

## ✨ Features

### 📊 Comprehensive Analysis
- **Repository Metrics**: Size, commits, contributors, activity
- **Storage Breakdown**: LFS, artifacts, packages, container registry
- **Advanced Scoring**: Complexity, health, hotness, maintenance scores
- **Pipeline Analysis**: Success rates, performance, runner usage
- **Optimization Recommendations**: Concrete cleanup suggestions

### 🚀 Performance & Caching
- **Intelligent Caching**: JSON-based intermediate storage for fast re-analysis
- **Performance Tracking**: Detailed API performance statistics
- **Incremental Updates**: Fetch only new data with `--refresh-data`

### 📱 Modern Reporting
- **Bootstrap 5 HTML**: Responsive, professional reports
- **Chart.js Visualizations**: Interactive charts and diagrams
- **GitLab Version Detection**: Optimized for GitLab 17.x+ features
- **Export-Ready**: PDF-print optimized layouts

### 🐳 Deployment Options
- **Standalone CLI**: Direct installation and execution
- **Docker Support**: Containerized deployment
- **CI/CD Integration**: GitHub Actions ready

## 🚀 Quick Start

### 🐳 Installation

```bash
# Production Ready (recommended)
docker pull ghcr.io/cdds-ab/glabmetrics:latest

# Development Setup
git clone https://github.com/cdds-ab/glabmetrics.git
cd glabmetrics
pdm install
```

### 🚀 Usage

```bash
# 🐳 Docker (Production - recommended)
docker run --rm -v $(pwd):/reports ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-admin-token \
  --output /reports/gitlab-analysis.html

# With data persistence and advanced options
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/reports:/reports \
  ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-admin-token \
  --data-file /data/cache.json \
  --output /reports/detailed-report.html \
  --verbose --refresh-data

# 🛠️ Development (for developers only)
pdm run glabmetrics https://gitlab.example.com your-admin-token \
  --output report.html --refresh-data
```

## 📖 Usage Guide

### CLI Options

```
Usage: glabmetrics [OPTIONS] GITLAB_URL ADMIN_TOKEN

Arguments:
  GITLAB_URL   GitLab instance URL (e.g., https://gitlab.example.com)
  ADMIN_TOKEN  Admin access token for GitLab API

Options:
  -o, --output TEXT        Output HTML file path (default: gitlab_report.html)
  -v, --verbose           Enable verbose output
  -r, --refresh-data      Refresh data from GitLab API (use cached data otherwise)
  -d, --data-file TEXT    Data file path (default: gitlab_data.json)
  --skip-binary-scan     Skip binary file detection (faster collection)
  --help                 Show this message and exit
```

### GitLab Token Setup

1. **Create Admin Token**:
   - GitLab → User Settings → Access Tokens
   - Scopes: `api`, `read_api`, `read_repository`
   - Role: `Administrator` (for system statistics)

2. **Check Permissions**:
   ```bash
   curl -H "Private-Token: your-token" https://gitlab.example.com/api/v4/user
   ```

### Workflow Examples

#### First Complete Analysis
```bash
# Complete data collection (may take hours)
pdm run glabmetrics https://gitlab.example.com token --verbose --refresh-data

# Quick analysis without binary scan
pdm run glabmetrics https://gitlab.example.com token --skip-binary-scan --refresh-data
```

#### Regular Updates
```bash
# Use cached data for quick reports
pdm run glabmetrics https://gitlab.example.com token --output weekly-report.html

# Update cache (recommended weekly)
pdm run glabmetrics https://gitlab.example.com token --refresh-data
```

## 📊 Report Sections

### System Overview
- Total repositories, storage, commits
- Orphaned repository detection
- GitLab version and collection timestamp

### Storage Analysis
- **Detailed Breakdown**: Repository data, LFS, Artifacts, Packages
- **Cleanup Recommendations**: Specific storage optimization tips
- **GitLab 17.x Enhancement**: Accurate storage APIs

### Repository Rankings
- **Most Complex**: Language diversity, architectural complexity
- **Healthiest**: Activity, issue management, maintenance quality
- **Hottest**: Recent activity, fetch patterns, contributor engagement
- **Largest**: Storage consumption analysis

### Pipeline Intelligence  
- Success rates across all repositories
- Runner utilization patterns
- Job failure analysis and recommendations

### Optimization Recommendations
- Orphaned repository cleanup (6+ months inactive)
- LFS migration suggestions for large binary files
- Artifact cleanup policies (30+ day retention)
- Container image cleanup recommendations

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/cdds-ab/glabmetrics-analyzer.git
cd glabmetrics-analyzer

# Install PDM
curl -sSL https://pdm-project.org/install-pdm.py | python3 -

# Install dependencies
pdm install -d

# Setup pre-commit hooks
pdm run pre-commit-install
```

### Development Commands

```bash
# Run tests
pdm run test                 # All tests
pdm run test-cov            # With coverage report  
pdm run test-fast           # Fast tests (stop on first failure)

# Code quality
pdm run lint                # Linting
pdm run format              # Code formatting
pdm run format-check        # Check formatting

# Semantic versioning
pdm run commit              # Conventional commits
pdm run bump                # Version bump
pdm run changelog           # Generate changelog
```

### Testing

```bash
# Unit tests
pdm run test tests/test_analyzer.py

# Integration tests  
pdm run test tests/integration/

# With coverage
pdm run test-cov
open htmlcov/index.html
```

### Architecture Overview

```
glabmetrics/
├── main.py              # CLI entry point
├── gitlab_client.py     # GitLab API client
├── analyzer.py          # Core analysis logic
├── data_storage.py      # Caching and serialization
├── report_generator.py  # HTML report generation
└── performance_tracker.py # Performance monitoring

tests/
├── conftest.py          # Pytest fixtures
├── test_*.py           # Unit tests
└── integration/        # Integration tests
```

## 🚨 Troubleshooting

### Common Issues

#### API Rate Limiting
```bash
# Symptom: "Too many requests" errors
# Solution: Check GitLab rate limits and use caching
pdm run glabmetrics url token --data-file cache.json  # Use cached data
```

#### Memory Issues (Large Instances)
```bash
# Symptom: Out of memory during analysis
# Solution: Skip binary scanning
pdm run glabmetrics url token --skip-binary-scan
```

#### Slow Performance
```bash
# Check performance stats
pdm run glabmetrics url token --verbose --refresh-data

# Use incremental updates
pdm run glabmetrics url token  # Uses cache automatically
```

#### Token Permissions
```bash
# Test token access
curl -H "Private-Token: your-token" https://gitlab.example.com/api/v4/version

# Required scopes: api, read_api, read_repository
# Required role: Administrator (for system stats)
```

## 📝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork & Clone**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes with tests**
4. **Commit**: `pdm run commit` (uses conventional commits)
5. **Push & Create PR**

### Conventional Commits

```bash
# Use commitizen for proper commit messages
pdm run commit

# Examples:
feat: add new storage breakdown analysis
fix: resolve serialization error with defaultdict
docs: update README with Docker examples
test: add unit tests for scoring algorithms
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GitLab for their comprehensive API
- Chart.js for beautiful visualizations
- Bootstrap for responsive design
- The Python community for excellent tooling

---

**Made with ❤️ for the DevOps community**