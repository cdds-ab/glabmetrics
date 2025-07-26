"""GitLab API client for data collection."""

import requests
from typing import Dict, List, Optional
from urllib.parse import urljoin
import time
from rich.console import Console
from .performance_tracker import PerformanceTracker

console = Console()


class GitLabClient:
    """Client for interacting with GitLab API."""

    def __init__(
        self,
        gitlab_url: str,
        token: str,
        performance_tracker: Optional[PerformanceTracker] = None,
    ):
        self.gitlab_url = gitlab_url.rstrip("/")
        self.api_url = urljoin(self.gitlab_url, "/api/v4/")
        self.token = token
        self.performance_tracker = performance_tracker
        self.gitlab_version = None
        self.session = requests.Session()
        self.session.headers.update(
            {"Private-Token": token, "Content-Type": "application/json"}
        )

    def test_connection(self) -> bool:
        """Test if connection to GitLab is working and detect version."""
        try:
            response = self.session.get(urljoin(self.api_url, "user"))
            if response.status_code == 200:
                # Get GitLab version from version endpoint
                self._detect_gitlab_version()
                return True
            return False
        except Exception:
            return False

    def _detect_gitlab_version(self) -> None:
        """Detect GitLab version from API."""
        try:
            # Method 1: Try version endpoint
            response = self.session.get(urljoin(self.api_url, "version"))
            if response.status_code == 200:
                version_data = response.json()
                self.gitlab_version = version_data.get("version", "Unknown")
                return
        except Exception:
            pass

        try:
            # Method 2: Try from application statistics (admin only)
            response = self.session.get(urljoin(self.api_url, "application/statistics"))
            if response.status_code == 200:
                # Sometimes version info is in headers
                pass
        except Exception:
            pass

        try:
            # Method 3: Check for version-specific API endpoints
            # GitLab 17.x has different storage APIs
            response = self.session.get(
                urljoin(self.api_url, "admin/usage_trends/measurements")
            )
            if response.status_code in [
                200,
                403,
            ]:  # 403 means endpoint exists but no permission
                self.gitlab_version = "17.x+ (estimated from API availability)"
                return
        except Exception:
            pass

        self.gitlab_version = "Unknown (< 17.0 estimated)"

    def get_gitlab_version(self) -> str:
        """Get detected GitLab version."""
        return self.gitlab_version or "Unknown"

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Make paginated API request."""
        url = urljoin(self.api_url, endpoint)
        all_data = []
        page = 1
        per_page = 100

        if params is None:
            params = {}

        params.update({"per_page": per_page, "page": page})

        while True:
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()

                # Track successful API call
                if self.performance_tracker:
                    self.performance_tracker.add_api_call("API Requests", success=True)

                data = response.json()
                if not data:
                    break

                all_data.extend(data)

                # Check if there are more pages
                if len(data) < per_page:
                    break

                page += 1
                params["page"] = page

                # Reduced rate limiting for faster collection
                time.sleep(0.02)

            except requests.exceptions.RequestException as e:
                # Track failed API call
                if self.performance_tracker:
                    self.performance_tracker.add_api_call(
                        "API Requests", success=False, error_message=str(e)
                    )
                console.print(
                    f"[yellow]Warning: Error fetching {endpoint}: {e}[/yellow]"
                )
                break

        return all_data

    def _make_single_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make single API request."""
        url = urljoin(self.api_url, endpoint)
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def get_projects(self) -> List[Dict]:
        """Get all projects from GitLab."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Project Discovery")

        result = self._make_request(
            "projects",
            {
                "statistics": "true",
                "with_custom_attributes": "true",
                "archived": "false",
            },
        )

        if self.performance_tracker:
            self.performance_tracker.end_api_block("Project Discovery", len(result))

        return result

    def get_project_details(self, project_id: int) -> Optional[Dict]:
        """Get detailed project information."""
        return self._make_single_request(
            f"projects/{project_id}", {"statistics": "true"}
        )

    def get_project_commits(
        self, project_id: int, since: Optional[str] = None
    ) -> List[Dict]:
        """Get commits for a project."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Commit History")

        params = {}
        if since:
            params["since"] = since
        result = self._make_request(f"projects/{project_id}/repository/commits", params)

        if self.performance_tracker:
            self.performance_tracker.end_api_block("Commit History", len(result))

        return result

    def get_project_contributors(self, project_id: int) -> List[Dict]:
        """Get contributors for a project."""
        return self._make_request(f"projects/{project_id}/repository/contributors")

    def get_project_merge_requests(self, project_id: int) -> List[Dict]:
        """Get merge requests for a project."""
        return self._make_request(
            f"projects/{project_id}/merge_requests", {"state": "opened"}
        )

    def get_project_pipelines(self, project_id: int) -> List[Dict]:
        """Get pipelines for a project."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("CI/CD Pipelines")

        result = self._make_request(f"projects/{project_id}/pipelines")

        if self.performance_tracker:
            self.performance_tracker.end_api_block("CI/CD Pipelines", len(result))

        return result

    def get_pipeline_details(self, project_id: int, pipeline_id: int) -> Optional[Dict]:
        """Get detailed pipeline information including jobs."""
        return self._make_single_request(
            f"projects/{project_id}/pipelines/{pipeline_id}"
        )

    def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> List[Dict]:
        """Get jobs for a specific pipeline."""
        return self._make_request(f"projects/{project_id}/pipelines/{pipeline_id}/jobs")

    def get_project_runners(self, project_id: int) -> List[Dict]:
        """Get runners available for a project."""
        return self._make_request(f"projects/{project_id}/runners")

    def get_project_storage(self, project_id: int) -> Optional[Dict]:
        """Get project storage statistics."""
        return self._make_single_request(f"projects/{project_id}/statistics")

    def get_project_with_statistics(self, project_id: int) -> Optional[Dict]:
        """Get project details including comprehensive storage statistics."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Detailed Storage Statistics")

        result = self._make_single_request(
            f"projects/{project_id}", {"statistics": "true"}
        )

        if self.performance_tracker:
            self.performance_tracker.end_api_block(
                "Detailed Storage Statistics", 1 if result else 0
            )

        return result

    def get_project_job_artifacts_list(self, project_id: int) -> List[Dict]:
        """Get list of job artifacts for detailed analysis (GitLab 17.x+)."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Job Artifacts Analysis")

        # Get recent jobs with artifacts
        jobs_with_artifacts = []
        try:
            # Get recent pipelines
            pipelines = self._make_request(
                f"projects/{project_id}/pipelines", {"per_page": 20}
            )

            for pipeline in pipelines[:10]:  # Analyze last 10 pipelines
                pipeline_id = pipeline.get("id")
                if pipeline_id:
                    jobs = self._make_request(
                        f"projects/{project_id}/pipelines/{pipeline_id}/jobs"
                    )
                    for job in jobs:
                        if job.get("artifacts") and job["artifacts"].get("file"):
                            artifact_info = {
                                "job_id": job["id"],
                                "job_name": job["name"],
                                "pipeline_id": pipeline_id,
                                "created_at": job.get("created_at"),
                                "artifacts_expire_at": job.get("artifacts_expire_at"),
                                "artifact_size": job["artifacts"]["file"].get(
                                    "size", 0
                                ),
                                "artifact_filename": job["artifacts"]["file"].get(
                                    "filename", ""
                                ),
                                "status": job.get("status"),
                            }
                            jobs_with_artifacts.append(artifact_info)
        except Exception as e:
            if self.performance_tracker:
                self.performance_tracker.add_api_call(
                    "Job Artifacts Analysis", False, str(e)
                )

        if self.performance_tracker:
            self.performance_tracker.end_api_block(
                "Job Artifacts Analysis", len(jobs_with_artifacts)
            )

        return jobs_with_artifacts

    def get_project_lfs_objects(self, project_id: int) -> List[Dict]:
        """Get LFS objects information (GitLab 17.x+)."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("LFS Objects Analysis")

        lfs_objects = []
        try:
            # Try to get LFS objects via repository files API
            # Note: This is an approximation as direct LFS API might need admin access
            tree = self.get_project_repository_tree(project_id)
            for item in tree:
                if (
                    item.get("name", "").endswith(".lfs")
                    or item.get("size", 0) > 100 * 1024 * 1024
                ):  # >100MB
                    lfs_objects.append(
                        {
                            "path": item.get("path"),
                            "size": item.get("size", 0),
                            "type": (
                                "lfs_pointer"
                                if item.get("name", "").endswith(".lfs")
                                else "large_file"
                            ),
                        }
                    )
        except Exception as e:
            if self.performance_tracker:
                self.performance_tracker.add_api_call(
                    "LFS Objects Analysis", False, str(e)
                )

        if self.performance_tracker:
            self.performance_tracker.end_api_block(
                "LFS Objects Analysis", len(lfs_objects)
            )

        return lfs_objects

    def get_project_packages(self, project_id: int) -> List[Dict]:
        """Get packages for a project."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Package Registry")

        result = self._make_request(f"projects/{project_id}/packages")

        if self.performance_tracker:
            self.performance_tracker.end_api_block("Package Registry", len(result))

        return result

    def get_project_container_registry(self, project_id: int) -> List[Dict]:
        """Get container registry repositories for a project."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Container Registry")

        result = self._make_request(f"projects/{project_id}/registry/repositories")

        if self.performance_tracker:
            self.performance_tracker.end_api_block("Container Registry", len(result))

        return result

    def get_registry_tags(self, project_id: int, repository_id: int) -> List[Dict]:
        """Get tags for a container registry repository."""
        return self._make_request(
            f"projects/{project_id}/registry/repositories/{repository_id}/tags"
        )

    def get_users(self) -> List[Dict]:
        """Get all users."""
        return self._make_request("users")

    def get_user_activities(self, user_id: int) -> List[Dict]:
        """Get user activities."""
        return self._make_request(f"users/{user_id}/events")

    def get_system_statistics(self) -> Optional[Dict]:
        """Get system-wide statistics (admin only)."""
        return self._make_single_request("application/statistics")

    def get_project_repository_tree(
        self, project_id: int, path: str = "", ref: Optional[str] = None
    ) -> List[Dict]:
        """Get repository file tree."""
        if self.performance_tracker:
            self.performance_tracker.start_api_block("Binary File Detection")

        params = {"path": path, "recursive": "true"}

        # Try to get default branch if no ref specified
        if not ref:
            try:
                project_details = self._make_single_request(f"projects/{project_id}")
                if project_details and project_details.get("default_branch"):
                    ref = project_details["default_branch"]
                else:
                    # Fallback: try common branch names
                    for branch_name in ["main", "master", "develop"]:
                        try:
                            test_params = params.copy()
                            test_params["ref"] = branch_name
                            result = self._make_request(
                                f"projects/{project_id}/repository/tree", test_params
                            )
                            if result:
                                ref = branch_name
                                break
                        except Exception:
                            continue
            except Exception:
                ref = "main"  # Final fallback

        if ref:
            params["ref"] = ref

        result = self._make_request(f"projects/{project_id}/repository/tree", params)

        if self.performance_tracker:
            self.performance_tracker.end_api_block("Binary File Detection", len(result))

        return result

    def get_project_languages(self, project_id: int) -> Optional[Dict]:
        """Get programming languages used in project."""
        return self._make_single_request(f"projects/{project_id}/languages")

    def get_project_issues(self, project_id: int) -> List[Dict]:
        """Get issues for a project."""
        return self._make_request(f"projects/{project_id}/issues", {"state": "opened"})
