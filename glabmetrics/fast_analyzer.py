"""Fast analyzer for GitLab statistics with minimal API calls."""

from datetime import datetime
from typing import Dict, Optional

from dateutil.parser import parse as parse_date

from .analyzer import GitLabAnalyzer, RepositoryStats
from .gitlab_client import GitLabClient


class FastGitLabAnalyzer(GitLabAnalyzer):
    """High-speed GitLab analyzer with minimal API calls for better performance."""

    def __init__(self, client: Optional[GitLabClient], performance_tracker=None):
        super().__init__(client, performance_tracker)
        self.fast_mode: bool = True
        self.minimal_data_collection: bool = True

    def _analyze_project_fast(self, project: Dict) -> Optional[RepositoryStats]:
        """Fast project analysis with minimal API calls (3-5 calls vs 10+ calls)."""
        try:
            project_id = project["id"]

            # Get basic stats from project data (already fetched)
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )

            # Parse last activity
            if project.get("last_activity_at"):
                last_activity = parse_date(project["last_activity_at"])
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=None)
            else:
                last_activity = datetime.min

            # Check if orphaned (no activity in 6 months)
            from datetime import timedelta

            six_months_ago = datetime.now() - timedelta(days=180)
            if last_activity.tzinfo is not None and six_months_ago.tzinfo is None:
                six_months_ago = six_months_ago.replace(tzinfo=None)
                last_activity = last_activity.replace(tzinfo=None)
            is_orphaned = last_activity < six_months_ago

            # FAST MODE: Balanced speed vs data quality (3-4 API calls)
            if self.fast_mode:
                try:
                    # Call 1: Get repository statistics
                    detailed_project = self.client.get_project_with_statistics(
                        project_id
                    )
                    storage_stats = (
                        detailed_project.get("statistics", {})
                        if detailed_project
                        else {}
                    )

                    # Call 2: Get recent commits (limited to 50 for speed)
                    commits = self.client.get_project_commits(project_id)[:50]
                    commit_count = len(commits)

                    # Call 3: Get basic counts (fast endpoints)
                    try:
                        merge_requests = self.client.get_project_merge_requests(
                            project_id
                        )
                        open_mrs = len(merge_requests)
                    except Exception:
                        open_mrs = project.get("open_merge_requests_count", 0) or 0

                    try:
                        issues = self.client.get_project_issues(project_id)
                        open_issues = len(issues)
                    except Exception:
                        open_issues = project.get("open_issues_count", 0) or 0

                    # Call 4: Get languages (important for analysis)
                    try:
                        languages = self.client.get_project_languages(project_id) or {}
                    except Exception:
                        languages = {}

                    # Estimate contributor count from commits (no extra API call)
                    if commits:
                        unique_emails = set()
                        for commit in commits[:20]:  # Check last 20 commits
                            if commit.get("author_email"):
                                unique_emails.add(commit["author_email"])
                        contributor_count = max(len(unique_emails), 1)
                    else:
                        contributor_count = max(
                            1, int(size_mb / 10)
                        )  # Fallback heuristic

                    # Skip slower endpoints in fast mode
                    pipeline_count = 0  # Skip pipelines for speed
                    packages_size_mb = 0  # Skip packages
                    container_registry_size_mb = 0  # Skip container registry

                    # Storage calculations from statistics
                    lfs_size_mb = (storage_stats.get("lfs_objects_size", 0) or 0) / (
                        1024 * 1024
                    )
                    artifacts_size_mb = (
                        storage_stats.get("job_artifacts_size", 0) or 0
                    ) / (1024 * 1024)

                except Exception:
                    # Fallback to minimal data
                    commits = []
                    commit_count = 0
                    contributor_count = 1
                    open_mrs = 0
                    open_issues = 0
                    pipeline_count = 0
                    languages = {}
                    lfs_size_mb = 0
                    artifacts_size_mb = 0
                    packages_size_mb = 0
                    container_registry_size_mb = 0
                    storage_stats = {}

            else:
                # Original full analysis (slower but complete)
                return super()._analyze_project(project)

            # Calculate simplified metrics
            complexity_score = self._calculate_simple_complexity_score(
                project, languages, commit_count
            )
            health_score = self._calculate_simple_health_score(
                project, open_mrs, open_issues, last_activity
            )
            commit_frequency = (
                commit_count / max((datetime.now() - last_activity).days, 1)
                if commit_count > 0
                else 0
            )
            hotness_score = self._calculate_simple_hotness_score(
                commit_count, last_activity
            )
            maintenance_score = health_score  # Simplified

            return RepositoryStats(
                id=project_id,
                name=project["name"],
                path_with_namespace=project["path_with_namespace"],
                size_mb=size_mb,
                commit_count=commit_count,
                contributor_count=contributor_count,
                last_activity=last_activity,
                is_orphaned=is_orphaned,
                languages=languages,
                storage_stats=storage_stats,
                pipeline_count=pipeline_count,
                open_mrs=open_mrs,
                open_issues=open_issues,
                lfs_size_mb=lfs_size_mb,
                artifacts_size_mb=artifacts_size_mb,
                packages_size_mb=packages_size_mb,
                container_registry_size_mb=container_registry_size_mb,
                binary_files=[],  # Skip binary scan in fast mode
                complexity_score=complexity_score,
                health_score=health_score,
                fetch_activity={},
                language_diversity=len(languages),
                commit_frequency=commit_frequency,
                hotness_score=hotness_score,
                maintenance_score=maintenance_score,
                default_branch=project.get("default_branch", ""),
                pipeline_success_rate=0.0,  # Skip in fast mode
                avg_pipeline_duration=0.0,  # Skip in fast mode
                pipeline_details={},
                job_artifacts_details=[],
                lfs_objects_details=[],
                expired_artifacts_count=0,
                old_artifacts_size_mb=0.0,
                gitlab_version=self.client.get_gitlab_version() if self.client else "",
            )

        except Exception as e:
            print(
                f"Error in fast analysis of project {project.get('name', 'unknown')}: {e}"
            )
            return None

    def _calculate_simple_complexity_score(
        self, project: Dict, languages: Dict, commit_count: int
    ) -> float:
        """Simplified complexity calculation for fast mode."""
        try:
            score = 0.0

            # Size-based complexity (0-50 points)
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )
            score += min(size_mb / 10, 50)

            # Commit-based complexity (0-50 points)
            score += min(commit_count / 2, 50)

            return min(score, 100.0)
        except Exception:
            return 25.0  # Default medium complexity

    def _calculate_simple_health_score(
        self, project: Dict, open_mrs: int, open_issues: int, last_activity: datetime
    ) -> float:
        """Simplified health calculation for fast mode."""
        try:
            score = 100.0

            # Activity penalty
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity > 30:
                score -= min((days_since_activity - 30) * 0.5, 50)

            # Open items penalty
            if open_issues > 10:
                score -= min((open_issues - 10) * 2, 20)
            if open_mrs > 5:
                score -= min((open_mrs - 5) * 3, 15)

            return max(0.0, min(score, 100.0))
        except Exception:
            return 50.0  # Default medium health

    def _calculate_simple_hotness_score(
        self, commit_count: int, last_activity: datetime
    ) -> float:
        """Simplified hotness calculation for fast mode."""
        try:
            score = 0.0

            # Recent activity (0-70 points)
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity <= 1:
                score += 70
            elif days_since_activity <= 7:
                score += 50
            elif days_since_activity <= 30:
                score += 30
            elif days_since_activity <= 90:
                score += 10

            # Commit activity (0-30 points)
            score += min(commit_count * 2, 30)

            return min(score, 100.0)
        except Exception:
            return 25.0  # Default low hotness
