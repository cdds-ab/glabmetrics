"""Tests for GitLab analyzer and scoring algorithms."""

from datetime import datetime, timedelta

from glabmetrics.analyzer import GitLabAnalyzer


class TestGitLabAnalyzer:
    """Test suite for GitLabAnalyzer class."""

    def test_initialization(self, mock_gitlab_client):
        """Test analyzer initialization."""
        analyzer = GitLabAnalyzer(mock_gitlab_client)

        assert analyzer.client == mock_gitlab_client
        assert analyzer.repositories == []
        assert analyzer.system_stats is None
        assert analyzer.skip_binary_scan is False

    def test_initialization_without_client(self):
        """Test analyzer initialization without client (for cached data)."""
        analyzer = GitLabAnalyzer(None)

        assert analyzer.client is None
        assert analyzer.repositories == []


class TestRepositoryAnalysis:
    """Test repository analysis methods."""

    def test_analyze_project_basic_stats(
        self, mock_gitlab_client, sample_repository_data
    ):
        """Test basic project analysis statistics."""
        # Setup mock responses
        mock_gitlab_client.get_projects.return_value = [sample_repository_data]
        mock_gitlab_client.get_project_commits.return_value = [
            {"id": "abc123", "created_at": "2025-07-25T10:00:00Z"},
            {"id": "def456", "created_at": "2025-07-24T15:30:00Z"},
        ]
        mock_gitlab_client.get_project_contributors.return_value = [
            {"name": "Dev 1"},
            {"name": "Dev 2"},
            {"name": "Dev 3"},
        ]
        mock_gitlab_client.get_project_merge_requests.return_value = [
            {"id": 1, "state": "opened"}
        ]
        mock_gitlab_client.get_project_issues.return_value = [
            {"id": 1, "state": "opened"},
            {"id": 2, "state": "opened"},
        ]
        mock_gitlab_client.get_project_pipelines.return_value = [
            {"id": 1, "status": "success"},
            {"id": 2, "status": "success"},
        ]
        mock_gitlab_client.get_project_languages.return_value = {
            "Python": 70.0,
            "JavaScript": 30.0,
        }
        mock_gitlab_client.get_project_with_statistics.return_value = (
            sample_repository_data
        )
        mock_gitlab_client.get_project_packages.return_value = []
        mock_gitlab_client.get_project_container_registry.return_value = []
        mock_gitlab_client.get_project_job_artifacts_list.return_value = []
        mock_gitlab_client.get_project_lfs_objects.return_value = []
        mock_gitlab_client.get_gitlab_version.return_value = "17.2.1-ee"

        analyzer = GitLabAnalyzer(mock_gitlab_client)
        analyzer.collect_project_data()

        assert len(analyzer.repositories) == 1
        repo = analyzer.repositories[0]

        assert repo.id == 123
        assert repo.name == "test-repository"
        assert repo.size_mb == 100.0  # 104857600 bytes / (1024*1024)
        assert repo.commit_count == 2
        assert repo.contributor_count == 3
        assert repo.open_mrs == 1
        assert repo.open_issues == 2
        assert repo.pipeline_count == 2
        assert repo.gitlab_version == "17.2.1-ee"

    def test_orphaned_repository_detection(self, mock_gitlab_client):
        """Test detection of orphaned repositories."""
        old_activity = (datetime.now() - timedelta(days=200)).isoformat()

        old_repo_data = {
            "id": 124,
            "name": "old-repo",
            "path_with_namespace": "legacy/old-repo",
            "last_activity_at": old_activity,
            "statistics": {"repository_size": 26214400},
        }

        mock_gitlab_client.get_projects.return_value = [old_repo_data]
        mock_gitlab_client.get_project_commits.return_value = []
        mock_gitlab_client.get_project_contributors.return_value = []
        mock_gitlab_client.get_project_merge_requests.return_value = []
        mock_gitlab_client.get_project_issues.return_value = []
        mock_gitlab_client.get_project_pipelines.return_value = []
        mock_gitlab_client.get_project_languages.return_value = {}
        mock_gitlab_client.get_project_with_statistics.return_value = old_repo_data
        mock_gitlab_client.get_project_packages.return_value = []
        mock_gitlab_client.get_project_container_registry.return_value = []
        mock_gitlab_client.get_project_job_artifacts_list.return_value = []
        mock_gitlab_client.get_project_lfs_objects.return_value = []
        mock_gitlab_client.get_gitlab_version.return_value = "17.2.1-ee"

        analyzer = GitLabAnalyzer(mock_gitlab_client)
        analyzer.collect_project_data()

        repo = analyzer.repositories[0]
        assert repo.is_orphaned is True


class TestScoringAlgorithms:
    """Test scoring algorithm implementations."""

    def test_complexity_score_calculation(self):
        """Test complexity score calculation algorithm."""
        analyzer = GitLabAnalyzer(None)

        # High complexity project
        project = {"statistics": {"repository_size": 209715200}}  # 200MB
        languages = {"Python": 30, "JavaScript": 25, "Go": 20, "Rust": 15, "CSS": 10}
        commits = [{"id": f"commit_{i}"} for i in range(50)]  # 50 commits
        contributors = [{"name": f"dev_{i}"} for i in range(10)]  # 10 contributors

        score = analyzer._calculate_complexity_score(
            project, languages, commits, contributors
        )

        # Should be high due to language diversity, size/commit ratio, and contributors
        assert 60 <= score <= 100
        assert isinstance(score, float)

    def test_complexity_score_simple_project(self):
        """Test complexity score for simple project."""
        analyzer = GitLabAnalyzer(None)

        # Simple project
        project = {"statistics": {"repository_size": 1048576}}  # 1MB
        languages = {"Python": 100}  # Single language
        commits = [{"id": f"commit_{i}"} for i in range(100)]  # Many small commits
        contributors = [{"name": "single_dev"}]  # Single contributor

        score = analyzer._calculate_complexity_score(
            project, languages, commits, contributors
        )

        # Should be low due to single language, small size, single contributor
        assert 0 <= score <= 40

    def test_health_score_calculation(self):
        """Test health score calculation algorithm."""
        analyzer = GitLabAnalyzer(None)

        # Healthy project
        project = {"name": "healthy-project"}
        merge_requests = []  # No open MRs
        issues = []  # No open issues
        recent_activity = datetime.now() - timedelta(days=1)  # Recent activity

        score = analyzer._calculate_health_score(
            project, merge_requests, issues, recent_activity
        )

        # Should be high due to recent activity and no open issues/MRs
        assert 80 <= score <= 100

    def test_health_score_unhealthy_project(self):
        """Test health score for unhealthy project."""
        analyzer = GitLabAnalyzer(None)

        # Unhealthy project
        project = {"name": "unhealthy-project"}
        merge_requests = [{"id": i} for i in range(15)]  # Many open MRs
        issues = [{"id": i} for i in range(25)]  # Many open issues
        old_activity = datetime.now() - timedelta(days=200)  # Old activity

        score = analyzer._calculate_health_score(
            project, merge_requests, issues, old_activity
        )

        # Should be low due to old activity and many open issues/MRs
        assert 0 <= score <= 30

    def test_commit_frequency_calculation(self):
        """Test commit frequency calculation."""
        analyzer = GitLabAnalyzer(None)

        # Project created 100 days ago with 50 commits
        created_at = (datetime.now() - timedelta(days=100)).isoformat()
        commits = [{"id": f"commit_{i}"} for i in range(50)]

        frequency = analyzer._calculate_commit_frequency(commits, created_at)

        # Should be approximately 0.5 commits per day
        assert 0.4 <= frequency <= 0.6

    def test_hotness_score_calculation(self):
        """Test hotness score calculation."""
        analyzer = GitLabAnalyzer(None)

        # Hot project with recent activity
        fetch_activity = {
            "days": [
                {"date": "2025-07-25", "count": 20},
                {"date": "2025-07-24", "count": 15},
                {"date": "2025-07-23", "count": 10},
            ]
        }

        recent_commits = []
        for i in range(20):
            days_ago = i % 10  # Commits in last 10 days
            commit_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            recent_commits.append({"created_at": commit_date})

        recent_activity = datetime.now() - timedelta(hours=2)  # Very recent

        score = analyzer._calculate_hotness_score(
            fetch_activity, recent_commits, recent_activity
        )

        # Should be high due to recent fetches, commits, and activity
        assert 60 <= score <= 100

    def test_maintenance_score_calculation(self):
        """Test maintenance score calculation."""
        analyzer = GitLabAnalyzer(None)

        # Well-maintained project
        project = {"description": "A well-documented project"}
        last_activity = datetime.now() - timedelta(days=3)  # Recent activity
        merge_requests = []  # No open MRs
        issues = []  # No open issues

        score = analyzer._calculate_maintenance_score(
            project, last_activity, merge_requests, issues
        )

        # Should be high due to recent activity, no open issues/MRs, and description
        assert 70 <= score <= 100

    def test_pipeline_metrics_calculation(self):
        """Test pipeline success rate and duration calculation."""
        analyzer = GitLabAnalyzer(None)

        pipelines = [
            {"status": "success", "duration": 120},
            {"status": "success", "duration": 150},
            {"status": "success", "duration": 100},
            {"status": "failed", "duration": 80},
            {"status": "success", "duration": 110},
        ]

        success_rate, avg_duration = analyzer._calculate_pipeline_metrics(pipelines)

        # 4 success out of 5 = 80% success rate
        assert success_rate == 80.0

        # Average of durations (limited to first 20, but we have 5)
        expected_avg = (120 + 150 + 100 + 80 + 110) / 5
        assert avg_duration == expected_avg


class TestStorageAnalysis:
    """Test storage analysis methods."""

    def test_gitlab_17x_storage_breakdown(self, mock_gitlab_client):
        """Test GitLab 17.x storage API integration."""
        project_data = {
            "id": 123,
            "name": "storage-test",
            "path_with_namespace": "test/storage-test",
            "last_activity_at": datetime.now().isoformat(),
            "statistics": {
                "repository_size": 104857600,  # 100MB
                "lfs_objects_size": 52428800,  # 50MB
                "job_artifacts_size": 10485760,  # 10MB
                "pipeline_artifacts_size": 5242880,  # 5MB
            },
        }

        mock_gitlab_client.get_projects.return_value = [project_data]
        mock_gitlab_client.get_project_with_statistics.return_value = project_data
        mock_gitlab_client.get_project_commits.return_value = []
        mock_gitlab_client.get_project_contributors.return_value = []
        mock_gitlab_client.get_project_merge_requests.return_value = []
        mock_gitlab_client.get_project_issues.return_value = []
        mock_gitlab_client.get_project_pipelines.return_value = []
        mock_gitlab_client.get_project_languages.return_value = {}
        mock_gitlab_client.get_project_packages.return_value = []
        mock_gitlab_client.get_project_container_registry.return_value = []
        mock_gitlab_client.get_project_job_artifacts_list.return_value = []
        mock_gitlab_client.get_project_lfs_objects.return_value = []
        mock_gitlab_client.get_gitlab_version.return_value = "17.2.1-ee"

        analyzer = GitLabAnalyzer(mock_gitlab_client)
        analyzer.collect_project_data()

        repo = analyzer.repositories[0]

        # Storage should be correctly parsed from GitLab 17.x API
        assert repo.lfs_size_mb == 50.0
        assert repo.artifacts_size_mb == 15.0  # job_artifacts + pipeline_artifacts
        assert repo.storage_stats["repository_size"] == 104857600

    def test_old_artifacts_analysis(self, mock_gitlab_client):
        """Test analysis of old artifacts for cleanup recommendations."""
        project_data = {
            "id": 123,
            "name": "artifacts-test",
            "path_with_namespace": "test/artifacts-test",
            "last_activity_at": datetime.now().isoformat(),
            "statistics": {"repository_size": 52428800},
        }

        # Mock artifacts - some old, some recent
        old_date = (datetime.now() - timedelta(days=45)).isoformat()
        recent_date = (datetime.now() - timedelta(days=5)).isoformat()

        artifacts = [
            {
                "job_id": 1,
                "created_at": old_date,
                "artifact_size": 10485760,  # 10MB, old
                "artifact_filename": "old-build.zip",
            },
            {
                "job_id": 2,
                "created_at": recent_date,
                "artifact_size": 5242880,  # 5MB, recent
                "artifact_filename": "recent-build.zip",
            },
            {
                "job_id": 3,
                "created_at": old_date,
                "artifact_size": 15728640,  # 15MB, old
                "artifact_filename": "old-test-results.zip",
            },
        ]

        mock_gitlab_client.get_projects.return_value = [project_data]
        mock_gitlab_client.get_project_with_statistics.return_value = project_data
        mock_gitlab_client.get_project_commits.return_value = []
        mock_gitlab_client.get_project_contributors.return_value = []
        mock_gitlab_client.get_project_merge_requests.return_value = []
        mock_gitlab_client.get_project_issues.return_value = []
        mock_gitlab_client.get_project_pipelines.return_value = []
        mock_gitlab_client.get_project_languages.return_value = {}
        mock_gitlab_client.get_project_packages.return_value = []
        mock_gitlab_client.get_project_container_registry.return_value = []
        mock_gitlab_client.get_project_job_artifacts_list.return_value = artifacts
        mock_gitlab_client.get_project_lfs_objects.return_value = []
        mock_gitlab_client.get_gitlab_version.return_value = "17.2.1-ee"

        analyzer = GitLabAnalyzer(mock_gitlab_client)
        analyzer.collect_project_data()

        repo = analyzer.repositories[0]

        # Should identify 2 old artifacts (>30 days)
        assert repo.expired_artifacts_count == 2
        # Should calculate size of old artifacts: 10MB + 15MB = 25MB
        assert repo.old_artifacts_size_mb == 25.0


class TestSystemAnalysis:
    """Test system-wide analysis methods."""

    def test_get_analysis_results(self, multiple_repository_stats):
        """Test comprehensive analysis results generation."""
        analyzer = GitLabAnalyzer(None)
        analyzer.repositories = multiple_repository_stats

        results = analyzer.get_analysis_results()

        assert "system_stats" in results
        assert "repositories" in results
        assert "analysis_timestamp" in results
        assert "gitlab_version" in results

        system_stats = results["system_stats"]
        assert system_stats.total_repositories == 3
        assert system_stats.orphaned_repositories == 1
        assert len(system_stats.repositories_by_size) <= 10
        assert len(system_stats.most_active_repositories) <= 10

    def test_recommendations_generation(self, multiple_repository_stats):
        """Test optimization recommendations generation."""
        analyzer = GitLabAnalyzer(None)
        analyzer.repositories = multiple_repository_stats

        recommendations = analyzer._generate_recommendations()

        # Should detect orphaned repository (check for "6 months" text from recommendation)
        orphaned_rec = next(
            (r for r in recommendations if "6 months" in r or "activity" in r.lower()),
            None,
        )
        assert orphaned_rec is not None

        # Should detect GitLab version specific recommendations
        version_rec = next((r for r in recommendations if "17." in r), None)
        assert version_rec is not None
