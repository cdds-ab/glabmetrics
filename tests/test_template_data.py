"""Tests for template data preparation and handling."""

from datetime import datetime
import json

from glabmetrics.report_generator import HTMLReportGenerator
from glabmetrics.analyzer import RepositoryStats, SystemStats


class TestTemplateDataPreparation:
    """Test template data preparation logic."""

    def test_empty_system_stats_handling(self):
        """Test handling when system_stats is None or missing."""
        # Test with None system_stats
        analysis_results = {
            "system_stats": None,
            "repositories": [],
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Should return empty template data
        assert template_data["system_stats"]["total_repositories"] == 0
        assert template_data["system_stats"]["total_size_gb"] == 0.0
        assert template_data["repositories"] == []
        assert template_data["gitlab_version"] == "Unknown"

    def test_storage_breakdown_generation(self):
        """Test storage breakdown calculation logic."""
        # Test with detailed storage data
        system_stats = SystemStats(
            total_repositories=3,
            total_size_gb=10.0,
            total_users=5,
            active_users_30d=3,
            total_commits=100,
            orphaned_repositories=0,
            repositories_with_lfs=1,
            total_lfs_size_gb=2.5,
            total_artifacts_size_gb=1.5,
            total_packages_size_gb=0.5,
            total_container_registry_size_gb=1.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Check storage breakdown contains expected categories
        storage_breakdown = template_data["storage_breakdown"]
        assert "Repository Code" in storage_breakdown
        assert "LFS Objects" in storage_breakdown
        assert "CI/CD Artifacts" in storage_breakdown
        assert "Packages" in storage_breakdown
        assert "Container Images" in storage_breakdown

        # Check values are correct
        assert storage_breakdown["Repository Code"] == 10.0
        assert storage_breakdown["LFS Objects"] == 2.5
        assert storage_breakdown["CI/CD Artifacts"] == 1.5

        # Check JSON is valid
        storage_json = json.loads(template_data["storage_breakdown_json"])
        assert storage_json == storage_breakdown

    def test_repository_size_based_breakdown(self):
        """Test fallback to repository size-based breakdown."""
        # Create repositories with different sizes
        repos = [
            RepositoryStats(
                id=1, name="large-repo", path_with_namespace="group/large-repo",
                size_mb=500.0, commit_count=100, contributor_count=5,
                last_activity=datetime.now(), is_orphaned=False
            ),
            RepositoryStats(
                id=2, name="medium-repo", path_with_namespace="group/medium-repo",
                size_mb=50.0, commit_count=20, contributor_count=2,
                last_activity=datetime.now(), is_orphaned=False
            ),
            RepositoryStats(
                id=3, name="small-repo", path_with_namespace="group/small-repo",
                size_mb=5.0, commit_count=10, contributor_count=1,
                last_activity=datetime.now(), is_orphaned=False
            )
        ]

        # System stats with minimal storage detail (triggers fallback)
        system_stats = SystemStats(
            total_repositories=3,
            total_size_gb=0.555,  # About 555MB total
            total_users=5,
            active_users_30d=3,
            total_commits=130,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": repos,
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Should use repository-based breakdown
        storage_breakdown = template_data["storage_breakdown"]

        # Check for repository category labels
        category_keys = list(storage_breakdown.keys())
        assert any("Large Repositories" in key for key in category_keys)
        assert any("Medium Repositories" in key for key in category_keys)
        assert any("Small Repositories" in key for key in category_keys)

    def test_repository_data_transformation(self):
        """Test repository data transformation for template."""
        repo = RepositoryStats(
            id=123,
            name="test-repo",
            path_with_namespace="group/test-repo",
            size_mb=1500.5,
            commit_count=250,
            contributor_count=12,
            last_activity=datetime(2025, 7, 20, 15, 30, 45),
            is_orphaned=False,
            pipeline_count=45,
            open_mrs=3,
            open_issues=7,
            lfs_size_mb=123.45,
            artifacts_size_mb=67.89,
            complexity_score=85.7,
            health_score=92.3,
            hotness_score=76.1,
            maintenance_score=88.4,
            language_diversity=5,
            commit_frequency=1.234567,
            default_branch="main",
            pipeline_success_rate=94.2,
            avg_pipeline_duration=125.6,
            binary_files=["file1.exe", "file2.dll", "file3.zip"]
        )

        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=1.5,
            total_users=12,
            active_users_30d=8,
            total_commits=250,
            orphaned_repositories=0,
            repositories_with_lfs=1,
            total_lfs_size_gb=0.12,
            total_artifacts_size_gb=0.07,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [repo],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        repo_data = template_data["repositories"][0]

        # Test numeric rounding
        assert repo_data["size_mb"] == 1500.5
        assert repo_data["lfs_size_mb"] == 123.45
        assert repo_data["artifacts_size_mb"] == 67.89
        assert repo_data["complexity_score"] == 85.7
        assert repo_data["health_score"] == 92.3
        assert repo_data["commit_frequency"] == 1.235  # Rounded to 3 decimal places

        # Test date formatting
        assert repo_data["last_activity"] == "2025-07-20"

        # Test derived fields
        assert repo_data["binary_files_count"] == 3

        # Test integer fields
        assert repo_data["commit_count"] == 250
        assert repo_data["contributor_count"] == 12

    def test_repository_sorting_and_filtering(self):
        """Test repository sorting and filtering for different views."""
        repos = [
            RepositoryStats(
                id=1, name="huge-repo", path_with_namespace="group/huge-repo",
                size_mb=2000.0, commit_count=50, contributor_count=2,
                last_activity=datetime.now(), is_orphaned=False,
                complexity_score=95.0, health_score=60.0, hotness_score=40.0,
                lfs_size_mb=100.0, binary_files=["big.exe"]
            ),
            RepositoryStats(
                id=2, name="active-repo", path_with_namespace="group/active-repo",
                size_mb=100.0, commit_count=1000, contributor_count=10,
                last_activity=datetime.now(), is_orphaned=False,
                complexity_score=70.0, health_score=95.0, hotness_score=90.0,
                lfs_size_mb=0.0, binary_files=[]
            ),
            RepositoryStats(
                id=3, name="orphan-repo", path_with_namespace="legacy/orphan-repo",
                size_mb=50.0, commit_count=10, contributor_count=1,
                last_activity=datetime(2024, 1, 1), is_orphaned=True,
                complexity_score=30.0, health_score=20.0, hotness_score=5.0,
                lfs_size_mb=0.0, binary_files=["old.dll", "legacy.exe"]
            )
        ]

        system_stats = SystemStats(
            total_repositories=3,
            total_size_gb=2.15,
            total_users=13,
            active_users_30d=10,
            total_commits=1060,
            orphaned_repositories=1,
            repositories_with_lfs=1,
            total_lfs_size_gb=0.1,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": repos,
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Test largest repos (sorted by size)
        largest_repos = template_data["largest_repos"]
        assert largest_repos[0]["size_mb"] >= largest_repos[1]["size_mb"]
        assert largest_repos[0]["path_with_namespace"] == "group/huge-repo"

        # Test most active repos (sorted by commits)
        most_active = template_data["most_active_repos"]
        assert most_active[0]["commit_count"] >= most_active[1]["commit_count"]
        assert most_active[0]["path_with_namespace"] == "group/active-repo"

        # Test orphaned repos filtering
        orphaned_repos = template_data["orphaned_repos"]
        assert len(orphaned_repos) == 1
        assert orphaned_repos[0]["path_with_namespace"] == "legacy/orphan-repo"

        # Test LFS repos filtering
        lfs_repos = template_data["lfs_repos"]
        assert len(lfs_repos) == 1
        assert lfs_repos[0]["lfs_size_mb"] > 0

        # Test binary heavy repos filtering
        binary_heavy = template_data["binary_heavy_repos"]
        assert len(binary_heavy) == 1  # Only orphan-repo has binary files but no LFS
        assert binary_heavy[0]["path_with_namespace"] == "legacy/orphan-repo"

        # Test complex scoring sorts
        most_complex = template_data["most_complex_repos"]
        assert most_complex[0]["complexity_score"] >= most_complex[1]["complexity_score"]

        healthiest = template_data["healthiest_repos"]
        assert healthiest[0]["health_score"] >= healthiest[1]["health_score"]

        hottest = template_data["hottest_repos"]
        assert hottest[0]["hotness_score"] >= hottest[1]["hotness_score"]

    def test_json_serialization_safety(self):
        """Test that all JSON fields are properly serializable."""
        # Create data with complex nested structures
        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=1.0,
            total_users=1,
            active_users_30d=1,
            total_commits=10,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0,
            language_distribution={"Python": 50, "JavaScript": 30, "HTML": 20},
            fetch_heatmap_data={"2025-07-26": 15, "2025-07-25": 10}
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Test that all JSON fields are valid JSON
        json_fields = [
            'storage_breakdown_json',
            'language_distribution_json',
            'fetch_heatmap_json'
        ]

        for field in json_fields:
            json_str = template_data[field]
            assert isinstance(json_str, str), f"{field} should be a string"

            # Should be valid JSON
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict), f"{field} should parse to a dict"

        # Test specific content
        lang_data = json.loads(template_data['language_distribution_json'])
        assert lang_data["Python"] == 50
        assert lang_data["JavaScript"] == 30

        heatmap_data = json.loads(template_data['fetch_heatmap_json'])
        assert "2025-07-26" in heatmap_data
        assert heatmap_data["2025-07-26"] == 15
