"""Parallel data collection with Producer-Consumer pattern for GitLab statistics."""

import concurrent.futures
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .analyzer import GitLabAnalyzer, RepositoryStats
from .gitlab_client import GitLabClient
from .performance_tracker import PerformanceTracker

# Live, Layout, Panel imports removed as they're not used


console = Console()
logger = logging.getLogger(__name__)


@dataclass
class CollectionProgress:
    """Progress tracking for parallel collection."""

    total_projects: int = 0
    completed_projects: int = 0
    failed_projects: int = 0
    current_phase: str = "Initializing"
    start_time: float = 0.0
    estimated_remaining: float = 0.0
    current_project: str = ""
    api_calls_made: int = 0

    @property
    def completion_percentage(self) -> float:
        if self.total_projects == 0:
            return 0.0
        return (self.completed_projects / self.total_projects) * 100

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time if self.start_time > 0 else 0.0


class ParallelGitLabCollector:
    """High-performance parallel GitLab data collector using Producer-Consumer pattern."""

    def __init__(
        self,
        gitlab_client: GitLabClient,
        max_workers: int = 20,
        performance_tracker: Optional[PerformanceTracker] = None,
    ):
        self.gitlab_client = gitlab_client
        self.max_workers = max_workers
        self.performance_tracker = performance_tracker or PerformanceTracker()
        self.debug_mode = False  # Debug mode for detailed timing

        # Producer-Consumer Queue
        self.results_queue: Queue = Queue()
        self.progress = CollectionProgress()

        # Threading controls
        self.collection_finished = threading.Event()
        self.consumer_thread: Optional[threading.Thread] = None

        # Results storage
        self.collected_repositories: List[RepositoryStats] = []
        self.collection_errors: List[Dict[str, Any]] = []

    def collect_all_projects_parallel(
        self, projects: List[Dict]
    ) -> List[RepositoryStats]:
        """Main entry point for parallel project collection with live progress."""
        if not projects:
            console.print("[yellow]No projects to collect[/yellow]")
            return []

        self.progress.total_projects = len(projects)
        self.progress.start_time = time.time()
        self.progress.current_phase = "Starting collection"

        console.print(
            f"🚀 Starting parallel collection of {len(projects)} projects with {self.max_workers} workers"
        )

        # Initialize global debug analyzer if in debug mode
        if self.debug_mode:
            from .debug_analyzer import DebugGitLabAnalyzer

            self.global_debug_analyzer = DebugGitLabAnalyzer(self.gitlab_client)

        try:
            # Start performance tracking
            self.performance_tracker.start_collection()
            self.performance_tracker.set_repository_count(len(projects))

            # Start consumer thread (sequential JSON writing)
            self.consumer_thread = threading.Thread(
                target=self._consumer_worker, daemon=True
            )
            self.consumer_thread.start()

            # Create live dashboard with real-time updates
            self._collect_with_live_dashboard(projects)

            # Signal consumer to finish
            self.results_queue.put(None)  # Poison pill
            self.collection_finished.set()

            # Wait for consumer to finish processing
            if self.consumer_thread:
                self.consumer_thread.join(timeout=30)

            # Final statistics
            self._print_collection_summary()

            # Print debug summary if in debug mode
            if self.debug_mode and self.global_debug_analyzer:
                self.global_debug_analyzer.print_debug_summary()

            return self.collected_repositories

        except Exception as e:
            console.print(f"[red]Critical error in parallel collection: {e}[/red]")
            raise

    def _collect_with_live_dashboard(self, projects: List[Dict]) -> None:
        """Collect projects with live progress dashboard."""
        # Create progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:

            # Create main progress task
            main_task = progress.add_task(
                "🔄 Collecting GitLab data...", total=len(projects)
            )

            # Use ThreadPoolExecutor with as_completed for better progress tracking
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self.progress.current_phase = "Collecting project data"

                # Submit all projects to workers
                future_to_project = {
                    executor.submit(self._producer_collect_project, project): project
                    for project in projects
                }

                # Process completed futures as they finish
                completed = 0
                errors = 0
                current_project_names = []

                try:
                    for future in as_completed(
                        future_to_project, timeout=1800
                    ):  # 30 minute total timeout
                        try:
                            # Get the result (will raise exception if future failed)
                            result = future.result()
                            project = future_to_project[future]
                            project_name = project.get("name", "Unknown")

                            if result:
                                completed += 1
                                self.progress.completed_projects = completed

                                # Update current project being processed (for display)
                                current_project_names.append(project_name)
                                if len(current_project_names) > 3:  # Keep only last 3
                                    current_project_names.pop(0)

                                # Update progress with current project info
                                recent = ", ".join(current_project_names[-2:])
                                desc = (
                                    f"🔄 Collecting: {project_name} | Recent: {recent}"[
                                        :100
                                    ]
                                )
                                progress.update(main_task, advance=1, description=desc)

                            else:
                                errors += 1
                                self.progress.failed_projects += 1

                        except Exception as e:
                            errors += 1
                            self.progress.failed_projects += 1
                            project = future_to_project[future]
                            project_name = project.get("name", "unknown")

                            error_info = {
                                "project_id": project.get("id", "unknown"),
                                "project_name": project_name,
                                "error": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                            self.collection_errors.append(error_info)

                            # Update progress to show error
                            progress.update(
                                main_task,
                                advance=1,
                                description=f"⚠️  Error in {project_name} | {completed} completed, {errors} errors",
                            )

                except concurrent.futures.TimeoutError:
                    # Handle unfinished futures gracefully
                    unfinished_count = 0
                    unfinished_projects = []

                    for future, project in future_to_project.items():
                        if not future.done():
                            unfinished_count += 1
                            unfinished_projects.append(project.get("name", "Unknown"))
                            future.cancel()  # Try to cancel the future

                    logger.warning(
                        f"Timeout reached with {unfinished_count} unfinished projects: "
                        f"{', '.join(unfinished_projects[:5])}"
                    )

                    # Update progress to show timeout
                    progress.update(
                        main_task,
                        description=f"⏰ Timeout: {completed} completed, {unfinished_count} timed out",
                    )

                # Final progress update
                elapsed = time.time() - self.progress.start_time
                rate = completed / elapsed if elapsed > 0 else 0
                progress.update(
                    main_task,
                    description=f"✅ Completed! {completed} repositories ({rate:.1f}/sec)",
                )

    def _producer_collect_project(self, project: Dict) -> Optional[RepositoryStats]:
        """Producer: Collect data for a single project (runs in thread pool)."""
        project_id = project.get("id")
        project_name = project.get("name", f"Project-{project_id}")

        try:
            self.progress.current_project = project_name

            # Use appropriate analyzer based on debug mode
            if self.debug_mode and self.global_debug_analyzer:
                # Use shared debug analyzer to aggregate timing data
                analyzer = self.global_debug_analyzer
                repo_stats = analyzer._analyze_project_debug(project)
            else:
                # Use standard analyzer for complete data collection
                analyzer = GitLabAnalyzer(self.gitlab_client)
                repo_stats = analyzer._analyze_project(project)

            if repo_stats:
                # Put result in queue for sequential processing
                self.results_queue.put(("success", repo_stats))
                self.progress.api_calls_made += 1
                return repo_stats
            else:
                self.results_queue.put(
                    (
                        "error",
                        {
                            "project_id": project_id,
                            "error": "Failed to analyze project",
                            "project_name": project_name,
                        },
                    )
                )

        except Exception as e:
            # Handle individual project errors gracefully
            error_data = {
                "project_id": project_id,
                "project_name": project_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.results_queue.put(("error", error_data))

            if self.performance_tracker:
                self.performance_tracker.add_api_call(
                    "Project Collection", success=False, error_message=str(e)
                )

        return None

    def _consumer_worker(self):
        """Consumer: Sequential processing of collected data."""
        while not self.collection_finished.is_set() or not self.results_queue.empty():
            try:
                # Get result from queue with timeout
                result = self.results_queue.get(timeout=1.0)

                if result is None:  # Poison pill
                    break

                result_type, data = result

                if result_type == "success":
                    self.collected_repositories.append(data)
                elif result_type == "error":
                    self.collection_errors.append(data)

                self.results_queue.task_done()

            except Empty:
                # Timeout - continue checking
                continue
            except Exception as e:
                console.print(f"[red]Consumer error: {e}[/red]")
                break

    def _print_collection_summary(self):
        """Print detailed collection summary."""
        elapsed = self.progress.elapsed_time
        successful = len(self.collected_repositories)
        failed = len(self.collection_errors)
        total = self.progress.total_projects

        # Create summary table with better formatting
        table = Table(
            title="🎯 GitLab Collection Summary",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="green", width=20)
        table.add_column("Details", style="dim", width=40)

        # Success metrics
        success_rate = (successful / total * 100) if total > 0 else 0
        table.add_row("Total Projects", str(total), "100% of GitLab instance")
        table.add_row(
            "✅ Successfully Collected",
            str(successful),
            f"{success_rate:.1f}% success rate",
        )

        if failed > 0:
            table.add_row(
                "❌ Failed Projects",
                str(failed),
                f"{failed/total*100:.1f}% failure rate",
            )

        # Performance metrics
        table.add_row("⏱️  Total Duration", f"{elapsed:.1f}s", "Wall clock time")

        if elapsed > 0:
            rate = successful / elapsed
            table.add_row(
                "🚀 Collection Speed",
                f"{rate:.2f}/sec",
                f"~{rate*60:.0f} projects/minute",
            )

            # Estimated time for different instance sizes
            if rate > 0:
                est_1000 = 1000 / rate / 60  # minutes for 1000 projects
                table.add_row(
                    "📊 Scaling Estimate",
                    f"{est_1000:.1f}min",
                    "for 1000 projects at this rate",
                )

        table.add_row(
            "👥 Workers Used", str(self.max_workers), "Parallel processing threads"
        )

        console.print(table)

        # Show error details if any
        if self.collection_errors:
            console.print(
                f"\n[yellow]⚠️  Collection Issues ({len(self.collection_errors)} total):[/yellow]"
            )

            # Group errors by type for better overview
            error_types = {}
            for error in self.collection_errors:
                error_msg = error.get("error", "Unknown error")
                if "404" in error_msg:
                    error_types["404 Not Found"] = (
                        error_types.get("404 Not Found", 0) + 1
                    )
                elif "403" in error_msg:
                    error_types["403 Forbidden"] = (
                        error_types.get("403 Forbidden", 0) + 1
                    )
                elif "timeout" in error_msg.lower():
                    error_types["Timeout"] = error_types.get("Timeout", 0) + 1
                else:
                    error_types["Other"] = error_types.get("Other", 0) + 1

            # Show error summary
            for error_type, count in error_types.items():
                console.print(f"  • {error_type}: {count} projects")

            # Show specific examples (first 3)
            if len(self.collection_errors) <= 3:
                console.print("\n[dim]Specific errors:[/dim]")
                for error in self.collection_errors:
                    project_name = error.get("project_name", "Unknown")[:30]
                    error_msg = error.get("error", "Unknown error")[:50]
                    console.print(f"  • {project_name}: {error_msg}")

        # Performance analysis and recommendations
        if elapsed > 0:
            projects_per_second = successful / elapsed
            console.print("\n[bold]📈 Performance Analysis:[/bold]")

            if projects_per_second < 0.5:
                console.print("[red]🐌 Slow performance detected[/red]")
                console.print(
                    "  💡 Try: Reduce --workers, check network latency, or use --skip-binary-scan"
                )
            elif projects_per_second < 2.0:
                console.print("[yellow]⚖️  Moderate performance[/yellow]")
                console.print(
                    "  💡 Consider: Increase --workers if network allows, or run closer to GitLab server"
                )
            else:
                console.print("[green]🚀 Excellent performance![/green]")
                console.print(
                    "  ✨ Your GitLab instance and network connection are responding well"
                )

        # Show API warnings summary
        if hasattr(self.gitlab_client, "get_warning_summary"):
            try:
                warning_summary = self.gitlab_client.get_warning_summary()
                if warning_summary and isinstance(warning_summary, dict):
                    console.print("\n[bold]⚠️  API Warnings Summary:[/bold]")
                    for warning_type, count in warning_summary.items():
                        console.print(
                            f"  • {warning_type}: [yellow]{count}[/yellow] API calls"
                        )
            except (TypeError, AttributeError):
                # Skip warnings summary if mock object or invalid format
                pass

        # Show total repositories and estimated storage
        if successful > 0:
            console.print(
                f"\n[dim]Ready to analyze {successful} repositories and generate HTML report...[/dim]"
            )

    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get detailed collection statistics."""
        return {
            "total_projects": self.progress.total_projects,
            "successful_collections": len(self.collected_repositories),
            "failed_collections": len(self.collection_errors),
            "elapsed_time_seconds": self.progress.elapsed_time,
            "projects_per_second": (
                len(self.collected_repositories) / self.progress.elapsed_time
                if self.progress.elapsed_time > 0
                else 0
            ),
            "workers_used": self.max_workers,
            "errors": self.collection_errors,
            "performance_stats": (
                self.performance_tracker.get_performance_stats()
                if self.performance_tracker
                else None
            ),
        }
