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

A powerful CLI tool for comprehensive analysis of GitLab instances with detailed HTML reporting, enhanced KPI analysis, and actionable optimization recommendations for DevOps consultants and platform engineers.

## ✨ Features

### 📊 Comprehensive Analysis
- **Repository Metrics**: Size, commits, contributors, activity, binary file detection
- **Storage Breakdown**: LFS, artifacts, packages, container registry analysis
- **Advanced Scoring**: Complexity, health, hotness, maintenance scores
- **Pipeline Analysis**: Success rates, performance, runner usage
- **🎯 Critical Issues Detection**: Binary performance killers, repository sprawl, CI/CD gaps
- **📋 Actionable Recommendations**: Concrete implementation steps with expected results

### 🚀 Performance & Caching
- **Parallel Collection**: Multi-threaded data gathering (CPU count workers by default)
- **Intelligent Caching**: JSON-based intermediate storage for fast re-analysis
- **Smart Incremental Updates**: Default behavior - only fetch changed repositories
- **Auto-Generated Paths**: Automatic file paths to `.generated/` directory
- **Performance Tracking**: Detailed API performance statistics saved as separate JSON

### 🎯 Enhanced KPI Analysis (NEW!)
- **P1 - Issue KPI Analysis**: Issue backlog health, resolution times, workflow efficiency
- **P2 - Code Review Quality**: MR lead times, approval bottlenecks, review patterns
- **P3 - CI/CD Insights**: Runner usage, pipeline success rates, Jenkins webhook analysis
- **P4 - Configuration Check**: GitLab-CI best practices, security scans, caching optimization
- **P5 - Network Analysis**: Submodule dependency graphs, circular dependency detection
- **P6 - Performance Guidelines**: Caching recommendations, large file optimization
- **🚀 Parallel Processing**: All 6 analyses run simultaneously for 6x speed improvement

### 📱 Modern Reporting
- **Tab-Based Dashboard**: Switchable overview, repository details, storage, and recommendations
- **Bootstrap 5 HTML**: Responsive, professional reports with dark/light mode
- **Chart.js Visualizations**: Interactive charts, graphs, and network diagrams
- **Critical Issues Summary**: Top 3 issues displayed in console and dashboard
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

# 🎯 Enhanced KPI Analysis (Default behavior!)
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/reports:/reports \
  ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-admin-token \
  --data-file /data/cache.json \
  --output /reports/enhanced-report.html \
  --verbose --refresh-data

# 🚀 Smart incremental updates (Default behavior)
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/reports:/reports \
  ghcr.io/cdds-ab/glabmetrics:latest \
  https://gitlab.example.com your-admin-token \
  --data-file /data/cache.json \
  --output /reports/updated-report.html

# 🛠️ Development with PDM and auto-generated paths
pdm run glabmetrics https://gitlab.example.com your-admin-token --verbose
pdm run analyze https://gitlab.example.com your-admin-token --verbose
```

## 📖 Usage Guide

### Simplified CLI Options

```
Usage: glabmetrics [OPTIONS] GITLAB_URL ADMIN_TOKEN

Arguments:
  GITLAB_URL   GitLab instance URL (e.g., https://gitlab.example.com)
  ADMIN_TOKEN  Admin access token for GitLab API

Options:
  -o, --output TEXT         Output HTML file path (default: auto-generated)
  -d, --data-file TEXT      Data cache file path (default: auto-generated)
  -v, --verbose            Enable verbose output with performance details
  -r, --refresh-data       Force complete data refresh (conflicts with -i)
  -i, --incremental        Force incremental update (conflicts with -r)
  -w, --workers INTEGER    Number of parallel workers (default: CPU count)
  --basic                  Disable Enhanced KPIs (basic analysis only)
  --help                   Show this message and exit

Default Behavior:
  • Enhanced KPIs (P1-P6) enabled by default
  • Intelligent incremental updates when cache exists
  • Auto-generated paths to .generated/ directory
  • Performance data saved as separate JSON file
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

#### 🚀 First Complete Analysis
```bash
# Complete Enhanced KPI analysis (default behavior)
pdm run analyze https://gitlab.example.com token --refresh-data --verbose

# Quick basic analysis (for testing)
pdm run glabmetrics https://gitlab.example.com token --basic --refresh-data
```

#### 📊 Enhanced KPI Analysis (Default!)
```bash
# Full P1-P6 analysis with auto-generated paths
pdm run glabmetrics https://gitlab.example.com token --verbose

# Custom output location
pdm run analyze https://gitlab.example.com token \
  --output custom-report.html --refresh-data
```

#### ⚡ Regular Updates
```bash
# Smart incremental update (default behavior)
pdm run glabmetrics https://gitlab.example.com token

# Force incremental update with custom output
pdm run analyze https://gitlab.example.com token \
  --incremental --output weekly-report.html
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
git clone https://github.com/cdds-ab/glabmetrics.git
cd glabmetrics

# Install PDM
curl -sSL https://pdm-project.org/install-pdm.py | python3 -

# Install dependencies & setup development environment
pdm install -d
pdm run setup-dev           # One-time setup: clean + create target/ + install pre-commit hooks
```

### Development Commands

```bash
# 🚀 Complete CI-like validation (recommended before commits)
pdm run check               # format-check + lint + typecheck + security + test-cov
pdm run check-fast          # format-check + lint + test-fast (for rapid iteration)

# 🧪 Testing
pdm run test                # All 77 tests
pdm run test-cov            # With coverage report (outputs to target/coverage-html/)
pdm run test-fast           # Fast tests (stop on first failure)
pdm run test-verbose        # Verbose test output

# 🔍 Code Quality
pdm run lint                # flake8 linting (88-char line limit)
pdm run format              # Black + isort formatting
pdm run format-check        # Check formatting without changes
pdm run typecheck           # mypy type checking
pdm run security            # Bandit security scan (19 low-severity findings)
pdm run security-report     # Security report to target/bandit-report.json

# 🧹 Development Utilities
pdm run clean               # Remove target/, .generated/, caches
pdm run setup-dev           # Reset development environment

# 📦 Release Management
pdm run commit              # Conventional commits with commitizen
pdm run bump                # Semantic version bump
pdm run changelog           # Generate changelog

# 🚀 Application Commands
pdm run glabmetrics         # Run the CLI tool
pdm run analyze             # Alias for glabmetrics
```

### Pre-commit Hooks

Pre-commit hooks automatically run on `git commit` and include:
- Black code formatting (88 characters)
- isort import sorting
- flake8 linting
- mypy type checking
- Bandit security scanning
- Trailing whitespace removal
- YAML/TOML validation

**Bypass hooks** (not recommended): `git commit --no-verify`

### Line Length Configuration

All tools use **88 characters** (Black/PSF standard) configured in **one place**:
- Edit `pyproject.toml`: `line-length = 88`
- All tools (Black, flake8, isort) automatically inherit this setting
- **To change to 120 chars**: Only change the single line-length value in pyproject.toml

### Testing & Coverage

```bash
# Run specific test files
pdm run test tests/test_analyzer.py
pdm run test tests/test_security.py

# Coverage analysis
pdm run test-cov                    # Run tests with coverage
open target/coverage-html/index.html  # View HTML coverage report
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
# Solution: Use cached data and reduce workers
pdm run glabmetrics url token --workers 4  # Use cached data automatically
```

#### Memory Issues (Large Instances)
```bash
# Symptom: Out of memory during analysis
# Solution: Use basic analysis mode
pdm run glabmetrics url token --basic
```

#### Slow Performance
```bash
# Check performance stats (automatically saved as separate JSON)
pdm run analyze url token --verbose --refresh-data

# Use incremental updates (default behavior)
pdm run glabmetrics url token  # Smart incremental updates
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
