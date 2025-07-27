"""Pytest fixtures and configuration for GitLab Stats Analyzer tests."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

from glabmetrics.analyzer import RepositoryStats, SystemStats
from glabmetrics.gitlab_client import GitLabClient
from glabmetrics.performance_tracker import PerformanceTracker


@pytest.fixture
def sample_repository_data() -> Dict[str, Any]:
    """Sample GitLab repository data as returned by API."""
    return {
        "id": 123,
        "name": "test-repository",
        "path_with_namespace": "group/test-repository",
        "last_activity_at": "2025-07-25T10:30:00Z",
        "created_at": "2024-01-15T09:00:00Z",
        "default_branch": "main",
        "description": "A test repository for unit testing",
        "statistics": {
            "repository_size": 104857600,  # 100MB
            "lfs_objects_size": 52428800,  # 50MB
            "job_artifacts_size": 10485760,  # 10MB
            "pipeline_artifacts_size": 5242880,  # 5MB
        },
    }


@pytest.fixture
def sample_repository_stats() -> RepositoryStats:
    """Sample RepositoryStats object for testing."""
    return RepositoryStats(
        id=123,
        name="test-repository",
        path_with_namespace="group/test-repository",
        size_mb=100.0,
        commit_count=150,
        contributor_count=5,
        last_activity=datetime(2025, 7, 25, 10, 30, 0),
        is_orphaned=False,
        languages={"Python": 70.5, "JavaScript": 25.2, "HTML": 4.3},
        storage_stats={
            "repository_size": 104857600,
            "lfs_objects_size": 52428800,
            "job_artifacts_size": 10485760,
        },
        pipeline_count=50,
        open_mrs=3,
        open_issues=8,
        lfs_size_mb=50.0,
        artifacts_size_mb=15.0,
        packages_size_mb=0.0,
        container_registry_size_mb=0.0,
        binary_files=["assets/logo.png", "docs/manual.pdf"],
        complexity_score=65.5,
        health_score=85.2,
        hotness_score=45.8,
        maintenance_score=75.0,
        language_diversity=3,
        commit_frequency=2.5,
        default_branch="main",
        pipeline_success_rate=92.5,
        avg_pipeline_duration=180.0,
        pipeline_details={
            "total_pipelines": 50,
            "status_distribution": {"success": 45, "failed": 3, "canceled": 2},
            "runner_usage": {"docker-runner-1": 30, "docker-runner-2": 20},
        },
        job_artifacts_details=[
            {
                "job_id": 1001,
                "job_name": "build",
                "created_at": "2025-07-20T10:00:00Z",
                "artifact_size": 5242880,
                "artifact_filename": "build-artifacts.zip",
            }
        ],
        lfs_objects_details=[
            {"path": "assets/large-image.png", "size": 26214400, "type": "large_file"}
        ],
        expired_artifacts_count=2,
        old_artifacts_size_mb=8.5,
        gitlab_version="17.2.1-ee",
        fetch_activity={
            "days": [
                {"date": "2025-07-25", "count": 15},
                {"date": "2025-07-24", "count": 8},
            ]
        },
    )


@pytest.fixture
def multiple_repository_stats(sample_repository_stats) -> List[RepositoryStats]:
    """Multiple RepositoryStats objects for testing aggregations."""
    repos = []

    # Active repository
    repos.append(sample_repository_stats)

    # Orphaned repository
    orphaned = RepositoryStats(
        id=124,
        name="old-project",
        path_with_namespace="legacy/old-project",
        size_mb=25.0,
        commit_count=20,
        contributor_count=2,
        last_activity=datetime.now() - timedelta(days=200),  # 200 days old
        is_orphaned=True,
        languages={"PHP": 90.0, "CSS": 10.0},
        complexity_score=25.0,
        health_score=15.0,
        hotness_score=5.0,
        maintenance_score=20.0,
        gitlab_version="17.2.1-ee",
    )
    repos.append(orphaned)

    # Large repository with LFS
    large_repo = RepositoryStats(
        id=125,
        name="large-dataset",
        path_with_namespace="data/large-dataset",
        size_mb=500.0,
        commit_count=75,
        contributor_count=3,
        last_activity=datetime.now() - timedelta(days=5),
        is_orphaned=False,
        languages={"Python": 60.0, "R": 40.0},
        lfs_size_mb=400.0,
        artifacts_size_mb=50.0,
        complexity_score=80.0,
        health_score=70.0,
        hotness_score=85.0,
        maintenance_score=65.0,
        gitlab_version="17.2.1-ee",
    )
    repos.append(large_repo)

    return repos


@pytest.fixture
def sample_system_stats(multiple_repository_stats) -> SystemStats:
    """Sample SystemStats object for testing."""
    return SystemStats(
        total_repositories=3,
        total_size_gb=6.25,  # (100 + 25 + 500) MB / 1024
        total_users=15,
        active_users_30d=8,
        total_commits=245,  # 150 + 20 + 75
        orphaned_repositories=1,
        repositories_with_lfs=1,
        total_lfs_size_gb=0.43,  # 450 MB / 1024
        total_artifacts_size_gb=0.063,  # 65 MB / 1024
        total_packages_size_gb=0.0,
        total_container_registry_size_gb=0.0,
        repositories_by_size=sorted(
            multiple_repository_stats, key=lambda r: r.size_mb, reverse=True
        ),
        activity_by_month={"2025-07": 225, "2025-01": 20},
        most_active_repositories=sorted(
            multiple_repository_stats, key=lambda r: r.commit_count, reverse=True
        ),
        optimization_recommendations=[
            "Found 1 repositories with no activity in the last 6 months.",
            "Found 1 repositories with more than 400MB of LFS data.",
        ],
        most_complex_repositories=sorted(
            multiple_repository_stats, key=lambda r: r.complexity_score, reverse=True
        ),
        healthiest_repositories=sorted(
            multiple_repository_stats, key=lambda r: r.health_score, reverse=True
        ),
        hottest_repositories=sorted(
            multiple_repository_stats, key=lambda r: r.hotness_score, reverse=True
        ),
        language_distribution={"Python": 2, "JavaScript": 1, "PHP": 1, "R": 1},
        avg_complexity_score=56.83,
        avg_health_score=56.73,
        fetch_heatmap_data={"2025-07-25": 15, "2025-07-24": 8},
        pipeline_success_rate=92.5,
        default_branch_stats={"main": 2, "master": 1},
    )


@pytest.fixture
def mock_gitlab_client(mocker) -> Mock:
    """Mock GitLab client for testing."""
    client = mocker.Mock(spec=GitLabClient)
    client.gitlab_version = "17.2.1-ee"
    client.get_gitlab_version.return_value = "17.2.1-ee"
    client.test_connection.return_value = True
    return client


@pytest.fixture
def mock_performance_tracker() -> Mock:
    """Mock performance tracker for testing."""
    tracker = Mock(spec=PerformanceTracker)
    tracker.get_performance_stats.return_value = Mock(
        total_duration=120.5, total_api_calls=150, total_failed_calls=2
    )
    return tracker


@pytest.fixture
def sample_gitlab_projects_response() -> List[Dict]:
    """Sample GitLab projects API response."""
    return [
        {
            "id": 123,
            "name": "test-repository",
            "path_with_namespace": "group/test-repository",
            "last_activity_at": "2025-07-25T10:30:00Z",
            "created_at": "2024-01-15T09:00:00Z",
            "default_branch": "main",
            "statistics": {
                "repository_size": 104857600,
                "lfs_objects_size": 52428800,
                "job_artifacts_size": 10485760,
            },
        },
        {
            "id": 124,
            "name": "old-project",
            "path_with_namespace": "legacy/old-project",
            "last_activity_at": "2024-12-01T10:30:00Z",
            "created_at": "2023-06-15T09:00:00Z",
            "default_branch": "master",
            "statistics": {"repository_size": 26214400},
        },
    ]


@pytest.fixture
def sample_commits_response() -> List[Dict]:
    """Sample GitLab commits API response."""
    return [
        {
            "id": "abc123",
            "title": "Add new feature",
            "created_at": "2025-07-25T09:00:00Z",
            "author_name": "Developer 1",
        },
        {
            "id": "def456",
            "title": "Fix bug in module",
            "created_at": "2025-07-24T15:30:00Z",
            "author_name": "Developer 2",
        },
    ]


@pytest.fixture
def sample_pipelines_response() -> List[Dict]:
    """Sample GitLab pipelines API response."""
    return [
        {
            "id": 1001,
            "status": "success",
            "created_at": "2025-07-25T08:00:00Z",
            "duration": 180,
        },
        {
            "id": 1002,
            "status": "failed",
            "created_at": "2025-07-24T16:00:00Z",
            "duration": 95,
        },
    ]


@pytest.fixture
def temp_data_file(tmp_path) -> Path:
    """Temporary file path for testing data storage."""
    return tmp_path / "test_gitlab_data.json"


@pytest.fixture
def temp_report_file(tmp_path) -> Path:
    """Temporary file path for testing report generation."""
    return tmp_path / "test_report.html"


@pytest.fixture
def sample_analysis_results(
    sample_system_stats, multiple_repository_stats
) -> Dict[str, Any]:
    """Sample complete analysis results for testing."""
    return {
        "system_stats": sample_system_stats,
        "repositories": multiple_repository_stats,
        "analysis_timestamp": datetime.now().isoformat(),
        "gitlab_version": "17.2.1-ee",
        "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


# Test data helper functions
def create_repository_stats(**overrides) -> RepositoryStats:
    """Factory function to create RepositoryStats with custom values."""
    defaults = {
        "id": 999,
        "name": "factory-repo",
        "path_with_namespace": "test/factory-repo",
        "size_mb": 50.0,
        "commit_count": 25,
        "contributor_count": 3,
        "last_activity": datetime.now(),
        "is_orphaned": False,
        "gitlab_version": "17.2.1-ee",
    }
    defaults.update(overrides)
    return RepositoryStats(**defaults)


def create_mock_api_response(data: Any, status_code: int = 200) -> Mock:
    """Create a mock HTTP response for API testing."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = data
    response.raise_for_status.side_effect = (
        None if status_code < 400 else Exception(f"HTTP {status_code}")
    )
    return response
