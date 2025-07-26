# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the glabmetrics project.

## Project Overview

**glabmetrics** is a Python-based GitLab statistics analyzer that helps organizations understand their GitLab instance usage, identify optimization opportunities, and generate comprehensive HTML reports.

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

# Build the project
pdm build

# Run the CLI tool
pdm run glabmetrics --help
```

## Architecture Overview

This is a modern Python application following a clean architecture pattern:

### Core Components
- **`main.py`** - CLI entry point using Click framework
- **`gitlab_client.py`** - GitLab API client with comprehensive error handling
- **`analyzer.py`** - Core analysis engine with scoring algorithms
- **`report_generator.py`** - HTML report generation with Jinja2 templates
- **`data_storage.py`** - JSON-based data persistence
- **`performance_tracker.py`** - Performance monitoring and profiling

### Key Features
- **GitLab API Integration** - Full support for GitLab 17.x+ with fallback compatibility
- **Advanced Scoring** - Repository complexity, health, and hotness scores
- **Storage Analysis** - Comprehensive breakdown of storage usage (LFS, artifacts, packages)
- **Security-First** - XSS protection with Jinja2 autoescape enabled
- **Modern Python** - Type hints, dataclasses, comprehensive error handling

### Configuration Standards
- **Line Length**: 120 characters (configured in `.flake8` and `pyproject.toml`)
- **Code Style**: Black-compatible formatting
- **Testing**: pytest with 77 comprehensive tests
- **Dependencies**: Managed with PDM

### Data Flow
1. **Collection** - GitLabClient fetches data from GitLab API
2. **Analysis** - GitLabAnalyzer processes and scores repositories
3. **Storage** - GitLabDataStorage handles caching and persistence
4. **Reporting** - HTMLReportGenerator creates interactive HTML reports

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

### Recent Improvements
- Package renamed from `gitlab_stats` to `glabmetrics` for consistency
- Modernized to 120-character line length standard
- Added comprehensive security and template testing
- Fixed GitLab version display in HTML reports
- Enhanced XSS protection testing

### Development Workflow
1. Use existing dataclasses (`RepositoryStats`, `SystemStats`)
2. Follow type hint conventions throughout
3. Add tests for all new functionality
4. Ensure linting passes with `pdm run lint`
5. Run full test suite before committing
6. Use descriptive commit messages following conventional commits

### GitLab API Compatibility
- **Primary Target**: GitLab 17.x+ (with detailed storage statistics)
- **Fallback Support**: Earlier versions with estimation algorithms
- **Rate Limiting**: Built-in retry and backoff mechanisms
- **Pagination**: Automatic handling of large datasets