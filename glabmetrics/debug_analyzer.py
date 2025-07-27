"""Debug analyzer with detailed timing for each operation."""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dateutil.parser import parse as parse_date
from rich.console import Console
from rich.table import Table

from .analyzer import GitLabAnalyzer, RepositoryStats
from .gitlab_client import GitLabClient

console = Console()


class DebugGitLabAnalyzer(GitLabAnalyzer):
    """Debug analyzer with detailed timing for performance analysis."""

    def __init__(self, client: Optional[GitLabClient], performance_tracker=None):
        super().__init__(client, performance_tracker)
        self.debug_mode: bool = True
        self.timing_data: Dict[str, List[float]] = defaultdict(list)
        self.operation_counts: Dict[str, int] = defaultdict(int)

    def _analyze_project_debug(self, project: Dict) -> Optional[RepositoryStats]:
        """Debug project analysis with detailed timing for each operation."""
        project_id = project["id"]
        project_name = project.get("name", f"Project-{project_id}")

        console.print(f"[cyan]🔍 Debug analyzing: {project_name}[/cyan]")

        overall_start = time.time()
        timings = {}

        try:
            # Basic setup (no API calls)
            start_time = time.time()
            size_mb = (project.get("statistics", {}).get("repository_size", 0) or 0) / (
                1024 * 1024
            )

            if project.get("last_activity_at"):
                last_activity = parse_date(project["last_activity_at"])
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=None)
            else:
                last_activity = datetime.min

            six_months_ago = datetime.now() - timedelta(days=180)
            if last_activity.tzinfo is not None and six_months_ago.tzinfo is None:
                six_months_ago = six_months_ago.replace(tzinfo=None)
                last_activity = last_activity.replace(tzinfo=None)
            is_orphaned = last_activity < six_months_ago

            timings["setup"] = time.time() - start_time

            # API Call 1: Get project with statistics
            start_time = time.time()
            try:
                detailed_project = self.client.get_project_with_statistics(project_id)
                storage_stats = (
                    detailed_project.get("statistics", {}) if detailed_project else {}
                )
                timings["project_statistics"] = time.time() - start_time
                self.operation_counts["project_statistics"] += 1
            except Exception as e:
                timings["project_statistics"] = time.time() - start_time
                storage_stats = {}
                console.print(f"  [red]⚠️  Failed to get project statistics: {e}[/red]")

            # API Call 2: Get commits
            start_time = time.time()
            try:
                commits = self.client.get_project_commits(project_id)
                timings["commits"] = time.time() - start_time
                self.operation_counts["commits"] += 1
            except Exception as e:
                timings["commits"] = time.time() - start_time
                commits = []
                console.print(f"  [red]⚠️  Failed to get commits: {e}[/red]")

            # API Call 3: Get contributors
            start_time = time.time()
            try:
                contributors = self.client.get_project_contributors(project_id)
                timings["contributors"] = time.time() - start_time
                self.operation_counts["contributors"] += 1
            except Exception as e:
                timings["contributors"] = time.time() - start_time
                contributors = []
                console.print(f"  [red]⚠️  Failed to get contributors: {e}[/red]")

            # API Call 4: Get merge requests
            start_time = time.time()
            try:
                merge_requests = self.client.get_project_merge_requests(project_id)
                timings["merge_requests"] = time.time() - start_time
                self.operation_counts["merge_requests"] += 1
            except Exception as e:
                timings["merge_requests"] = time.time() - start_time
                merge_requests = []
                console.print(f"  [red]⚠️  Failed to get merge requests: {e}[/red]")

            # API Call 5: Get issues
            start_time = time.time()
            try:
                issues = self.client.get_project_issues(project_id)
                timings["issues"] = time.time() - start_time
                self.operation_counts["issues"] += 1
            except Exception as e:
                timings["issues"] = time.time() - start_time
                issues = []
                console.print(f"  [red]⚠️  Failed to get issues: {e}[/red]")

            # API Call 6: Get pipelines
            start_time = time.time()
            try:
                pipelines = self.client.get_project_pipelines(project_id)
                timings["pipelines"] = time.time() - start_time
                self.operation_counts["pipelines"] += 1
            except Exception as e:
                timings["pipelines"] = time.time() - start_time
                pipelines = []
                console.print(f"  [red]⚠️  Failed to get pipelines: {e}[/red]")

            # API Call 7: Get languages
            start_time = time.time()
            try:
                languages = self.client.get_project_languages(project_id) or {}
                timings["languages"] = time.time() - start_time
                self.operation_counts["languages"] += 1
            except Exception as e:
                timings["languages"] = time.time() - start_time
                languages = {}
                console.print(f"  [red]⚠️  Failed to get languages: {e}[/red]")

            # API Call 8: Get packages (often slow)
            start_time = time.time()
            try:
                packages = self.client.get_project_packages(project_id)
                timings["packages"] = time.time() - start_time
                self.operation_counts["packages"] += 1
            except Exception as e:
                timings["packages"] = time.time() - start_time
                packages = []
                console.print(f"  [red]⚠️  Failed to get packages: {e}[/red]")

            # API Call 9: Get container registry (often slow)
            start_time = time.time()
            try:
                container_repos = self.client.get_project_container_registry(project_id)
                timings["container_registry"] = time.time() - start_time
                self.operation_counts["container_registry"] += 1
            except Exception as e:
                timings["container_registry"] = time.time() - start_time
                container_repos = []
                console.print(f"  [red]⚠️  Failed to get container registry: {e}[/red]")

            # Binary file detection (potentially very slow)
            start_time = time.time()
            try:
                binary_files = self._detect_binary_files(project_id)
                timings["binary_files"] = time.time() - start_time
                self.operation_counts["binary_files"] += 1
            except Exception as e:
                timings["binary_files"] = time.time() - start_time
                binary_files = []
                console.print(f"  [red]⚠️  Failed to detect binary files: {e}[/red]")

            # Calculate metrics (CPU intensive)
            start_time = time.time()
            try:
                # Storage calculations
                lfs_size_mb = (storage_stats.get("lfs_objects_size", 0) or 0) / (
                    1024 * 1024
                )
                artifacts_size_mb = (
                    storage_stats.get("job_artifacts_size", 0) or 0
                ) / (1024 * 1024)
                packages_size_mb = sum(pkg.get("size", 0) for pkg in packages) / (
                    1024 * 1024
                )

                container_registry_size_mb = 0
                for repo in container_repos:
                    try:
                        tags = self.client.get_registry_tags(project_id, repo["id"])
                        container_registry_size_mb += sum(
                            tag.get("size", 0) for tag in tags
                        ) / (1024 * 1024)
                    except Exception:
                        pass

                # Advanced metrics
                complexity_score = self._calculate_complexity_score(
                    project, languages, commits, contributors
                )
                health_score = self._calculate_health_score(
                    project, merge_requests, issues, last_activity
                )
                commit_frequency = self._calculate_commit_frequency(
                    commits, project.get("created_at")
                )
                hotness_score = self._calculate_hotness_score(
                    {}, commits, last_activity
                )
                maintenance_score = self._calculate_maintenance_score(
                    project, last_activity, merge_requests, issues
                )
                pipeline_success_rate, avg_duration = self._calculate_pipeline_metrics(
                    pipelines
                )

                timings["calculations"] = time.time() - start_time
            except Exception as e:
                timings["calculations"] = time.time() - start_time
                console.print(f"  [red]⚠️  Failed in calculations: {e}[/red]")
                # Set defaults
                lfs_size_mb = artifacts_size_mb = packages_size_mb = (
                    container_registry_size_mb
                ) = 0
                complexity_score = health_score = commit_frequency = hotness_score = (
                    maintenance_score
                ) = 0
                pipeline_success_rate = avg_duration = 0

            # Store timing data
            for operation, duration in timings.items():
                self.timing_data[operation].append(duration)

            total_time = time.time() - overall_start
            self.timing_data["total_per_project"].append(total_time)

            # Print debug timing for this project
            self._print_project_debug_timing(project_name, timings, total_time)

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
                fetch_activity={},
                language_diversity=len(languages),
                commit_frequency=commit_frequency,
                hotness_score=hotness_score,
                maintenance_score=maintenance_score,
                default_branch=project.get("default_branch", ""),
                pipeline_success_rate=pipeline_success_rate,
                avg_pipeline_duration=avg_duration,
                pipeline_details={},
                job_artifacts_details=[],
                lfs_objects_details=[],
                expired_artifacts_count=0,
                old_artifacts_size_mb=0.0,
                gitlab_version=self.client.get_gitlab_version() if self.client else "",
            )

        except Exception as e:
            total_time = time.time() - overall_start
            console.print(f"[red]❌ Error analyzing project {project_name}: {e}[/red]")
            console.print(f"[dim]   Total time before error: {total_time:.3f}s[/dim]")
            return None

    def _print_project_debug_timing(
        self, project_name: str, timings: Dict[str, float], total_time: float
    ):
        """Print detailed timing for a single project."""
        console.print(f"[dim]  📊 Timing for {project_name}:[/dim]")

        # Sort timings by duration (slowest first)
        sorted_timings = sorted(timings.items(), key=lambda x: x[1], reverse=True)

        for operation, duration in sorted_timings:
            if duration > 0.1:  # Only show operations taking more than 100ms
                percentage = (duration / total_time) * 100 if total_time > 0 else 0
                console.print(
                    f"[dim]    • {operation}: {duration:.3f}s ({percentage:.1f}%)[/dim]"
                )

        console.print(f"[dim]    💫 Total: {total_time:.3f}s[/dim]")

    def print_debug_summary(self):
        """Print comprehensive debug timing summary."""
        if not self.timing_data:
            console.print("[yellow]No timing data collected[/yellow]")
            return

        console.print("\n[bold cyan]🐛 DEBUG TIMING SUMMARY[/bold cyan]")

        # Create summary table
        table = Table(
            title="Operation Performance Analysis",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Operation", style="cyan", width=20)
        table.add_column("Count", style="green", width=8)
        table.add_column("Avg Time", style="yellow", width=10)
        table.add_column("Total Time", style="red", width=10)
        table.add_column("% of Total", style="blue", width=10)
        table.add_column("Max Time", style="bright_yellow", width=10)

        total_project_time = sum(self.timing_data.get("total_per_project", [0]))

        for operation, times in sorted(
            self.timing_data.items(), key=lambda x: sum(x[1]), reverse=True
        ):
            if operation == "total_per_project":
                continue

            count = len(times)
            avg_time = sum(times) / count if count > 0 else 0
            total_time = sum(times)
            max_time = max(times) if times else 0
            percentage = (
                (total_time / total_project_time) * 100 if total_project_time > 0 else 0
            )

            table.add_row(
                operation,
                str(count),
                f"{avg_time:.3f}s",
                f"{total_time:.3f}s",
                f"{percentage:.1f}%",
                f"{max_time:.3f}s",
            )

        console.print(table)

        # Performance recommendations
        console.print("\n[bold yellow]💡 PERFORMANCE RECOMMENDATIONS:[/bold yellow]")

        # Find slowest operations
        operation_totals = {
            op: sum(times)
            for op, times in self.timing_data.items()
            if op != "total_per_project"
        }
        slowest_ops = sorted(
            operation_totals.items(), key=lambda x: x[1], reverse=True
        )[:3]

        for i, (operation, total_time) in enumerate(slowest_ops, 1):
            percentage = (
                (total_time / total_project_time) * 100 if total_project_time > 0 else 0
            )
            console.print(
                f"  {i}. [red]{operation}[/red]: {total_time:.1f}s ({percentage:.1f}% of total time)"
            )

            # Specific recommendations
            if operation == "binary_files" and total_time > 5:
                console.print(
                    f"     💡 Consider using --skip-binary-scan to save {total_time:.1f}s"
                )
            elif operation == "packages" and total_time > 3:
                console.print(
                    "     💡 Package scanning is slow - consider skipping in fast modes"
                )
            elif operation == "container_registry" and total_time > 3:
                console.print(
                    "     💡 Container registry scanning is slow - consider skipping in fast modes"
                )

        # Overall stats
        avg_per_project = (
            total_project_time / len(self.timing_data["total_per_project"])
            if self.timing_data.get("total_per_project")
            else 0
        )
        console.print("\n[bold green]📊 OVERALL STATS:[/bold green]")
        console.print(f"  • Average time per project: {avg_per_project:.3f}s")
        console.print(f"  • Total analysis time: {total_project_time:.1f}s")
        console.print(
            f"  • Estimated time for 345 projects: {avg_per_project * 345:.1f}s ({avg_per_project * 345 / 60:.1f} minutes)"
        )
