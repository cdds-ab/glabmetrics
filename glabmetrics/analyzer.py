"""Main analyzer for GitLab statistics."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.parser import parse as parse_date

from .gitlab_client import GitLabClient
from .performance_tracker import PerformanceTracker


@dataclass
class RepositoryStats:
    """Statistics for a single repository."""

    id: int
    name: str
    path_with_namespace: str
    size_mb: float
    commit_count: int
    contributor_count: int
    last_activity: datetime
    is_orphaned: bool
    languages: Dict[str, float] = field(default_factory=dict)
    storage_stats: Dict[str, Any] = field(default_factory=dict)
    pipeline_count: int = 0
    open_mrs: int = 0
    open_issues: int = 0
    lfs_size_mb: float = 0
    artifacts_size_mb: float = 0
    packages_size_mb: float = 0
    container_registry_size_mb: float = 0
    binary_files: List[str] = field(default_factory=list)

    # New advanced metrics
    complexity_score: float = 0.0
    health_score: float = 0.0
    fetch_activity: Dict[str, Any] = field(default_factory=dict)
    language_diversity: int = 0
    commit_frequency: float = 0.0  # commits per day
    hotness_score: float = 0.0
    maintenance_score: float = 0.0
    default_branch: str = ""
    pipeline_success_rate: float = 0.0
    avg_pipeline_duration: float = 0.0
    pipeline_details: Dict[str, Any] = field(default_factory=dict)

    # Detailed storage breakdown
    job_artifacts_details: List[Dict] = field(default_factory=list)
    lfs_objects_details: List[Dict] = field(default_factory=list)
    expired_artifacts_count: int = 0
    old_artifacts_size_mb: float = 0.0  # Artifacts older than 30 days
    gitlab_version: str = ""


@dataclass
class SystemStats:
    """System-wide statistics."""

    total_repositories: int
    total_size_gb: float
    total_users: int
    active_users_30d: int
    total_commits: int
    orphaned_repositories: int
    repositories_with_lfs: int
    total_lfs_size_gb: float
    total_artifacts_size_gb: float
    total_packages_size_gb: float
    total_container_registry_size_gb: float
    repositories_by_size: List[RepositoryStats] = field(default_factory=list)
    activity_by_month: Dict[str, int] = field(default_factory=dict)
    most_active_repositories: List[RepositoryStats] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)

    # New advanced analytics
    most_complex_repositories: List[RepositoryStats] = field(default_factory=list)
    healthiest_repositories: List[RepositoryStats] = field(default_factory=list)
    hottest_repositories: List[RepositoryStats] = field(default_factory=list)
    language_distribution: Dict[str, int] = field(default_factory=dict)
    avg_complexity_score: float = 0.0
    avg_health_score: float = 0.0
    fetch_heatmap_data: Dict[str, int] = field(default_factory=dict)
    pipeline_success_rate: float = 0.0
    default_branch_stats: Dict[str, int] = field(default_factory=dict)


class GitLabAnalyzer:
    """Analyzes GitLab instance data."""

    def __init__(
        self,
        client: Optional[GitLabClient],
        performance_tracker: Optional[PerformanceTracker] = None,
    ):
        self.client = client
        self.repositories: List[RepositoryStats] = []
        self.system_stats: Optional[SystemStats] = None
        self.users: List[Dict] = []
        self.performance_tracker = performance_tracker
        self.use_parallel_collection: bool = True  # Default to parallel collection
        self.max_workers: int = 20  # Default worker count

    def collect_project_data(self, use_parallel: Optional[bool] = None) -> None:
        """Collect all project data from GitLab using parallel or sequential method."""
        if not self.client:
            raise ValueError("GitLab client is required for data collection")

        # Override parallel setting if specified
        if use_parallel is not None:
            self.use_parallel_collection = use_parallel

        projects = self.client.get_projects()

        if not projects:
            print("No projects found in GitLab instance")
            return

        if self.use_parallel_collection:
            self._collect_project_data_parallel(projects)
        else:
            self._collect_project_data_sequential(projects)

    def _collect_project_data_sequential(self, projects: List[Dict]) -> None:
        """Original sequential collection method."""
        print(f"📊 Collecting data for {len(projects)} projects sequentially...")

        for i, project in enumerate(projects, 1):
            print(f"Processing {i}/{len(projects)}: {project.get('name', 'Unknown')}")
            repo_stats = self._analyze_project(project)
            if repo_stats:
                self.repositories.append(repo_stats)

    def _collect_project_data_parallel(self, projects: List[Dict]) -> None:
        """New parallel collection method using Producer-Consumer pattern."""
        # Import here to avoid circular imports
        from .parallel_collector import ParallelGitLabCollector

        print(f"🚀 Using parallel collection with {self.max_workers} workers")

        # Create parallel collector (speed modes removed)
        parallel_collector = ParallelGitLabCollector(
            gitlab_client=self.client,
            max_workers=self.max_workers,
            performance_tracker=self.performance_tracker,
        )

        # Set debug mode if needed
        if hasattr(self, "debug_mode"):
            parallel_collector.debug_mode = self.debug_mode

        # Collect all repositories in parallel
        collected_repositories = parallel_collector.collect_all_projects_parallel(
            projects
        )

        # Store results
        self.repositories = collected_repositories

        # Print collection statistics
        stats = parallel_collector.get_collection_statistics()
        if stats["failed_collections"] > 0:
            print(f"⚠️  {stats['failed_collections']} projects failed to collect")

        print(
            f"✅ Successfully collected {len(self.repositories)} repositories in {stats['elapsed_time_seconds']:.1f}s"
        )
        print(f"📈 Performance: {stats['projects_per_second']:.2f} projects/second")

    def _analyze_project(self, project: Dict) -> Optional[RepositoryStats]:
        """Analyze a single project."""
        try:
            project_id = project["id"]

            # Get basic stats
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )

            # Parse last activity with timezone handling
            if project.get("last_activity_at"):
                last_activity = parse_date(project["last_activity_at"])
                # Make timezone-aware datetime for comparison
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=None)
            else:
                last_activity = datetime.min

            # Check if orphaned (no activity in 6 months)
            six_months_ago = datetime.now()
            if last_activity.tzinfo is not None and six_months_ago.tzinfo is None:
                # Make six_months_ago timezone-naive for comparison
                six_months_ago = six_months_ago.replace(tzinfo=None)
                last_activity = last_activity.replace(tzinfo=None)

            six_months_ago = six_months_ago - timedelta(days=180)
            is_orphaned = last_activity < six_months_ago

            # Get commits and contributors
            commits = self.client.get_project_commits(project_id)
            contributors = self.client.get_project_contributors(project_id)

            # Get merge requests and issues
            merge_requests = self.client.get_project_merge_requests(project_id)
            issues = self.client.get_project_issues(project_id)

            # Get pipelines
            pipelines = self.client.get_project_pipelines(project_id)

            # Get languages
            languages = self.client.get_project_languages(project_id) or {}

            # Get comprehensive storage statistics (GitLab 17.x+ approach)
            detailed_project = self.client.get_project_with_statistics(project_id)
            storage_stats = (
                detailed_project.get("statistics", {}) if detailed_project else {}
            )

            # Get packages and container registry
            packages = self.client.get_project_packages(project_id)
            container_repos = self.client.get_project_container_registry(project_id)

            # Get detailed artifacts and LFS information
            job_artifacts_details = self.client.get_project_job_artifacts_list(
                project_id
            )
            lfs_objects_details = self.client.get_project_lfs_objects(project_id)

            # Calculate storage sizes from comprehensive data
            lfs_size_mb = 0.0
            artifacts_size_mb = 0.0
            packages_size_mb = 0.0

            # Method 1: Use GitLab 17.x+ detailed statistics
            if storage_stats:
                lfs_size_mb = (storage_stats.get("lfs_objects_size", 0) or 0) / (
                    1024 * 1024
                )
                artifacts_size_mb = (
                    storage_stats.get("job_artifacts_size", 0) or 0
                ) / (1024 * 1024)
                # Add pipeline artifacts (new in GitLab 17.x)
                pipeline_artifacts_mb = (
                    storage_stats.get("pipeline_artifacts_size", 0) or 0
                ) / (1024 * 1024)
                artifacts_size_mb += pipeline_artifacts_mb

            # Method 2: Estimate from project data if API doesn't provide detailed stats
            # Use repository size and other indicators as fallback
            if lfs_size_mb == 0 and artifacts_size_mb == 0:
                # Estimate based on repository characteristics
                repo_size_mb = (
                    project.get("statistics", {}).get("repository_size", 0) or 0
                ) / (1024 * 1024)

                # Heuristic: If repo is large but has few commits, likely has binary/LFS content
                if len(commits) > 0 and repo_size_mb > 50:
                    size_per_commit = repo_size_mb / len(commits)
                    if (
                        size_per_commit > 1
                    ):  # More than 1MB per commit suggests binary content
                        lfs_size_mb = (
                            repo_size_mb * 0.3
                        )  # Estimate 30% as potential LFS

                # Estimate artifacts based on pipeline activity
                if len(pipelines) > 10:  # Active CI/CD
                    artifacts_size_mb = min(
                        repo_size_mb * 0.2, 100
                    )  # Estimate max 100MB artifacts

            # Analyze job artifacts for cleanup recommendations
            expired_artifacts_count = 0
            old_artifacts_size_mb = 0.0
            current_time = datetime.now()

            for artifact in job_artifacts_details:
                created_at = artifact.get("created_at")
                if created_at:
                    try:
                        created_date = parse_date(created_at)
                        # Make timezone-naive for comparison
                        if created_date.tzinfo is not None:
                            created_date = created_date.replace(tzinfo=None)

                        age_days = (current_time - created_date).days
                        artifact_size_mb = artifact.get("artifact_size", 0) / (
                            1024 * 1024
                        )

                        if age_days > 30:  # Artifacts older than 30 days
                            old_artifacts_size_mb += artifact_size_mb
                            expired_artifacts_count += 1
                    except Exception:
                        pass

            # Calculate package sizes
            packages_size_mb = sum(pkg.get("size", 0) for pkg in packages) / (
                1024 * 1024
            )

            # Calculate container registry size
            container_registry_size_mb = 0
            for repo in container_repos:
                tags = self.client.get_registry_tags(project_id, repo["id"])
                container_registry_size_mb += sum(
                    tag.get("size", 0) for tag in tags
                ) / (1024 * 1024)

            # Detect binary files
            binary_files = self._detect_binary_files(project_id)

            # Calculate advanced metrics
            complexity_score = self._calculate_complexity_score(
                project, languages, commits, contributors
            )
            health_score = self._calculate_health_score(
                project, merge_requests, issues, last_activity
            )
            fetch_activity = storage_stats.get("fetches", {})
            language_diversity = len(languages)
            commit_frequency = self._calculate_commit_frequency(
                commits, project.get("created_at")
            )
            hotness_score = self._calculate_hotness_score(
                fetch_activity, commits, last_activity
            )
            maintenance_score = self._calculate_maintenance_score(
                project, last_activity, merge_requests, issues
            )

            # Get pipeline metrics
            pipeline_success_rate, avg_duration = self._calculate_pipeline_metrics(
                pipelines
            )
            pipeline_details = self._analyze_pipeline_details(project_id, pipelines)

            return RepositoryStats(
                id=project_id,
                name=project["name"],
                path_with_namespace=project["path_with_namespace"],
                size_mb=size_mb,
                commit_count=len(commits),
                contributor_count=len(contributors),
                last_activity=last_activity,
                is_orphaned=is_orphaned,
                languages=languages,
                storage_stats=storage_stats,
                pipeline_count=len(pipelines),
                open_mrs=len(merge_requests),
                open_issues=len(issues),
                lfs_size_mb=lfs_size_mb,
                artifacts_size_mb=artifacts_size_mb,
                packages_size_mb=packages_size_mb,
                container_registry_size_mb=container_registry_size_mb,
                binary_files=binary_files,
                complexity_score=complexity_score,
                health_score=health_score,
                fetch_activity=fetch_activity,
                language_diversity=language_diversity,
                commit_frequency=commit_frequency,
                hotness_score=hotness_score,
                maintenance_score=maintenance_score,
                default_branch=project.get("default_branch", ""),
                pipeline_success_rate=pipeline_success_rate,
                avg_pipeline_duration=avg_duration,
                pipeline_details=pipeline_details,
                job_artifacts_details=job_artifacts_details,
                lfs_objects_details=lfs_objects_details,
                expired_artifacts_count=expired_artifacts_count,
                old_artifacts_size_mb=old_artifacts_size_mb,
                gitlab_version=self.client.get_gitlab_version() if self.client else "",
            )

        except Exception as e:
            print(f"Error analyzing project {project.get('name', 'unknown')}: {e}")
            return None

    def _detect_binary_files(self, project_id: int) -> List[str]:
        """Detect large binary files not in LFS."""
        if not self.client:
            return []  # Cannot detect without client

        binary_extensions = {
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".jar",
            ".war",
            ".ear",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".7z",
            ".rar",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".svg",
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".mp3",
            ".wav",
            ".flac",
            ".ogg",
            ".aac",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
        }

        binary_files = []
        try:
            tree = self.client.get_project_repository_tree(project_id)
            for item in tree:
                if item["type"] == "blob":
                    file_path = item["path"]
                    file_ext = (
                        "." + file_path.split(".")[-1].lower()
                        if "." in file_path
                        else ""
                    )

                    # Check if it's a binary file and relatively large
                    if file_ext in binary_extensions:
                        binary_files.append(file_path)
        except Exception:
            pass

        return binary_files

    def _calculate_complexity_score(
        self, project: Dict, languages: Dict, commits: List, contributors: List
    ) -> float:
        """Calculate repository complexity score (0-100)."""
        try:
            score = 0.0

            # Language diversity (0-25 points)
            lang_count = len(languages)
            score += min(lang_count * 5, 25)

            # Size vs commits ratio (0-25 points)
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )
            commit_count = len(commits)
            if commit_count > 0:
                complexity_ratio = (size_mb / commit_count) * 10
                score += min(complexity_ratio, 25)

            # Contributor diversity (0-25 points)
            contributor_count = len(contributors)
            score += min(contributor_count * 2, 25)

            # File complexity from languages (0-25 points)
            if languages:
                # More balanced language distribution = higher complexity
                values = list(languages.values())
                if len(values) > 1:
                    import statistics

                    std_dev = statistics.stdev(values)
                    balance_score = max(0, 25 - (std_dev / 10))
                    score += balance_score

            return min(score, 100.0)
        except Exception:
            return 0.0

    def _calculate_health_score(
        self, project: Dict, merge_requests: List, issues: List, last_activity: datetime
    ) -> float:
        """Calculate repository health score (0-100)."""
        try:
            score = 100.0

            # Penalize old activity
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity > 30:
                score -= min((days_since_activity - 30) * 0.5, 50)

            # Penalize too many open issues/MRs
            open_issues = len(issues)
            open_mrs = len(merge_requests)

            if open_issues > 10:
                score -= min((open_issues - 10) * 2, 20)
            if open_mrs > 5:
                score -= min((open_mrs - 5) * 3, 15)

            # Bonus for recent activity
            if days_since_activity <= 7:
                score += 10
            elif days_since_activity <= 30:
                score += 5

            return max(0.0, min(score, 100.0))
        except Exception:
            return 50.0

    def _calculate_commit_frequency(
        self, commits: List, created_at: Optional[str]
    ) -> float:
        """Calculate commits per day since creation."""
        try:
            if not commits or not created_at:
                return 0.0

            created = parse_date(created_at)
            days_active = (datetime.now() - created).days
            if days_active <= 0:
                return 0.0

            return len(commits) / days_active
        except Exception:
            return 0.0

    def _calculate_hotness_score(
        self, fetch_activity: Dict, commits: List, last_activity: datetime
    ) -> float:
        """Calculate repository hotness based on recent activity (0-100)."""
        try:
            score = 0.0

            # Fetch activity in last 30 days (0-40 points)
            if fetch_activity and "days" in fetch_activity:
                recent_fetches = sum(
                    day["count"]
                    for day in fetch_activity["days"]
                    if (
                        datetime.now() - datetime.strptime(day["date"], "%Y-%m-%d")
                    ).days
                    <= 30
                )
                score += min(recent_fetches / 10, 40)

            # Recent commits (0-30 points)
            recent_commits = 0
            for commit in commits[:50]:  # Check last 50 commits
                try:
                    commit_date = parse_date(commit.get("created_at", ""))
                    if (datetime.now() - commit_date).days <= 30:
                        recent_commits += 1
                except Exception:
                    continue
            score += min(recent_commits * 2, 30)

            # Last activity recency (0-30 points)
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity <= 1:
                score += 30
            elif days_since_activity <= 7:
                score += 20
            elif days_since_activity <= 30:
                score += 10

            return min(score, 100.0)
        except Exception:
            return 0.0

    def _calculate_maintenance_score(
        self, project: Dict, last_activity: datetime, merge_requests: List, issues: List
    ) -> float:
        """Calculate maintenance quality score (0-100)."""
        try:
            score = 50.0  # Base score

            # Regular activity bonus
            days_since_activity = (datetime.now() - last_activity).days
            if days_since_activity <= 7:
                score += 20
            elif days_since_activity <= 30:
                score += 10
            elif days_since_activity > 180:
                score -= 30

            # Issue management
            open_issues = len(issues)
            if open_issues == 0:
                score += 15
            elif open_issues > 20:
                score -= 15

            # MR management
            open_mrs = len(merge_requests)
            if open_mrs == 0:
                score += 10
            elif open_mrs > 10:
                score -= 10

            # Project has description
            if project.get("description"):
                score += 5

            return max(0.0, min(score, 100.0))
        except Exception:
            return 50.0

    def _calculate_pipeline_metrics(self, pipelines: List) -> tuple[float, float]:
        """Calculate pipeline success rate and average duration."""
        try:
            if not pipelines:
                return 0.0, 0.0

            # Count different statuses
            status_counts = defaultdict(int)
            for pipeline in pipelines:
                status = pipeline.get("status", "unknown")
                status_counts[status] += 1

            # Calculate success rate
            successful = status_counts.get("success", 0)
            success_rate = (successful / len(pipelines)) * 100 if pipelines else 0.0

            # Calculate average duration
            durations = []
            for pipeline in pipelines[:20]:  # Last 20 pipelines
                if pipeline.get("duration"):
                    durations.append(pipeline["duration"])

            avg_duration = sum(durations) / len(durations) if durations else 0.0

            return success_rate, avg_duration
        except Exception:
            return 0.0, 0.0

    def _analyze_pipeline_details(
        self, project_id: int, pipelines: List
    ) -> Dict[str, Any]:
        """Analyze detailed pipeline information."""
        if not self.client or not pipelines:
            return {}

        try:
            pipeline_details = {
                "total_pipelines": len(pipelines),
                "status_distribution": defaultdict(int),
                "runner_usage": defaultdict(int),
                "job_types": defaultdict(int),
                "avg_duration_by_status": {},
                "failure_reasons": defaultdict(int),
            }

            # Get detailed info for recent pipelines (last 10)
            for pipeline in pipelines[:10]:
                pipeline_id = pipeline.get("id")
                if not pipeline_id:
                    continue

                status = pipeline.get("status", "unknown")
                pipeline_details["status_distribution"][status] += 1

                # Get pipeline jobs for more details
                try:
                    jobs = self.client.get_pipeline_jobs(project_id, pipeline_id)
                    for job in jobs:
                        job_name = job.get("name", "unknown")
                        runner_description = job.get("runner", {}).get(
                            "description", "unknown"
                        )

                        pipeline_details["job_types"][job_name] += 1
                        pipeline_details["runner_usage"][runner_description] += 1

                        # Track failure reasons
                        if job.get("status") == "failed":
                            failure_reason = job.get("failure_reason", "unknown")
                            pipeline_details["failure_reasons"][failure_reason] += 1

                except Exception:
                    continue

            return dict(pipeline_details)
        except Exception:
            return {}

    def analyze_repositories(self) -> None:
        """Analyze repository statistics."""
        # Sort repositories by various metrics for analysis
        self.repositories.sort(key=lambda r: r.size_mb, reverse=True)

    def analyze_storage(self) -> None:
        """Analyze storage usage patterns."""
        pass  # Implementation included in project analysis

    def analyze_activity(self) -> None:
        """Analyze activity patterns."""
        # Calculate monthly activity
        activity_by_month = defaultdict(int)

        for repo in self.repositories:
            if repo.last_activity > datetime.min:
                month_key = repo.last_activity.strftime("%Y-%m")
                activity_by_month[month_key] += 1

    def analyze_pipelines(self) -> None:
        """Analyze CI/CD pipeline usage."""
        pass  # Pipeline data already collected in project analysis

    def get_analysis_results(self) -> Dict[str, Any]:
        """Get comprehensive analysis results."""
        if not self.repositories:
            return {}

        # Calculate system-wide statistics
        total_size_gb = sum(r.size_mb for r in self.repositories) / 1024
        total_commits = sum(r.commit_count for r in self.repositories)
        orphaned_count = sum(1 for r in self.repositories if r.is_orphaned)
        lfs_repos = sum(1 for r in self.repositories if r.lfs_size_mb > 0)
        total_lfs_gb = sum(r.lfs_size_mb for r in self.repositories) / 1024
        total_artifacts_gb = sum(r.artifacts_size_mb for r in self.repositories) / 1024
        total_packages_gb = sum(r.packages_size_mb for r in self.repositories) / 1024
        total_container_gb = (
            sum(r.container_registry_size_mb for r in self.repositories) / 1024
        )

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Activity analysis
        activity_by_month = defaultdict(int)
        for repo in self.repositories:
            if repo.last_activity > datetime.min:
                month_key = repo.last_activity.strftime("%Y-%m")
                activity_by_month[month_key] += repo.commit_count

        # Most active repositories
        most_active = sorted(
            self.repositories, key=lambda r: r.commit_count, reverse=True
        )[:10]

        # Largest repositories
        largest_repos = sorted(
            self.repositories, key=lambda r: r.size_mb, reverse=True
        )[:10]

        # New advanced rankings
        most_complex = sorted(
            self.repositories, key=lambda r: r.complexity_score, reverse=True
        )[:10]
        healthiest = sorted(
            self.repositories, key=lambda r: r.health_score, reverse=True
        )[:10]
        hottest = sorted(
            self.repositories, key=lambda r: r.hotness_score, reverse=True
        )[:10]

        # Language distribution
        language_distribution = defaultdict(int)
        for repo in self.repositories:
            for lang in repo.languages.keys():
                language_distribution[lang] += 1

        # Fetch heatmap data
        fetch_heatmap = defaultdict(int)
        for repo in self.repositories:
            if repo.fetch_activity and "days" in repo.fetch_activity:
                for day_data in repo.fetch_activity["days"]:
                    date = day_data["date"]
                    count = day_data["count"]
                    fetch_heatmap[date] += count

        # Average scores
        avg_complexity = (
            sum(r.complexity_score for r in self.repositories) / len(self.repositories)
            if self.repositories
            else 0
        )
        avg_health = (
            sum(r.health_score for r in self.repositories) / len(self.repositories)
            if self.repositories
            else 0
        )

        # Pipeline success rate across all repos
        total_success_rate = sum(
            r.pipeline_success_rate
            for r in self.repositories
            if r.pipeline_success_rate > 0
        )
        repos_with_pipelines = sum(
            1 for r in self.repositories if r.pipeline_success_rate > 0
        )
        avg_pipeline_success = (
            total_success_rate / repos_with_pipelines if repos_with_pipelines > 0 else 0
        )

        # Default branch statistics
        branch_stats = defaultdict(int)
        for repo in self.repositories:
            if repo.default_branch:
                branch_stats[repo.default_branch] += 1

        # Get GitLab version info
        gitlab_version = (
            self.repositories[0].gitlab_version if self.repositories else "Unknown"
        )

        system_stats = SystemStats(
            total_repositories=len(self.repositories),
            total_size_gb=total_size_gb,
            total_users=0,  # Will be updated if user data is collected
            active_users_30d=0,
            total_commits=total_commits,
            orphaned_repositories=orphaned_count,
            repositories_with_lfs=lfs_repos,
            total_lfs_size_gb=total_lfs_gb,
            total_artifacts_size_gb=total_artifacts_gb,
            total_packages_size_gb=total_packages_gb,
            total_container_registry_size_gb=total_container_gb,
            repositories_by_size=largest_repos,
            activity_by_month=dict(activity_by_month),
            most_active_repositories=most_active,
            optimization_recommendations=recommendations,
            most_complex_repositories=most_complex,
            healthiest_repositories=healthiest,
            hottest_repositories=hottest,
            language_distribution=dict(language_distribution),
            avg_complexity_score=avg_complexity,
            avg_health_score=avg_health,
            fetch_heatmap_data=dict(fetch_heatmap),
            pipeline_success_rate=avg_pipeline_success,
            default_branch_stats=dict(branch_stats),
        )

        return {
            "system_stats": system_stats,
            "repositories": self.repositories,
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": gitlab_version,
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Check for orphaned repositories
        orphaned = [r for r in self.repositories if r.is_orphaned]
        if orphaned:
            recommendations.append(
                f"Found {len(orphaned)} repositories with no activity in the last 6 months. "
                "Consider archiving or removing these repositories to free up storage space."
            )

        # Check for large repositories without LFS
        large_without_lfs = [
            r
            for r in self.repositories
            if r.size_mb > 100 and r.lfs_size_mb == 0 and r.binary_files
        ]
        if large_without_lfs:
            recommendations.append(
                f"Found {len(large_without_lfs)} large repositories that contain binary files but don't use Git LFS. "
                "Consider migrating binary files to Git LFS to improve performance."
            )

        # Check for excessive artifacts with specific cleanup recommendations
        high_artifacts = [r for r in self.repositories if r.artifacts_size_mb > 1000]
        if high_artifacts:
            recommendations.append(
                f"Found {len(high_artifacts)} repositories with more than 1GB of CI/CD artifacts. "
                "Consider implementing artifact cleanup policies with 30-day retention."
            )

        # Check for old artifacts across all repositories
        total_old_artifacts_mb = sum(r.old_artifacts_size_mb for r in self.repositories)
        total_expired_artifacts = sum(
            r.expired_artifacts_count for r in self.repositories
        )

        if total_old_artifacts_mb > 500:  # More than 500MB of old artifacts
            recommendations.append(
                f"Found {total_expired_artifacts} artifacts older than 30 days consuming "
                f"{total_old_artifacts_mb:.1f}MB. These can be safely cleaned up to free storage space."
            )

        # GitLab version specific recommendations
        if self.repositories and self.repositories[0].gitlab_version:
            version = self.repositories[0].gitlab_version
            if "17." in version:
                recommendations.append(
                    f"GitLab {version} detected. Consider using the new storage management automation "
                    f"features for automated cleanup policies."
                )

        # Check for old container images
        container_repos = [
            r for r in self.repositories if r.container_registry_size_mb > 500
        ]
        if container_repos:
            recommendations.append(
                f"Found {len(container_repos)} repositories with more than 500MB of container images. "
                "Consider implementing container image cleanup policies to remove old images."
            )

        # Check for repositories with many open MRs
        high_mrs = [r for r in self.repositories if r.open_mrs > 10]
        if high_mrs:
            recommendations.append(
                f"Found {len(high_mrs)} repositories with more than 10 open merge requests. "
                "Consider reviewing and merging or closing stale merge requests."
            )

        return recommendations
