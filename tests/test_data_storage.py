"""Tests for GitLab data storage and serialization."""

import pytest
import json
from datetime import datetime
from collections import defaultdict

from glabmetrics.data_storage import GitLabDataStorage
from glabmetrics.analyzer import RepositoryStats
from glabmetrics.performance_tracker import CollectionPerformanceStats


class TestGitLabDataStorage:
    """Test suite for GitLabDataStorage class."""

    def test_save_and_load_basic_data(self, temp_data_file, sample_repository_stats):
        """Test basic save and load functionality."""
        storage = GitLabDataStorage(str(temp_data_file))
        timestamp = datetime.now()

        # Save data
        storage.save_data([sample_repository_stats], timestamp)

        # Verify file exists
        assert temp_data_file.exists()

        # Load data
        loaded_repos, loaded_timestamp = storage.load_data()

        # Verify data integrity
        assert len(loaded_repos) == 1
        loaded_repo = loaded_repos[0]

        assert loaded_repo.id == sample_repository_stats.id
        assert loaded_repo.name == sample_repository_stats.name
        assert loaded_repo.size_mb == sample_repository_stats.size_mb
        assert loaded_repo.commit_count == sample_repository_stats.commit_count
        assert abs((loaded_timestamp - timestamp).total_seconds()) < 1

    def test_serialize_complex_objects(self, temp_data_file):
        """Test serialization of complex objects like defaultdict."""
        # Create repository with complex objects
        pipeline_details = defaultdict(int)
        pipeline_details["success"] = 45
        pipeline_details["failed"] = 5

        fetch_activity = defaultdict(list)
        fetch_activity["days"] = [
            {"date": "2025-07-25", "count": 15},
            {"date": "2025-07-24", "count": 8},
        ]

        nested_dict = defaultdict(dict)
        nested_dict["runners"]["docker-1"] = 25
        nested_dict["runners"]["docker-2"] = 20

        repo = RepositoryStats(
            id=123,
            name="complex-repo",
            path_with_namespace="test/complex-repo",
            size_mb=100.0,
            commit_count=50,
            contributor_count=5,
            last_activity=datetime.now(),
            is_orphaned=False,
            pipeline_details=pipeline_details,
            fetch_activity=fetch_activity,
            storage_stats=nested_dict,
            gitlab_version="17.2.1-ee",
        )

        storage = GitLabDataStorage(str(temp_data_file))

        # Should not raise any exceptions
        storage.save_data([repo], datetime.now())

        # Should load successfully
        loaded_repos, _ = storage.load_data()
        loaded_repo = loaded_repos[0]

        # Verify complex objects are preserved as regular dicts
        assert isinstance(loaded_repo.pipeline_details, dict)
        assert loaded_repo.pipeline_details["success"] == 45
        assert loaded_repo.pipeline_details["failed"] == 5

        assert isinstance(loaded_repo.fetch_activity, dict)
        assert loaded_repo.fetch_activity["days"][0]["count"] == 15

        assert isinstance(loaded_repo.storage_stats, dict)
        assert loaded_repo.storage_stats["runners"]["docker-1"] == 25

    def test_serialize_datetime_handling(self, temp_data_file):
        """Test proper datetime serialization and deserialization."""
        now = datetime.now()
        old_activity = datetime.min

        repo_with_activity = RepositoryStats(
            id=123,
            name="active-repo",
            path_with_namespace="test/active-repo",
            size_mb=100.0,
            commit_count=50,
            contributor_count=5,
            last_activity=now,
            is_orphaned=False,
            gitlab_version="17.2.1-ee",
        )

        repo_without_activity = RepositoryStats(
            id=124,
            name="inactive-repo",
            path_with_namespace="test/inactive-repo",
            size_mb=50.0,
            commit_count=10,
            contributor_count=1,
            last_activity=old_activity,
            is_orphaned=True,
            gitlab_version="17.2.1-ee",
        )

        storage = GitLabDataStorage(str(temp_data_file))
        storage.save_data([repo_with_activity, repo_without_activity], datetime.now())

        loaded_repos, _ = storage.load_data()

        # Active repo should have proper datetime
        active_repo = next(r for r in loaded_repos if r.name == "active-repo")
        assert abs((active_repo.last_activity - now).total_seconds()) < 1

        # Inactive repo should have datetime.min
        inactive_repo = next(r for r in loaded_repos if r.name == "inactive-repo")
        assert inactive_repo.last_activity == datetime.min

    def test_backward_compatibility_missing_fields(self, temp_data_file):
        """Test loading data with missing fields (backward compatibility)."""
        # Create JSON with missing new fields
        old_format_data = {
            "repositories": [
                {
                    "id": 123,
                    "name": "old-repo",
                    "path_with_namespace": "test/old-repo",
                    "size_mb": 100.0,
                    "commit_count": 50,
                    "contributor_count": 5,
                    "last_activity": None,
                    "is_orphaned": False,
                    "languages": {"Python": 100.0},
                    "pipeline_count": 10,
                    "open_mrs": 2,
                    "open_issues": 5,
                    "lfs_size_mb": 0.0,
                    "artifacts_size_mb": 0.0,
                    "packages_size_mb": 0.0,
                    "container_registry_size_mb": 0.0,
                    "binary_files": [],
                    # Missing: complexity_score, health_score, etc.
                }
            ],
            "analysis_timestamp": datetime.now().isoformat(),
            "version": "1.0",
        }

        # Write old format manually
        with open(temp_data_file, "w") as f:
            json.dump(old_format_data, f)

        storage = GitLabDataStorage(str(temp_data_file))
        loaded_repos, _ = storage.load_data()

        assert len(loaded_repos) == 1
        repo = loaded_repos[0]

        # Old fields should be preserved
        assert repo.name == "old-repo"
        assert repo.size_mb == 100.0

        # New fields should have default values
        assert repo.complexity_score == 0.0
        assert repo.health_score == 0.0
        assert repo.hotness_score == 0.0
        assert repo.gitlab_version == ""
        assert repo.fetch_activity == {}

    def test_save_with_performance_stats(self, temp_data_file, sample_repository_stats):
        """Test saving data with performance statistics."""
        perf_stats = CollectionPerformanceStats(
            total_duration=120.5,
            total_api_calls=150,
            total_failed_calls=2,
            api_blocks={
                "Project Discovery": {"duration": 30.2, "count": 50},
                "Commit History": {"duration": 45.8, "count": 75},
            },
            recommendations=["Use pagination for large datasets"],
        )

        storage = GitLabDataStorage(str(temp_data_file))
        storage.save_data([sample_repository_stats], datetime.now(), perf_stats)

        # Verify performance stats are in JSON
        with open(temp_data_file, "r") as f:
            data = json.load(f)

        assert "performance_stats" in data
        assert data["performance_stats"]["total_duration"] == 120.5
        assert data["performance_stats"]["total_api_calls"] == 150

    def test_data_exists_and_age(self, temp_data_file, sample_repository_stats):
        """Test data existence and age calculation."""
        storage = GitLabDataStorage(str(temp_data_file))

        # Initially no data
        assert not storage.data_exists()
        assert storage.get_data_age() == "No data file found"

        # Save data
        storage.save_data([sample_repository_stats], datetime.now())

        # Now data exists
        assert storage.data_exists()
        age = storage.get_data_age()
        assert "minutes old" in age or "seconds old" in age

    def test_corrupted_file_handling(self, temp_data_file):
        """Test handling of corrupted data files."""
        # Write invalid JSON
        with open(temp_data_file, "w") as f:
            f.write("invalid json content")

        storage = GitLabDataStorage(str(temp_data_file))

        with pytest.raises(Exception):  # Should raise JSONDecodeError or similar
            storage.load_data()

    def test_missing_file_handling(self):
        """Test handling of missing data files."""
        storage = GitLabDataStorage("nonexistent_file.json")

        with pytest.raises(FileNotFoundError):
            storage.load_data()

    def test_serialize_empty_and_none_values(self, temp_data_file):
        """Test serialization of empty and None values."""
        repo = RepositoryStats(
            id=123,
            name="minimal-repo",
            path_with_namespace="test/minimal-repo",
            size_mb=0.0,
            commit_count=0,
            contributor_count=0,
            last_activity=datetime.min,
            is_orphaned=False,
            languages={},  # Empty dict
            pipeline_details=defaultdict(int),  # Empty defaultdict
            fetch_activity=None,  # None value
            storage_stats={},
            gitlab_version="",
        )

        storage = GitLabDataStorage(str(temp_data_file))

        # Should handle empty/None values gracefully
        storage.save_data([repo], datetime.now())
        loaded_repos, _ = storage.load_data()

        loaded_repo = loaded_repos[0]
        assert loaded_repo.languages == {}
        assert loaded_repo.pipeline_details == {}
        assert loaded_repo.fetch_activity == {}
        assert loaded_repo.gitlab_version == ""

    def test_multiple_repositories_serialization(self, temp_data_file, multiple_repository_stats):
        """Test serialization of multiple repositories with different characteristics."""
        storage = GitLabDataStorage(str(temp_data_file))
        timestamp = datetime.now()

        storage.save_data(multiple_repository_stats, timestamp)
        loaded_repos, loaded_timestamp = storage.load_data()

        assert len(loaded_repos) == len(multiple_repository_stats)

        # Verify all repositories are preserved
        loaded_names = {repo.name for repo in loaded_repos}
        original_names = {repo.name for repo in multiple_repository_stats}
        assert loaded_names == original_names

        # Verify specific characteristics are preserved
        orphaned_repo = next(r for r in loaded_repos if r.is_orphaned)
        assert orphaned_repo.name == "old-project"
        assert orphaned_repo.health_score == 15.0

        large_repo = next(r for r in loaded_repos if r.lfs_size_mb > 100)
        assert large_repo.name == "large-dataset"
        assert large_repo.lfs_size_mb == 400.0


class TestSerializationHelpers:
    """Test serialization helper functions."""

    def test_serialize_complex_dict_with_nested_structures(self):
        """Test _serialize_complex_dict with deeply nested structures."""
        storage = GitLabDataStorage("dummy.json")

        complex_obj = defaultdict(lambda: defaultdict(list))
        complex_obj["level1"]["level2"].append("item1")
        complex_obj["level1"]["level2"].append("item2")
        complex_obj["level1"]["level3"].append("item3")

        result = storage._serialize_complex_dict(complex_obj)

        assert isinstance(result, dict)
        assert result["level1"]["level2"] == ["item1", "item2"]
        assert result["level1"]["level3"] == ["item3"]
