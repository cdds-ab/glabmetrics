"""Ultra-fast analyzer for GitLab statistics with absolutely minimal API calls."""

from datetime import datetime, timedelta
from typing import Dict, Optional

from dateutil.parser import parse as parse_date

from .analyzer import GitLabAnalyzer, RepositoryStats
from .gitlab_client import GitLabClient


class UltraFastGitLabAnalyzer(GitLabAnalyzer):
    """Ultra-high-speed GitLab analyzer with NO additional API calls beyond project list."""

    def __init__(self, client: Optional[GitLabClient], performance_tracker=None):
        super().__init__(client, performance_tracker)
        self.ultra_fast_mode: bool = True

    def _analyze_project_ultra_fast(self, project: Dict) -> Optional[RepositoryStats]:
        """Ultra-fast project analysis with ZERO additional API calls."""
        try:
            project_id = project["id"]

            # Get basic stats from project data only (no additional API calls!)
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
            six_months_ago = datetime.now() - timedelta(days=180)
            if last_activity.tzinfo is not None and six_months_ago.tzinfo is None:
                six_months_ago = six_months_ago.replace(tzinfo=None)
                last_activity = last_activity.replace(tzinfo=None)
            is_orphaned = last_activity < six_months_ago

            # ZERO ADDITIONAL API CALLS - Use only project data
            commit_count = project.get("commit_count", 0) or 0
            open_mrs = project.get("open_merge_requests_count", 0) or 0
            open_issues = project.get("open_issues_count", 0) or 0

            # Estimate everything else from project metadata
            contributor_count = max(
                1, min(int(size_mb / 5), 20)
            )  # Heuristic: 1 contributor per 5MB, max 20
            pipeline_count = 0  # Skip entirely
            languages = {}  # Skip entirely

            # Estimate storage from repository size (no additional calls)
            if size_mb > 100:  # Large repos likely have LFS/artifacts
                lfs_size_mb = size_mb * 0.2  # Estimate 20% as LFS
                artifacts_size_mb = size_mb * 0.1  # Estimate 10% as artifacts
            else:
                lfs_size_mb = 0
                artifacts_size_mb = 0

            packages_size_mb = 0
            container_registry_size_mb = 0
            storage_stats = project.get("statistics", {})

            # Ultra-simplified metrics
            complexity_score = min(size_mb * 2, 100)  # Simple size-based complexity
            health_score = self._calculate_ultra_simple_health_score(
                project, open_mrs, open_issues, last_activity
            )
            commit_frequency = (
                commit_count / max((datetime.now() - last_activity).days, 1)
                if commit_count > 0
                else 0
            )
            hotness_score = self._calculate_ultra_simple_hotness_score(last_activity)
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
                binary_files=[],  # Skip entirely
                complexity_score=complexity_score,
                health_score=health_score,
                fetch_activity={},
                language_diversity=0,
                commit_frequency=commit_frequency,
                hotness_score=hotness_score,
                maintenance_score=maintenance_score,
                default_branch=project.get("default_branch", ""),
                pipeline_success_rate=0.0,
                avg_pipeline_duration=0.0,
                pipeline_details={},
                job_artifacts_details=[],
                lfs_objects_details=[],
                expired_artifacts_count=0,
                old_artifacts_size_mb=0.0,
                gitlab_version="",  # Skip version check
            )

        except Exception as e:
            print(
                f"Error in ultra-fast analysis of project {project.get('name', 'unknown')}: {e}"
            )
            return None

    def _calculate_ultra_simple_health_score(
        self, project: Dict, open_mrs: int, open_issues: int, last_activity: datetime
    ) -> float:
        """Ultra-simplified health calculation."""
        try:
            score = 100.0

            # Only basic activity penalty
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity > 180:  # 6 months
                score = 20.0
            elif days_since_activity > 90:  # 3 months
                score = 50.0
            elif days_since_activity > 30:  # 1 month
                score = 80.0

            # Simple penalty for too many open items
            if open_issues > 50:
                score -= 20
            if open_mrs > 10:
                score -= 10

            return max(0.0, min(score, 100.0))
        except Exception:
            return 50.0

    def _calculate_ultra_simple_hotness_score(self, last_activity: datetime) -> float:
        """Ultra-simplified hotness calculation."""
        try:
            days_since_activity = (datetime.now() - last_activity).days

            if days_since_activity <= 1:
                return 100.0
            elif days_since_activity <= 7:
                return 80.0
            elif days_since_activity <= 30:
                return 50.0
            elif days_since_activity <= 90:
                return 20.0
            else:
                return 0.0
        except Exception:
            return 10.0
