"""Tests for GitLab API client."""

import responses
import unittest.mock
from requests.exceptions import Timeout

from glabmetrics.gitlab_client import GitLabClient


class TestGitLabClientInitialization:
    """Test GitLab client initialization."""

    def test_initialization_basic(self):
        """Test basic client initialization."""
        client = GitLabClient("https://gitlab.example.com", "test-token")

        assert client.gitlab_url == "https://gitlab.example.com"
        assert client.api_url == "https://gitlab.example.com/api/v4/"
        assert client.token == "test-token"
        assert client.gitlab_version is None
        assert client.session.headers["Private-Token"] == "test-token"

    def test_initialization_with_performance_tracker(self, mock_performance_tracker):
        """Test initialization with performance tracker."""
        client = GitLabClient("https://gitlab.example.com", "test-token", mock_performance_tracker)

        assert client.performance_tracker == mock_performance_tracker

    def test_url_normalization(self):
        """Test URL normalization (trailing slash removal)."""
        client = GitLabClient("https://gitlab.example.com/", "test-token")
        assert client.gitlab_url == "https://gitlab.example.com"
        assert client.api_url == "https://gitlab.example.com/api/v4/"


class TestConnection:
    """Test connection and authentication."""

    @responses.activate
    def test_successful_connection(self):
        """Test successful connection and authentication."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/user",
            json={"id": 1, "username": "admin"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/version",
            json={"version": "17.2.1-ee"},
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "valid-token")
        assert client.test_connection() is True
        assert client.gitlab_version == "17.2.1-ee"

    @responses.activate
    def test_failed_authentication(self):
        """Test failed authentication."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/user",
            json={"message": "401 Unauthorized"},
            status=401,
        )

        client = GitLabClient("https://gitlab.example.com", "invalid-token")
        assert client.test_connection() is False

    @responses.activate
    def test_connection_error(self):
        """Test network connection error."""
        # No responses added - will cause ConnectionError

        client = GitLabClient("https://unreachable.example.com", "token")
        assert client.test_connection() is False


class TestVersionDetection:
    """Test GitLab version detection."""

    @responses.activate
    def test_version_detection_from_version_endpoint(self):
        """Test version detection from /version endpoint."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/user",
            json={"id": 1},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/version",
            json={"version": "17.2.1-ee", "revision": "abc123"},
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        client.test_connection()

        assert client.get_gitlab_version() == "17.2.1-ee"

    @responses.activate
    def test_version_detection_fallback(self):
        """Test version detection fallback methods."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/user",
            json={"id": 1},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/version",
            status=404,  # Version endpoint not available
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/application/statistics",
            status=403,  # Statistics endpoint exists but forbidden
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/admin/usage_trends/measurements",
            status=403,  # GitLab 17.x endpoint exists
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        client.test_connection()

        assert "17.x+ (estimated from API availability)" in client.get_gitlab_version()

    @responses.activate
    def test_version_detection_unknown(self):
        """Test version detection when all methods fail."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/user",
            json={"id": 1},
            status=200,
        )
        responses.add(responses.GET, "https://gitlab.example.com/api/v4/version", status=404)
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/application/statistics",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/admin/usage_trends/measurements",
            status=404,
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        client.test_connection()

        assert "Unknown (< 17.0 estimated)" in client.get_gitlab_version()


class TestPaginatedRequests:
    """Test paginated API requests."""

    @responses.activate
    def test_single_page_request(self, sample_gitlab_projects_response):
        """Test request that fits in single page."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=sample_gitlab_projects_response,
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        projects = client._make_request("projects")

        assert len(projects) == len(sample_gitlab_projects_response)
        assert projects[0]["name"] == "test-repository"

    @responses.activate
    def test_multi_page_request(self):
        """Test request with multiple pages."""
        # First page
        page1_data = [{"id": i, "name": f"repo_{i}"} for i in range(1, 101)]  # 100 items
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=page1_data,
            status=200,
        )

        # Second page
        page2_data = [{"id": i, "name": f"repo_{i}"} for i in range(101, 151)]  # 50 items
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=page2_data,
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        projects = client._make_request("projects")

        assert len(projects) == 150
        assert projects[0]["name"] == "repo_1"
        assert projects[-1]["name"] == "repo_150"

    @responses.activate
    def test_empty_response(self):
        """Test handling of empty API response."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=[],
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        projects = client._make_request("projects")

        assert projects == []


class TestErrorHandling:
    """Test API error handling."""

    @responses.activate
    def test_http_error_handling(self, mock_performance_tracker):
        """Test handling of HTTP errors."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json={"message": "404 Not Found"},
            status=404,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        projects = client._make_request("projects")

        assert projects == []
        # Should track failed API call
        mock_performance_tracker.add_api_call.assert_called_with(
            "API Requests", success=False, error_message=unittest.mock.ANY
        )

    @responses.activate
    def test_network_timeout_handling(self, mock_performance_tracker):
        """Test handling of network timeouts."""

        def timeout_callback(request):
            raise Timeout("Request timed out")

        responses.add_callback(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            callback=timeout_callback,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        projects = client._make_request("projects")

        assert projects == []

    @responses.activate
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON responses."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            body="invalid json content",
            status=200,
            content_type="application/json",
        )

        client = GitLabClient("https://gitlab.example.com", "token")
        projects = client._make_request("projects")

        assert projects == []


class TestSpecificEndpoints:
    """Test specific API endpoints."""

    @responses.activate
    def test_get_projects(self, sample_gitlab_projects_response, mock_performance_tracker):
        """Test get_projects method."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=sample_gitlab_projects_response,
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        projects = client.get_projects()

        assert len(projects) == 2
        assert projects[0]["name"] == "test-repository"

        # Should track performance block
        mock_performance_tracker.start_api_block.assert_called_with("Project Discovery")
        mock_performance_tracker.end_api_block.assert_called_with("Project Discovery", 2)

    @responses.activate
    def test_get_project_commits(self, sample_commits_response, mock_performance_tracker):
        """Test get_project_commits method."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/123/repository/commits",
            json=sample_commits_response,
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        commits = client.get_project_commits(123)

        assert len(commits) == 2
        assert commits[0]["title"] == "Add new feature"

        # Should track performance block
        mock_performance_tracker.start_api_block.assert_called_with("Commit History")
        mock_performance_tracker.end_api_block.assert_called_with("Commit History", 2)

    @responses.activate
    def test_get_project_with_statistics(self, mock_performance_tracker):
        """Test get_project_with_statistics method for GitLab 17.x."""
        detailed_stats = {
            "id": 123,
            "name": "test-repo",
            "statistics": {
                "repository_size": 104857600,
                "lfs_objects_size": 52428800,
                "job_artifacts_size": 10485760,
                "pipeline_artifacts_size": 5242880,
            },
        }

        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/123",
            json=detailed_stats,
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        result = client.get_project_with_statistics(123)

        assert result["statistics"]["lfs_objects_size"] == 52428800
        assert result["statistics"]["job_artifacts_size"] == 10485760

        # Should track performance block
        mock_performance_tracker.start_api_block.assert_called_with("Detailed Storage Statistics")

    @responses.activate
    def test_get_project_job_artifacts_list(self, mock_performance_tracker):
        """Test detailed job artifacts analysis."""
        pipelines_response = [
            {"id": 1001, "status": "success"},
            {"id": 1002, "status": "success"},
        ]

        jobs_response = [
            {
                "id": 2001,
                "name": "build",
                "status": "success",
                "created_at": "2025-07-25T10:00:00Z",
                "artifacts_expire_at": "2025-08-25T10:00:00Z",
                "artifacts": {"file": {"filename": "artifacts.zip", "size": 10485760}},
            },
            {
                "id": 2002,
                "name": "test",
                "status": "success",
                "created_at": "2025-07-24T15:00:00Z",
                "artifacts": {"file": {"filename": "test-results.xml", "size": 1048576}},
            },
        ]

        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects/123/pipelines",
            json=pipelines_response,
            status=200,
        )

        for pipeline_id in [1001, 1002]:
            responses.add(
                responses.GET,
                f"https://gitlab.example.com/api/v4/projects/123/pipelines/{pipeline_id}/jobs",
                json=jobs_response,
                status=200,
            )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        artifacts = client.get_project_job_artifacts_list(123)

        assert len(artifacts) == 4  # 2 jobs × 2 pipelines
        assert artifacts[0]["job_name"] == "build"
        assert artifacts[0]["artifact_size"] == 10485760
        assert artifacts[0]["artifact_filename"] == "artifacts.zip"

        # Should track performance block
        mock_performance_tracker.start_api_block.assert_called_with("Job Artifacts Analysis")


class TestPerformanceTracking:
    """Test performance tracking integration."""

    @responses.activate
    def test_successful_api_call_tracking(self, mock_performance_tracker):
        """Test tracking of successful API calls."""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/projects",
            json=[{"id": 1, "name": "test"}],
            status=200,
        )

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        client._make_request("projects")

        mock_performance_tracker.add_api_call.assert_called_with("API Requests", success=True)

    @responses.activate
    def test_failed_api_call_tracking(self, mock_performance_tracker):
        """Test tracking of failed API calls."""
        responses.add(responses.GET, "https://gitlab.example.com/api/v4/projects", status=500)

        client = GitLabClient("https://gitlab.example.com", "token", mock_performance_tracker)
        client._make_request("projects")

        mock_performance_tracker.add_api_call.assert_called_with(
            "API Requests", success=False, error_message=unittest.mock.ANY
        )

    def test_no_performance_tracker(self):
        """Test client operation without performance tracker."""
        client = GitLabClient("https://gitlab.example.com", "token")

        # Should not raise errors when performance_tracker is None
        assert client.performance_tracker is None
