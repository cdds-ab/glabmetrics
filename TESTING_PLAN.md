# Unit-Test Plan für GitLab Statistics Analyzer

## Test-Framework Setup

### Dependencies
```bash
pip install pytest pytest-mock pytest-cov responses freezegun
```

### Test-Struktur
```
tests/
├── conftest.py                 # Pytest fixtures und Konfiguration
├── test_gitlab_client.py       # GitLab API Client Tests
├── test_analyzer.py            # Repository Analyzer Tests
├── test_data_storage.py        # Serialisierung/Caching Tests
├── test_report_generator.py    # HTML Report Generator Tests
├── test_performance_tracker.py # Performance Monitoring Tests
├── test_main.py               # CLI Integration Tests
├── fixtures/                  # Test-Daten und Mock-Responses
│   ├── gitlab_responses/      # JSON Mock-Responses
│   ├── test_repositories.json # Test Repository Daten
│   └── expected_reports/      # Erwartete HTML-Outputs
└── integration/               # End-to-End Integration Tests
    ├── test_full_workflow.py  # Kompletter Workflow
    └── test_caching.py        # Cache-Verhalten
```

## 1. GitLab Client Tests (`test_gitlab_client.py`)

### Test-Bereiche:
- **API Connection & Authentication**
  - Erfolgreiche Verbindung
  - Fehlgeschlagene Authentifizierung
  - Network-Timeouts und Retry-Logic

- **Version Detection**
  - GitLab 17.x Erkennung
  - Fallback für ältere Versionen
  - Unbekannte Versionen

- **Paginated Requests**
  - Korrekte Paginierung
  - Große Datenmengen (>100 Einträge)
  - Leere Antworten

- **API Endpoints**
  - Alle GET-Endpoints mit Mock-Daten
  - Fehlerbehandlung bei 404/403/500
  - Rate-Limiting-Verhalten

```python
# Beispiel-Test-Struktur
def test_get_projects_success(mock_gitlab_client, mock_responses):
    """Test successful project retrieval with pagination."""
    
def test_gitlab_version_detection_17x(mock_gitlab_client):
    """Test GitLab 17.x version detection."""
    
def test_api_error_handling(mock_gitlab_client):
    """Test proper handling of API errors."""
```

## 2. Analyzer Tests (`test_analyzer.py`)

### Test-Bereiche:
- **Repository Statistics Calculation**
  - Basis-Metriken (Size, Commits, Contributors)
  - Storage-Breakdown (LFS, Artifacts, Packages)
  - Activity-Timestamps mit Timezone-Handling

- **Scoring Algorithms**
  - Complexity Score (0-100)
  - Health Score (0-100)
  - Hotness Score (0-100)
  - Maintenance Score (0-100)
  - Edge-Cases (Division by Zero, leere Daten)

- **Advanced Analytics**
  - Pipeline Success Rate Berechnung
  - Language Diversity Scoring
  - Commit Frequency Calculation
  - Orphaned Repository Detection

- **Storage Analysis**
  - GitLab 17.x Storage API Integration
  - Fallback-Heuristiken für ältere Versionen
  - Artifacts Age Analysis

```python
# Test-Beispiele
def test_complexity_score_calculation():
    """Test repository complexity scoring algorithm."""
    
def test_health_score_with_old_activity():
    """Test health score calculation for inactive repos."""
    
def test_storage_breakdown_gitlab_17x():
    """Test accurate storage breakdown with GitLab 17.x APIs."""
```

## 3. Data Storage Tests (`test_data_storage.py`)

### Test-Bereiche:
- **Serialization/Deserialization**
  - RepositoryStats mit komplexen Objekten
  - defaultdict und nested structures
  - Datetime-Handling
  - Backward-Kompatibilität mit alten JSON-Formaten

- **Cache Management**
  - Save/Load Zyklen
  - Daten-Integrität
  - File-Locking und Concurrent Access
  - Korrupte Dateien

- **Schema Evolution**
  - Neue Felder hinzufügen
  - Fehlende Felder in alten Caches
  - Version-Migration

```python
def test_serialize_complex_objects():
    """Test serialization of defaultdict and complex structures."""
    
def test_backward_compatibility():
    """Test loading old cache format with missing fields."""
    
def test_concurrent_access():
    """Test thread-safe cache operations."""
```

## 4. Report Generator Tests (`test_report_generator.py`)

### Test-Bereiche:
- **HTML Generation**
  - Vollständige Reports mit allen Sections
  - Korrekte Chart.js Integration
  - Bootstrap CSS/JS Links

- **Template Rendering**
  - Jinja2 Template-Verarbeitung
  - Number Formatting
  - Date/Time Formatting
  - XSS-Prevention

- **Storage Charts**
  - Pie Chart mit korrekten Daten
  - Fallback für fehlende Storage-Details
  - Dynamic Chart Configuration

```python
def test_html_report_generation():
    """Test complete HTML report generation."""
    
def test_storage_chart_data():
    """Test storage breakdown chart data generation."""
    
def test_template_xss_prevention():
    """Test that user data is properly escaped."""
```

## 5. Performance Tracker Tests (`test_performance_tracker.py`)

### Test-Bereiche:
- **Timing Measurements**
  - API Block Timing
  - Total Duration Calculation
  - Nested Block Handling

- **Statistics Collection**
  - API Call Counting
  - Success/Failure Rates
  - Error Message Collection

- **Thematic Categorization**
  - Korrekte Block-Zuordnung
  - Performance Recommendations

```python
def test_api_block_timing():
    """Test accurate timing of API blocks."""
    
def test_nested_performance_blocks():
    """Test handling of nested timing blocks."""
    
def test_performance_statistics():
    """Test comprehensive performance statistics."""
```

## 6. CLI Integration Tests (`test_main.py`)

### Test-Bereiche:
- **Argument Parsing**
  - Alle CLI-Optionen
  - Fehlerhafte Parameter
  - Help-Output

- **Workflow Orchestration**
  - Fresh Data Collection
  - Cached Data Usage
  - Report Generation

- **Error Handling**
  - Connection Failures
  - Invalid Tokens
  - File Permission Errors

```python
def test_cli_fresh_data_collection(mock_gitlab_api):
    """Test CLI with fresh data collection."""
    
def test_cli_cached_data_usage():
    """Test CLI using cached data."""
    
def test_cli_error_handling():
    """Test CLI error scenarios."""
```

## 7. Integration Tests

### End-to-End Workflows
- **Complete Analysis Pipeline**
  - API → Analysis → Cache → Report
  - Performance Tracking Integration
  - Error Recovery

- **Cache Behavior**
  - Refresh vs. Cached Data
  - Data Age Calculation
  - Cache Invalidation

```python
def test_full_analysis_workflow():
    """Test complete analysis from API to report."""
    
def test_cache_refresh_behavior():
    """Test cache refresh vs. cached data workflows."""
```

## Mock-Strategien

### GitLab API Mocking
```python
# responses Library für HTTP-Mocking
@responses.activate
def test_api_endpoint():
    responses.add(responses.GET, 
                 'https://gitlab.example.com/api/v4/projects',
                 json=mock_projects_data)
```

### Test-Daten Generation
```python
# Factory Pattern für Test-Repositories
def create_test_repository(
    name="test-repo",
    size_mb=100.0,
    commit_count=50,
    is_orphaned=False,
    **kwargs
) -> RepositoryStats:
    return RepositoryStats(...)
```

### Time Mocking
```python
# freezegun für Datetime-Tests
@freeze_time("2025-07-26 12:00:00")
def test_activity_analysis():
    # Test mit fixiertem Zeitpunkt
```

## Coverage-Ziele

- **Minimum Coverage**: 80%
- **Critical Components**: 95%
  - Data Storage Serialization
  - Scoring Algorithms
  - API Error Handling

## Ausführung

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=glabmetrics --cov-report=html

# Spezifische Test-Kategorie
pytest tests/test_analyzer.py -v

# Performance Tests
pytest tests/test_performance_tracker.py --durations=10
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov responses freezegun
      - name: Run tests
        run: pytest --cov=glabmetrics --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test-Daten Management

### Fixtures Strategie
- **Small Fixtures**: Direkt in Tests definiert
- **Large Fixtures**: JSON-Dateien in `tests/fixtures/`
- **Dynamic Fixtures**: Factory Functions für variable Test-Daten

### Mock-Response Verwaltung
- **Real API Samples**: Echte GitLab API Responses als Basis
- **Edge Cases**: Spezielle Responses für Fehlerfälle
- **Version-Specific**: Unterschiedliche Responses für GitLab-Versionen