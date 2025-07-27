# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the glabmetrics project.

## Project Overview

**glabmetrics** is a powerful Python-based GitLab statistics analyzer with enhanced KPI analysis (P1-P6) that helps DevOps teams and platform engineers understand their GitLab instance, identify critical issues, and implement actionable optimization recommendations through comprehensive HTML reports.

## Build and Test Commands

```bash
# Install dependencies
pdm install

# Run all tests (77 tests total)
pdm run test

# Run tests with coverage
pdm run test-cov

# Run linting (flake8)
pdm run lint

# Run security scan (bandit)
pdm run security

# Build the project
pdm build

# Run the CLI tool
python -m glabmetrics --help

# Enhanced KPI Analysis (Default behavior!) - use PDM
pdm run glabmetrics https://gitlab.example.com token --verbose
pdm run analyze https://gitlab.example.com token --verbose

# Basic analysis mode (disable Enhanced KPIs)
pdm run glabmetrics https://gitlab.example.com token --basic
```

## Architecture Overview

This is a modern Python application following a clean architecture pattern:

### Core Components
- **`main.py`** - CLI entry point with Click framework and enhanced KPI integration
- **`gitlab_client.py`** - GitLab API client with comprehensive error handling and rate limiting
- **`analyzer.py`** - Core analysis engine with scoring algorithms
- **`enhanced_report_generator.py`** - Modern Bootstrap 5 HTML reports with tab-based dashboard
- **`parallel_collector.py`** - Multi-threaded data collection with CPU count workers by default
- **`data_storage.py`** - JSON-based data persistence with enhanced analysis caching
- **`performance_tracker.py`** - Performance monitoring with KPI analysis tracking

### Enhanced KPI Analyzers (NEW!)
- **`enhanced_issue_analyzer.py`** - P1: Issue backlog health and workflow analysis
- **`enhanced_mr_analyzer.py`** - P2: Code review quality and MR lead time analysis
- **`enhanced_ci_analyzer.py`** - P3: CI/CD insights and runner usage analysis
- **`enhanced_ci_config_analyzer.py`** - P4: GitLab-CI configuration best practices
- **`enhanced_submodule_analyzer.py`** - P5: Submodule network graphs and dependency analysis
- **`enhanced_performance_analyzer.py`** - P6: Performance guidelines and caching recommendations

### Key Features
- **🎯 Enhanced KPI Analysis** - P1-P6 deep analysis with parallel processing (6x speedup)
- **📋 Critical Issues Detection** - Binary performance killers, repository sprawl, CI/CD gaps
- **🚀 Actionable Recommendations** - Concrete bash commands with expected results
- **⚡ Parallel Collection** - Multi-threaded data gathering with intelligent caching
- **📊 Tab-Based Dashboard** - Modern Bootstrap 5 HTML reports with responsive design
- **🔄 Smart Incremental Updates** - Default behavior with intelligent cache management
- **📁 Auto-Generated Paths** - Automatic file paths to `.generated/` directory
- **GitLab API Integration** - Full support for GitLab 17.x+ with fallback compatibility
- **Advanced Scoring** - Repository complexity, health, and hotness scores
- **Storage Analysis** - Comprehensive breakdown of storage usage (LFS, artifacts, packages)
- **Security-First** - XSS protection with Jinja2 autoescape enabled
- **Modern Python** - Type hints, dataclasses, comprehensive error handling

### Code Standards & Formatting
- **Line Length**: 88 characters (Black standard, configured in `.flake8` and `pyproject.toml`)
- **Code Style**: Black formatting with PSF community standards
- **Formatting Command**: `pdm run format` (auto-formats all Python files)
- **Linting**: flake8 with community-ready configuration
- **Testing**: pytest with 77 comprehensive tests
- **Dependencies**: Managed with PDM

### Code Generation Guidelines
When generating new code, follow these standards:
- Use 88-character line limit (Black standard)
- Apply type hints consistently (`from typing import Dict, List, Optional`)
- Use dataclasses for structured data (`@dataclass`)
- Follow existing patterns in the codebase (see existing analyzers)
- Add comprehensive error handling with try/except blocks
- Use descriptive variable names and docstrings
- Prefer composition over inheritance
- **Post-Generation**: Always run `pdm run format` to ensure perfect formatting

### Data Flow
1. **Collection** - ParallelGitLabCollector fetches data with multi-threading (CPU count workers by default)
2. **Basic Analysis** - GitLabAnalyzer processes and scores repositories
3. **Enhanced Analysis** - P1-P6 KPI analyzers run in parallel (6x speedup)
4. **Storage** - GitLabDataStorage handles caching with enhanced analysis persistence
5. **Issue Detection** - Critical issues analysis with binary performance killers detection
6. **Recommendations** - Actionable best practices with concrete implementation steps
7. **Reporting** - EnhancedHTMLReportGenerator creates tab-based Bootstrap 5 dashboards

### Security Considerations
- **XSS Protection** - All user content properly escaped in HTML templates
- **Input Validation** - Comprehensive validation of API responses
- **No Secrets Logging** - Sensitive data (tokens, URLs) never logged
- **Safe JSON Handling** - Proper escaping in JavaScript contexts

### Testing Strategy
- **77 Tests Total** - Comprehensive coverage across all components
- **Security Tests** - XSS protection and data validation (7 tests)
- **Template Tests** - HTML generation and data preparation (6 tests)
- **Integration Tests** - End-to-end workflow testing
- **Mock-Heavy** - Isolated unit tests with extensive mocking

### Recent Major Features (v2.0)
- **🎯 Enhanced KPI Analysis** - P1-P6 analyzers enabled by default with parallel processing
- **📋 Critical Issues Detection** - Binary performance killers, storage waste detection
- **🚀 Actionable Recommendations** - Concrete bash commands with expected results
- **⚡ Simplified CLI Interface** - Streamlined options with intelligent defaults
- **📊 Tab-Based Dashboard** - Modern Bootstrap 5 HTML with responsive design
- **🔄 Smart Incremental Updates** - Default behavior with intelligent cache management
- **📁 Auto-Generated Paths** - Automatic output paths to `.generated/` directory
- **📈 Performance Tracking** - Separate JSON files with detailed performance statistics

### Development Workflow
1. **Initial Setup**: `pdm run setup-dev` - One-time developer environment setup
   - Cleans workspace (removes target/, .generated/, caches)
   - Creates target/ directory for build outputs
   - Installs pre-commit hooks for automatic code quality checks
2. **Development Cycle**:
   - Make code changes following existing patterns
   - `pdm run check-fast` - Quick validation during development (format-check + lint + test-fast)
   - `pdm run check` - Full CI-like validation before commits (format-check + lint + typecheck + security + test-cov)
3. **Code Standards**:
   - Use existing dataclasses (`RepositoryStats`, `SystemStats`)
   - Follow type hint conventions throughout
   - Add tests for all new functionality
   - Use descriptive commit messages with `pdm run commit` (conventional commits)

### Code Quality Standards (Single Source of Truth)
- **Line Length**: 88 characters (Black/PSF standard)
- **Configuration**: All tools read from `pyproject.toml` - change line-length in ONE place
- **Tools**: Black (formatting), isort (imports), flake8 (linting), mypy (typing), bandit (security)
- **Pre-commit**: Automatic quality checks on every commit using PDM-managed tools

### PDM Commands Reference
```bash
# 🚀 Primary Development Commands
pdm run setup-dev         # One-time environment setup
pdm run check             # Complete CI validation (recommended before commits)
pdm run check-fast        # Quick validation (development iteration)

# 🧪 Testing
pdm run test              # All 77 tests
pdm run test-cov          # Tests with coverage (output: target/coverage-html/)
pdm run test-fast         # Stop on first failure
pdm run test-verbose      # Detailed test output

# 🔍 Code Quality (Individual)
pdm run format            # Black + isort formatting
pdm run format-check      # Check formatting without changes
pdm run lint              # flake8 linting (88-char limit)
pdm run typecheck         # mypy type checking
pdm run security          # Bandit security scan
pdm run security-report   # Security report (target/bandit-report.json)

# 🧹 Utilities
pdm run clean             # Remove build artifacts and caches
pdm run commit            # Conventional commits with commitizen
pdm run bump              # Semantic version bump
pdm run changelog         # Generate changelog

# 🚀 Application
pdm run glabmetrics       # CLI tool execution
pdm run analyze           # Alias for glabmetrics
```

### Build Outputs & File Organization
- **Target Directory**: `target/` (auto-created, gitignored)
  - `target/coverage-html/` - Coverage reports
  - `target/coverage.xml` - Coverage XML
  - `target/bandit-report.json` - Security scan results
- **Generated Directory**: `.generated/` - GitLab analysis outputs (gitignored)
- **Pre-commit Hooks**: Use `language: system` to utilize PDM-managed tool versions

### CI/CD Pipeline (Matches Local Development)
- **Testing**: Python 3.9-3.12 matrix testing
- **Code Quality**: Black format-check (88 characters), flake8 linting, mypy type checking
- **Security**: Bandit security scanning (reports to artifacts)
- **Coverage**: pytest-cov with Codecov integration
- **Build Outputs**: All reports saved to `target/` directory
- **Building**: PDM build + Docker multi-arch
- **Deployment**: GitHub Container Registry
- **Pre-commit Consistency**: Same tools and versions as local development

### GitLab API Compatibility
- **Primary Target**: GitLab 17.x+ (with detailed storage statistics)
- **Fallback Support**: Earlier versions with estimation algorithms
- **Rate Limiting**: Built-in retry and backoff mechanisms
- **Pagination**: Automatic handling of large datasets
