# Unit Test Plan for GitLab Statistics Analyzer

## Test Framework Setup

### Dependencies
```toml
[tool.pdm.dev-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.1",
    "responses>=0.23.3",
    "freezegun>=1.2.2",
]
```

### Test Structure
```
tests/
├── conftest.py              # Pytest fixtures and test configuration
├── test_gitlab_client.py    # GitLab API client tests
├── test_analyzer.py         # Analysis logic tests
├── test_data_storage.py     # Caching and serialization tests
└── integration/
    └── test_end_to_end.py   # Full workflow integration tests
```

### ✅ Aktueller Test Status (2025-07-28)
- **GitLab Client**: ✅ Vollständig getestet
- **Analyzer**: ✅ Core-Funktionen getestet
- **Data Storage**: ✅ Caching und Serialization getestet
- **Enhanced Report Generator**: ✅ Integriert in main.py
- **Enhanced KPI Analyzers**: ⚠️ Benötigen spezifische Tests

## Test Categories

### 1. GitLab Client Tests (`test_gitlab_client.py`)

**Coverage Target: 90%+**

#### Core Functionality
- ✅ Client initialization with URL and token
- ✅ Version detection (GitLab 13.x vs 17.x)
- ✅ Authentication validation
- ✅ Rate limiting handling
- ✅ Error handling for API failures

#### Repository Operations
- ✅ Repository listing with pagination
- ✅ Repository details fetching
- ✅ Statistics gathering (commits, contributors)
- ✅ Storage breakdown (repository size, LFS, artifacts)
- ✅ Binary file detection

#### System Operations
- ✅ System statistics (version, users, projects)
- ✅ Runner information
- ✅ License information

#### Performance Tracking
- ✅ API call timing
- ✅ Request counting
- ✅ Error rate tracking

### 2. Analyzer Tests (`test_analyzer.py`)

**Coverage Target: 85%+**

#### Scoring Algorithms
- ✅ Complexity score calculation
- ✅ Health score calculation
- ✅ Hotness score calculation
- ✅ Overall repository ranking

#### Data Processing
- ✅ Repository statistics aggregation
- ✅ Language detection and categorization
- ✅ Contributor analysis
- ✅ Activity pattern recognition

#### Optimization Recommendations
- ✅ Orphaned repository detection
- ✅ Large file identification
- ✅ Cleanup suggestions generation

### 3. Data Storage Tests (`test_data_storage.py`)

**Coverage Target: 95%+**

#### Serialization
- ✅ Complex object serialization (RepositoryStats, SystemStats)
- ✅ DateTime handling
- ✅ defaultdict serialization
- ✅ Nested object structures

#### Caching Logic
- ✅ Cache file creation and reading
- ✅ Cache invalidation (24-hour rule)
- ✅ Partial cache updates
- ✅ Cache corruption handling

#### File Operations
- ✅ JSON file I/O operations
- ✅ File locking for concurrent access
- ✅ Backup and recovery mechanisms

### 4. Enhanced KPI Analyzer Tests (Neue Priorität)

**Coverage Target: 85%+**

#### P1-P6 Analyzer Tests
- ⚠️ **Enhanced Issue Analyzer**: Parallel processing, KPI calculation
- ⚠️ **Enhanced MR Analyzer**: Code review metrics, merge patterns
- ⚠️ **Enhanced CI Analyzer**: Runner usage, pipeline efficiency
- ⚠️ **Enhanced CI Config**: Configuration validation, best practices
- ⚠️ **Enhanced Submodule**: Dependency analysis, network graphs
- ⚠️ **Enhanced Performance**: Storage optimization, binary detection

#### Dashboard Integration Tests
- ⚠️ **Actionable Dashboard**: Critical issues generation
- ⚠️ **Performance Dashboard**: Optimization recommendations
- ⚠️ **Comprehensive Dashboard**: Multi-tab functionality

## Test Execution Strategy

### Local Development
```bash
# Run all tests
pdm run test

# Run with coverage
pdm run test-cov

# Run specific test file
pdm run test tests/test_analyzer.py

# Run tests matching pattern
pdm run test -k "test_complexity"
```

### Fast Development Cycle
```bash
# Stop on first failure for quick feedback
pdm run test-fast
```

### Coverage Analysis
```bash
# Generate HTML coverage report
pdm run test-cov
open htmlcov/index.html
```

## Mocking Strategy

### GitLab API Responses
```python
@responses.activate
def test_repository_fetching():
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects",
        json=[{"id": 1, "name": "test-repo"}],
        status=200
    )
```

### Time-Based Testing
```python
@freeze_time("2023-01-01 12:00:00")
def test_cache_expiration():
    # Test cache invalidation logic
```

### File System Operations
```python
def test_cache_storage(tmp_path):
    # Use pytest's tmp_path for file operations
```

## Performance Testing

### Benchmarks
- Repository processing speed (>100 repos/minute)
- Memory usage limits (<500MB for 1000 repositories)
- Cache I/O performance (<1s for 100MB cache files)

### Load Testing
```python
def test_large_dataset_processing():
    # Test with 1000+ mock repositories
    # Verify memory usage stays reasonable
    # Check processing time limits
```

## Integration Testing

### End-to-End Workflow
```python
def test_complete_analysis_workflow():
    # Mock GitLab API responses
    # Run full analysis
    # Verify HTML report generation
    # Check cache creation
```

### Docker Integration
```bash
# Test Docker image functionality
docker build -t glabmetrics:test .
docker run --rm glabmetrics:test --help
```

## Continuous Integration

### GitHub Actions Integration
```yaml
- name: Run tests with coverage
  run: |
    pdm run test-cov

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Test Matrix
- Python versions: 3.9, 3.10, 3.11, 3.12
- Operating systems: Ubuntu, macOS, Windows
- Dependencies: Latest and pinned versions

## Quality Gates

### Required Coverage
- **Overall**: 85%+
- **Critical modules**: 90%+
- **New features**: 95%+

### Test Performance
- **Test suite runtime**: <60 seconds
- **Individual test**: <5 seconds
- **Integration tests**: <30 seconds

### Code Quality
- All tests must pass
- No test warnings or deprecation notices
- Consistent test naming and structure
- Comprehensive docstrings for complex test scenarios

## Test Data Management

### Mock Data Generation
```python
def create_mock_repository_stats():
    return RepositoryStats(
        id=1,
        name="test-repo",
        size_mb=100.0,
        commits=500,
        contributors=10,
        # ... additional realistic test data
    )
```

### Fixture Organization
- Common fixtures in `conftest.py`
- Test-specific fixtures in individual test files
- Parameterized fixtures for different scenarios

This comprehensive test plan ensures reliable, maintainable code with high confidence in functionality and performance.
