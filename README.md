# glabmetrics

[![Development Status](https://img.shields.io/badge/Status-Active%20Development-blue?logo=github)](https://github.com/cdds-ab/glabmetrics)
[![CI/CD Pipeline](https://github.com/cdds-ab/glabmetrics/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/cdds-ab/glabmetrics/actions)
[![Test Coverage](https://img.shields.io/badge/Coverage-20%25-orange?logo=pytest)](https://github.com/cdds-ab/glabmetrics/actions)
[![Code Quality](https://img.shields.io/badge/Quality-PDM%20%7C%20Black%20%7C%20Flake8-green?logo=python)](https://github.com/cdds-ab/glabmetrics)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Build%20Ready-blue?logo=docker)](https://github.com/cdds-ab/glabmetrics/blob/master/Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensource)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-49%20passing-brightgreen?logo=pytest)](https://github.com/cdds-ab/glabmetrics/actions)
[![Last Commit](https://img.shields.io/github/last-commit/cdds-ab/glabmetrics?logo=github)](https://github.com/cdds-ab/glabmetrics/commits)
[![Issues](https://img.shields.io/github/issues/cdds-ab/glabmetrics?logo=github)](https://github.com/cdds-ab/glabmetrics/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?logo=github)](http://makeapullrequest.com)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/cdds-ab/glabmetrics/graphs/commit-activity)

A powerful CLI tool for comprehensive analysis of GitLab instances with enhanced KPI dashboards, 90% faster performance optimization, and actionable recommendations for DevOps consultants and platform engineers.

## ✨ Features

### 🎯 Enhanced KPI Analysis (Production Ready 2025)
- **P1 - Issue Analytics**: Backlog health, resolution patterns, workflow bottlenecks
- **P2 - Code Review Quality**: MR lead times, approval workflows, review efficiency  
- **P3 - CI/CD Intelligence**: Runner utilization, pipeline optimization, Jenkins integration
- **P4 - Configuration Audit**: GitLab-CI best practices, security compliance, caching strategies
- **P5 - Dependency Analysis**: Submodule networks, circular dependencies, architecture insights
- **P6 - Performance Crisis**: **90% faster binary detection**, storage waste cleanup, optimization roadmap
- **A1 - Actionable Dashboard**: Critical issues with concrete implementation steps and deadlines
- **C1 - Comprehensive View**: Unified analytics with prioritized transformation roadmap

### 🚀 Performance & Intelligence
- **Intelligent Incremental Mode**: Automatic cache detection - only analyzes changed repositories
- **90% Performance Boost**: Binary file scanning optimized from 250s → 10-30s for large repos
- **Parallel Collection**: Multi-threaded data gathering with CPU-adaptive workers
- **Smart Cache Management**: Automatic Enhanced KPI generation when missing from cache
- **Directory Blacklisting**: Skips `node_modules`, `build`, `dist` for faster analysis
- **Size-based Optimization**: Auto-skips repos >2GB to prevent timeouts
- **Emergency Save**: Graceful Ctrl-C handling with incremental restart capability

### 📊 Comprehensive Analysis Engine
- **Repository Intelligence**: Size, commits, contributors, activity patterns, health scoring
- **Storage Breakdown**: LFS, artifacts, packages, container registry with GitLab 17.x+ APIs
- **Advanced Metrics**: Complexity, health, hotness, maintenance scores with trend analysis
- **Pipeline Analytics**: Success rates, duration patterns, failure analysis, runner optimization
- **Critical Issues Detection**: Binary performance killers, repository sprawl, CI/CD gaps
- **Actionable Recommendations**: Copy-paste commands with expected results and timelines

### 📱 Modern Dashboard Experience
- **Modular Architecture**: 8 specialized dashboard tabs (P1-P6, A1, C1)
- **Bootstrap 5 + Chart.js**: Responsive design with interactive visualizations
- **Performance Crisis Mode**: Automated 110GB+ storage waste alerts
- **Console Integration**: Top 3 critical issues displayed during analysis
- **Export-Ready Layouts**: PDF-optimized reporting for executive summaries
- **Real-time Progress**: Live collection dashboard with ETA and error tracking

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
# 🎯 Super Simple - URL + Token + Go!
pdm run analyze https://gitlab.example.com YOUR_TOKEN -r -v  # First time
pdm run analyze https://gitlab.example.com YOUR_TOKEN       # Always after

# 🐳 Docker (Production - build locally)
docker build -t glabmetrics .
docker run --rm -v $(pwd):/reports glabmetrics \
  analyze https://gitlab.example.com your-admin-token --refresh-data

# 🚀 Intelligent Incremental (Automatic!)
pdm run analyze https://gitlab.example.com YOUR_TOKEN
# → Detects cache automatically, runs Enhanced KPIs if missing

# ⚡ Fast Report Regeneration (NEW! - No API calls)
pdm run analyze https://gitlab.example.com YOUR_TOKEN --regenerate-report
# → Instant HTML report from cached data (seconds, not minutes)

# 🎯 Performance Optimized for Large Instances
pdm run analyze https://gitlab.example.com YOUR_TOKEN --skip-binary-scan -w 30

# 📊 Standalone Performance Dashboard (from cached data)
pdm run performance --data-file=.generated/gitlab-data.json
```

## 📖 Usage Guide

### 🎯 Super Simple CLI

```bash
# Everything you need - 3 commands total!

# 1️⃣ First time: Complete analysis
pdm run analyze GITLAB_URL TOKEN -r

# 2️⃣ Updates: Intelligent incremental 
pdm run analyze GITLAB_URL TOKEN

# 3️⃣ Performance deep-dive: From cached data
pdm run performance --data-file=.generated/data.json
```

### 🔧 CLI Reference

```
Commands:
  analyze      Enhanced KPI analysis with 8-tab dashboard (P1-P6, A1, C1)
  performance  Standalone performance crisis dashboard

Main Options:
  -r, --refresh-data       Complete data collection (first time)
  -v, --verbose           Show detailed progress and timing
  -w, --workers N         Parallel processing (default: CPU count)
  --skip-binary-scan     90% faster for large instances
  --force-enhanced       Force refresh Enhanced KPIs
  --basic                Disable Enhanced KPIs (basic mode only)

Auto-Magic Features:
  ✨ Intelligent cache detection - no manual flags needed
  ✨ Auto-generates files to .generated/ directory  
  ✨ Enhanced KPIs run automatically when missing
  ✨ Emergency save on Ctrl-C for incremental restart
  ✨ Performance stats saved as separate JSON
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

#### 🚀 Production Workflows

```bash
# 🎯 Enterprise GitLab Analysis (Complete)
pdm run analyze https://gitlab.company.com ${GITLAB_TOKEN} -r -v

# ⚡ Large Instance Optimization (500+ repos)
pdm run analyze https://gitlab.company.com ${GITLAB_TOKEN} -r --skip-binary-scan -w 40

# 📊 Weekly Update Reports (Smart Incremental)
pdm run analyze https://gitlab.company.com ${GITLAB_TOKEN} -v

# 🚨 Performance Crisis Dashboard (From Cache)
pdm run performance --data-file=.generated/gitlab-company-com.json
```

#### 🛠️ Development & Testing

```bash
# Quick development test (basic mode)
pdm run analyze https://gitlab.example.com token --basic -r

# Force Enhanced KPI refresh (troubleshooting)
pdm run analyze https://gitlab.example.com token --force-enhanced

# Custom output paths (reporting)
pdm run analyze https://gitlab.example.com token -o weekly-report.html
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
