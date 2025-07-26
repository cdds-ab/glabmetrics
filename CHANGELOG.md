# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial GitLab Stats Analyzer implementation
- Comprehensive GitLab API client with version detection
- Advanced repository analysis with scoring algorithms
- HTML report generation with Bootstrap 5 and Chart.js
- JSON-based caching system for performance optimization
- Docker support with multi-stage builds
- GitHub Actions CI/CD pipeline
- Comprehensive test suite with 65% coverage
- Semantic versioning with commitizen
- Pre-commit hooks for code quality

### Features
- **Repository Analysis**: Size, commits, contributors, activity tracking
- **Storage Breakdown**: LFS, artifacts, packages, container registry analysis
- **Advanced Scoring**: Complexity, health, hotness, maintenance algorithms
- **Pipeline Intelligence**: Success rates, runner usage, failure analysis
- **Performance Tracking**: Detailed API performance monitoring
- **GitLab 17.x Support**: Version-specific API endpoints for enhanced accuracy
- **Optimization Recommendations**: Automated cleanup suggestions

### Technical
- Python 3.9+ compatibility
- PDM for dependency management
- pytest with comprehensive test coverage
- Black + flake8 for code formatting
- Docker containerization
- Conventional commits with automatic changelog generation

## [1.0.0] - 2025-07-26

### Added
- Initial release of GitLab Stats Analyzer
- Core functionality for GitLab instance analysis
- HTML report generation with visualizations
- Caching system for improved performance
- Docker support for containerized deployment
- Comprehensive documentation and development setup