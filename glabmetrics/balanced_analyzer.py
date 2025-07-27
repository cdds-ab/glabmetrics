"""Balanced analyzer with optimal speed/data trade-off for GitLab statistics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dateutil.parser import parse as parse_date

from .analyzer import GitLabAnalyzer, RepositoryStats
from .gitlab_client import GitLabClient


class BalancedGitLabAnalyzer(GitLabAnalyzer):
    """Balanced GitLab analyzer with 2 API calls per project for speed/data trade-off."""

    def __init__(self, client: Optional[GitLabClient], performance_tracker=None):
        super().__init__(client, performance_tracker)
        self.balanced_mode: bool = True

    def _analyze_project_balanced(self, project: Dict) -> Optional[RepositoryStats]:
        """Balanced analysis with only 2 essential API calls per project."""
        try:
            project_id = project["id"]

            # Get basic stats from project data (already available)
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

            # Check if orphaned
            six_months_ago = datetime.now() - timedelta(days=180)
            if last_activity.tzinfo is not None and six_months_ago.tzinfo is None:
                six_months_ago = six_months_ago.replace(tzinfo=None)
                last_activity = last_activity.replace(tzinfo=None)
            is_orphaned = last_activity < six_months_ago

            # BALANCED MODE: Only 2 strategic API calls
            try:
                # Call 1: Get detailed project statistics (most important data)
                detailed_project = self.client.get_project_with_statistics(project_id)
                storage_stats = (
                    detailed_project.get("statistics", {}) if detailed_project else {}
                )

                # Call 2: Get recent commits (essential for activity analysis)
                commits = self.client.get_project_commits(project_id)[
                    :30
                ]  # Limit to 30 for speed
                commit_count = len(commits)

                # Extract contributor info from commits (no extra API call)
                unique_authors = set()
                if commits:
                    for commit in commits:
                        author_name = commit.get("author_name")
                        author_email = commit.get("author_email")
                        if author_name:
                            unique_authors.add(author_name)
                        elif author_email:
                            unique_authors.add(author_email)
                contributor_count = max(len(unique_authors), 1)

                # Use project-level data for other metrics (already fetched)
                open_mrs = project.get("open_merge_requests_count", 0) or 0
                open_issues = project.get("open_issues_count", 0) or 0

                # Storage calculations from statistics
                lfs_size_mb = (storage_stats.get("lfs_objects_size", 0) or 0) / (
                    1024 * 1024
                )
                artifacts_size_mb = (
                    storage_stats.get("job_artifacts_size", 0) or 0
                ) / (1024 * 1024)

                # Skip expensive operations
                languages = {}  # Skip for speed
                pipeline_count = 0  # Skip pipelines
                packages_size_mb = 0  # Skip packages
                container_registry_size_mb = 0  # Skip container registry

            except Exception:
                # Fallback to project data only
                storage_stats = project.get("statistics", {})
                commits = []
                commit_count = project.get("commit_count", 0) or 0
                contributor_count = 1
                open_mrs = project.get("open_merge_requests_count", 0) or 0
                open_issues = project.get("open_issues_count", 0) or 0
                languages = {}
                lfs_size_mb = 0
                artifacts_size_mb = 0
                packages_size_mb = 0
                container_registry_size_mb = 0

            # Calculate balanced metrics (good approximations)
            complexity_score = self._calculate_balanced_complexity_score(
                project, commit_count, contributor_count
            )
            health_score = self._calculate_balanced_health_score(
                project, open_mrs, open_issues, last_activity
            )
            commit_frequency = (
                commit_count / max((datetime.now() - last_activity).days, 1)
                if commit_count > 0
                else 0
            )
            hotness_score = self._calculate_balanced_hotness_score(
                commits, last_activity
            )
            maintenance_score = health_score

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
                binary_files=[],  # Skip binary scan for speed
                complexity_score=complexity_score,
                health_score=health_score,
                fetch_activity={},
                language_diversity=0,  # Languages skipped
                commit_frequency=commit_frequency,
                hotness_score=hotness_score,
                maintenance_score=maintenance_score,
                default_branch=project.get("default_branch", ""),
                pipeline_success_rate=0.0,  # Pipelines skipped
                avg_pipeline_duration=0.0,
                pipeline_details={},
                job_artifacts_details=[],
                lfs_objects_details=[],
                expired_artifacts_count=0,
                old_artifacts_size_mb=0.0,
                gitlab_version="",  # Skip version check for speed
            )

        except Exception as e:
            print(
                f"Error in balanced analysis of project {project.get('name', 'unknown')}: {e}"
            )
            return None

    def _calculate_balanced_complexity_score(
        self, project: Dict, commit_count: int, contributor_count: int
    ) -> float:
        """Balanced complexity calculation without expensive operations."""
        try:
            score = 0.0

            # Repository size factor (0-40 points)
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )
            score += min(size_mb / 5, 40)

            # Commit activity factor (0-30 points)
            score += min(commit_count / 2, 30)

            # Contributor diversity factor (0-30 points)
            score += min(contributor_count * 3, 30)

            return min(score, 100.0)
        except Exception:
            return 30.0  # Default medium complexity

    def _calculate_balanced_health_score(
        self, project: Dict, open_mrs: int, open_issues: int, last_activity: datetime
    ) -> float:
        """Balanced health calculation."""
        try:
            score = 100.0

            # Activity penalty
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity > 180:  # 6 months
                score -= 40
            elif days_since_activity > 90:  # 3 months
                score -= 25
            elif days_since_activity > 30:  # 1 month
                score -= 10

            # Open items penalty
            if open_issues > 20:
                score -= min((open_issues - 20) * 1.5, 20)
            if open_mrs > 10:
                score -= min((open_mrs - 10) * 2, 15)

            # Bonus for recent activity
            if days_since_activity <= 7:
                score += 5

            return max(0.0, min(score, 100.0))
        except Exception:
            return 50.0

    def _calculate_balanced_hotness_score(
        self, commits: List, last_activity: datetime
    ) -> float:
        """Balanced hotness calculation using commit data."""
        try:
            score = 0.0

            # Recent activity score (0-60 points)
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity <= 1:
                score += 60
            elif days_since_activity <= 7:
                score += 45
            elif days_since_activity <= 30:
                score += 25
            elif days_since_activity <= 90:
                score += 10

            # Recent commits score (0-40 points)
            recent_commits = 0
            cutoff_date = datetime.now() - timedelta(days=30)

            for commit in commits:
                try:
                    commit_date = parse_date(commit.get("created_at", ""))
                    if commit_date.tzinfo is not None:
                        commit_date = commit_date.replace(tzinfo=None)
                    if commit_date > cutoff_date:
                        recent_commits += 1
                except Exception:
                    continue

            score += min(recent_commits * 4, 40)

            return min(score, 100.0)
        except Exception:
            return 20.0
