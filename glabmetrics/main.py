#!/usr/bin/env python3
"""Main CLI entry point for GitLab Statistics Analyzer."""

import multiprocessing
import re
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import click
from rich.console import Console
from rich.progress import Progress

from .analyzer import GitLabAnalyzer
from .data_storage import GitLabDataStorage
from .enhanced_report_generator import EnhancedHTMLReportGenerator
from .gitlab_client import GitLabClient
from .performance_analyzer import PerformanceAnalyzer
from .performance_tracker import PerformanceTracker

console = Console()


class GracefulShutdown:
    """Handles graceful shutdown with Ctrl-C, allowing current operations to complete."""

    def __init__(self):
        self.shutdown_requested = False
        self.lock = threading.Lock()
        self.collected_data = []
        self.enhanced_analysis = {}
        self.storage = None
        self.data_file = None

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        with self.lock:
            if not self.shutdown_requested:
                self.shutdown_requested = True
                console.print(
                    "\n[yellow]⚠️  Shutdown requested (Ctrl-C detected)...[/yellow]"
                )
                console.print(
                    "[cyan]🔄 Completing current operations and saving progress...[/cyan]"
                )
                console.print(
                    "[blue]💡 Data will be saved for incremental restart[/blue]"
                )

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        with self.lock:
            return self.shutdown_requested

    def set_data_context(
        self, storage, data_file, collected_data=None, enhanced_analysis=None
    ):
        """Set the current data context for emergency save."""
        with self.lock:
            self.storage = storage
            self.data_file = data_file
            if collected_data is not None:
                self.collected_data = collected_data
            if enhanced_analysis is not None:
                self.enhanced_analysis = enhanced_analysis

    def emergency_save(self, additional_data=None):
        """Save current progress to enable incremental restart."""
        with self.lock:
            if not self.storage or not self.data_file:
                console.print(
                    "[red]⚠️  Cannot save progress - no storage context available[/red]"
                )
                return False

            try:
                # Merge any additional data
                final_data = list(self.collected_data)
                if additional_data:
                    if isinstance(additional_data, list):
                        final_data.extend(additional_data)
                    else:
                        # If it's a single repository dict
                        final_data.append(additional_data)

                # Prepare emergency save data in the same format as normal saves
                emergency_data = {
                    "repositories": final_data,
                    "enhanced_analysis": self.enhanced_analysis or {},
                    "collection_metadata": {
                        "emergency_save": True,
                        "partial_completion": True,
                        "save_timestamp": datetime.now().isoformat(),
                        "total_collected": len(final_data),
                        "enhanced_kpis_enabled": True,  # Assume enhanced KPIs were intended
                        "incremental_used": False,  # Emergency saves are typically from fresh runs
                    },
                }

                # Save emergency data
                self.storage.save_data(emergency_data, datetime.now(), None)

                console.print(
                    f"[green]✅ Emergency save completed: {len(final_data)} repositories saved[/green]"
                )
                console.print(f"[blue]📁 Saved to: {self.data_file}[/blue]")
                console.print(
                    "[cyan]💡 Use --incremental to continue from this point[/cyan]"
                )
                return True

            except Exception as e:
                console.print(f"[red]❌ Emergency save failed: {e}[/red]")
                return False


# Global shutdown handler
shutdown_handler = GracefulShutdown()


def _generate_name_from_url(gitlab_url: str) -> str:
    """Generate a safe filename from GitLab URL."""
    parsed = urlparse(gitlab_url)
    hostname = parsed.hostname or "gitlab"
    # Replace dots and special chars with dashes
    safe_name = re.sub(r"[^\w\-]", "-", hostname)
    # Remove multiple consecutive dashes
    safe_name = re.sub(r"-+", "-", safe_name)
    # Remove leading/trailing dashes
    return safe_name.strip("-")


@click.group()
def cli():
    """GitLab Statistics Analyzer CLI."""
    pass


@cli.command()
@click.argument("gitlab_url", type=str)
@click.argument("admin_token", type=str)
@click.option(
    "--output",
    "-o",
    help="Output HTML file path (default: auto-generated from GitLab URL)",
)
@click.option(
    "--data-file",
    "-d",
    help="Data file path (default: auto-generated from GitLab URL)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with performance details",
)
@click.option(
    "--refresh-data",
    "-r",
    is_flag=True,
    help="Force complete data refresh (conflicts with --incremental)",
)
@click.option(
    "--incremental",
    "-i",
    is_flag=True,
    help="Force incremental update (conflicts with --refresh-data)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    help=f"Number of parallel workers (default: {multiprocessing.cpu_count()})",
)
@click.option(
    "--basic",
    is_flag=True,
    help="Disable enhanced KPIs (basic analysis only)",
)
@click.option(
    "--skip-binary-scan",
    is_flag=True,
    help="Skip binary file detection for faster analysis",
)
@click.option(
    "--force-enhanced",
    is_flag=True,
    help="Force enhanced KPI analysis refresh (automatically done if missing)",
)
@click.option(
    "--regenerate-report",
    is_flag=True,
    help="Regenerate HTML report from cached data without new API calls",
)
def analyze(
    gitlab_url: str,
    admin_token: str,
    output: Optional[str],
    data_file: Optional[str],
    verbose: bool,
    refresh_data: bool,
    incremental: bool,
    workers: Optional[int],
    basic: bool,
    skip_binary_scan: bool,
    force_enhanced: bool,
    regenerate_report: bool,
):
    """
    GitLab Statistics Analyzer with Enhanced KPI Analysis

    Analyzes a GitLab instance and generates comprehensive HTML reports with
    actionable recommendations and critical issues detection.

    Default behavior: Incremental updates (only changed repositories)
    First run: Use -r/--refresh-data for initial data collection

    GITLAB_URL: The base URL of the GitLab instance (e.g., https://gitlab.example.com)
    ADMIN_TOKEN: Admin access token for the GitLab API
    """
    if verbose:
        console.print(
            "[green]Starting GitLab analysis with Enhanced KPI Analysis...[/green]"
        )

    try:
        # Validate mutually exclusive flags
        if refresh_data and incremental:
            console.print(
                "[red]Error: --refresh-data and --incremental are mutually exclusive[/red]"
            )
            sys.exit(1)

        # Generate auto paths if not provided
        name_base = _generate_name_from_url(gitlab_url)
        generated_dir = Path(".generated")
        generated_dir.mkdir(exist_ok=True)

        if not output:
            output = str(generated_dir / f"{name_base}.html")
        if not data_file:
            data_file = str(generated_dir / f"{name_base}.json")

        # Set workers default to CPU count
        if workers is None:
            workers = multiprocessing.cpu_count()

        # Initialize data storage
        storage = GitLabDataStorage(data_file)

        # Set up graceful shutdown context
        shutdown_handler.set_data_context(storage, data_file)

        # Smart default behavior: incremental if cache exists, guide user if not
        if not refresh_data and not incremental:
            if storage.data_exists():
                # Default: incremental update
                incremental = True
                console.print(
                    f"[cyan]📊 Incremental update mode (cache age: {storage.get_data_age()})[/cyan]"
                )
            else:
                # No cache exists, guide user
                console.print(
                    "[yellow]⚠️  No cached data found. Use --refresh-data for initial data collection.[/yellow]"
                )
                console.print(
                    "[yellow]Example: python -m glabmetrics {} {} --refresh-data[/yellow]".format(
                        gitlab_url, "***"
                    )
                )
                sys.exit(1)

        # Check cache for incremental mode
        if incremental and not storage.data_exists():
            console.print(
                "[yellow]⚠️  Incremental mode requires existing cache. Use --refresh-data for initial collection.[/yellow]"
            )
            sys.exit(1)

        # Show selected paths
        if verbose:
            console.print(f"[blue]📁 Data file: {data_file}[/blue]")
            console.print(f"[blue]📄 Output file: {output}[/blue]")
            console.print(f"[blue]👥 Workers: {workers}[/blue]")

        # Check for regenerate-report mode (fastest option)
        if regenerate_report:
            if not storage.data_exists():
                console.print(
                    "[red]Error: --regenerate-report requires existing cached data. Run without this flag first.[/red]"
                )
                sys.exit(1)

            console.print(
                "[cyan]🎯 Regenerating HTML report from cached data (no API calls)...[/cyan]"
            )
            # Skip to report generation - use cached data only
            analysis_results, timestamp = storage.load_data()
            if not analysis_results:
                console.print("[red]Error: Failed to load cached data[/red]")
                sys.exit(1)

            # Jump directly to report generation
            repositories = analysis_results.get("repositories", [])
            enhanced_analysis = analysis_results.get("enhanced_analysis", {})

            # Generate the report directly
            enhanced_generator = EnhancedHTMLReportGenerator()
            enhanced_generator.generate_enhanced_dashboard(
                repositories=repositories,
                enhanced_analysis=enhanced_analysis,
                performance_stats=analysis_results.get("performance_stats"),
                output_file=output,
                enhanced_kpis_requested=not basic,
            )

            output_path = Path(output)
            console.print(
                f"\n[green]✅ HTML report regenerated: {output_path.absolute()}[/green]"
            )
            console.print(
                f"[cyan]🌐 Open in browser: file://{output_path.absolute()}[/cyan]"
            )
            return

        # Check if we should use cached data or refresh from API
        if not refresh_data and storage.data_exists():
            console.print(
                "[cyan]Using cached data for incremental update. Use --refresh-data to fetch all data fresh.[/cyan]"
            )

            # Load cached data
            cached_data, analysis_timestamp = storage.load_data()

            # Handle both old and new data formats
            if isinstance(cached_data, list):
                # Old format: just repositories
                repositories = cached_data
                enhanced_analysis = None
            elif "repositories" in cached_data:
                # New format: structured data with repositories, enhanced_analysis, metadata
                repositories = cached_data.get("repositories", [])
                enhanced_analysis = cached_data.get("enhanced_analysis")
            else:
                # Very old format: repositories directly in root of JSON
                repositories = cached_data.get("repositories", [])
                enhanced_analysis = None

            # Create analyzer with cached data
            analyzer = GitLabAnalyzer(None)  # No client needed for cached data
            analyzer.repositories = repositories

            # Check if we need to run enhanced KPI analysis on cached data
            if (force_enhanced or not enhanced_analysis) and not basic:
                if force_enhanced:
                    console.print(
                        "[cyan]🎯 Force Enhanced KPI Analysis requested with cached data...[/cyan]"
                    )
                else:
                    console.print(
                        "[cyan]🎯 Enhanced KPI Analysis missing in cache - running now...[/cyan]"
                    )

                # We need a GitLab client for enhanced KPI analysis
                client = GitLabClient(
                    gitlab_url,
                    admin_token,
                    performance_tracker=None,
                    silent_warnings=True,
                )

                # Test connection
                if not client.test_connection():
                    console.print(
                        "[red]Error: Cannot perform enhanced KPI analysis - GitLab connection failed[/red]"
                    )
                    sys.exit(1)

                # Perform enhanced KPI analysis on cached repository data
                enhanced_analysis = _run_enhanced_kpi_analysis(
                    client, repositories, workers, console, verbose
                )

                # Update cached data with enhanced analysis
                console.print(
                    "[cyan]💾 Updating cache with enhanced KPI analysis...[/cyan]"
                )
                updated_cache_data = {
                    "repositories": repositories,
                    "enhanced_analysis": enhanced_analysis,
                    "collection_metadata": {
                        "enhanced_kpis_enabled": True,
                        "force_enhanced_used": force_enhanced,
                        "incremental_used": incremental,
                        "final_repository_count": len(repositories),
                        "collection_timestamp": datetime.now().isoformat(),
                    },
                }
                storage.save_data(updated_cache_data, datetime.now(), None)

            # Set enhanced_analysis for cached data path
            if "enhanced_analysis" not in locals():
                enhanced_analysis = None
        else:
            # Fresh data collection from GitLab API
            console.print("[cyan]🚀 Collecting fresh data from GitLab API...[/cyan]")

            # Initialize performance tracker
            performance_tracker = PerformanceTracker()
            performance_tracker.start_collection()

            # Initialize GitLab client with performance tracking
            client = GitLabClient(
                gitlab_url, admin_token, performance_tracker, silent_warnings=True
            )

            # Enable verbose mode for client if requested
            if verbose:
                client.debug_mode = True

            # Test connection
            if not client.test_connection():
                console.print(
                    "[red]Error: Could not connect to GitLab instance or invalid token[/red]"
                )
                sys.exit(1)

            if verbose:
                console.print("[green]✓ Connection established[/green]")
                console.print(
                    f"[blue]GitLab Version: {client.get_gitlab_version()}[/blue]"
                )

            # Initialize analyzer with performance tracking
            analyzer = GitLabAnalyzer(client, performance_tracker)

            # Configure parallel collection (always enabled)
            analyzer.use_parallel_collection = True
            analyzer.max_workers = workers

            # Configure binary scanning
            if skip_binary_scan:
                analyzer.skip_binary_detection = True
                console.print(
                    "[yellow]⚠️  Binary file detection disabled for faster analysis[/yellow]"
                )

            # Enable verbose mode for analyzer if requested
            if verbose:
                analyzer.debug_mode = True

            # Show collection configuration
            console.print(
                f"[blue]🔧 Using parallel collection with {workers} workers[/blue]"
            )

            if workers > 50:
                console.print(
                    "[yellow]⚠️  High worker count may hit GitLab API rate limits[/yellow]"
                )

            # Run data collection
            console.print("[cyan]🚀 Starting data collection...[/cyan]")

            # Get project count for tracking
            projects = client.get_projects()
            original_count = len(projects)

            # Handle incremental updates
            if incremental:
                console.print(
                    "[cyan]🔄 Incremental mode: Checking for changed repositories...[/cyan]"
                )
                projects = _filter_changed_projects(client, projects, storage, console)
                console.print(
                    f"[green]📈 Incremental scan: {len(projects)} changed repositories "
                    f"(from {original_count} total)[/green]"
                )

            performance_tracker.set_repository_count(len(projects))

            # Run parallel data collection with shutdown detection
            from .parallel_collector import ParallelGitLabCollector

            parallel_collector = ParallelGitLabCollector(
                gitlab_client=client,
                max_workers=workers,
                performance_tracker=performance_tracker,
            )

            if verbose:
                parallel_collector.debug_mode = True

            # Collect repositories in parallel with graceful shutdown support
            collected_repositories = []
            try:
                collected_repositories = (
                    parallel_collector.collect_all_projects_parallel(projects)
                )

                # Check for shutdown during collection
                if shutdown_handler.is_shutdown_requested():
                    console.print(
                        "[yellow]⚠️  Shutdown requested during data collection[/yellow]"
                    )
                    # Update shutdown handler with partial data
                    shutdown_handler.set_data_context(
                        storage, data_file, collected_repositories
                    )
                    shutdown_handler.emergency_save()
                    sys.exit(0)

                analyzer.repositories = collected_repositories

            except KeyboardInterrupt:
                console.print(
                    "[yellow]⚠️  KeyboardInterrupt caught during data collection[/yellow]"
                )
                shutdown_handler.set_data_context(
                    storage, data_file, collected_repositories
                )
                shutdown_handler.emergency_save()
                sys.exit(0)

            # Enhanced KPI Analysis (default, unless --basic is used)
            enhanced_analysis = None
            if not basic:
                console.print(
                    "[cyan]🎯 Running Enhanced KPI Analysis (Parallel)...[/cyan]"
                )

                import concurrent.futures
                import time

                from .enhanced_ci_analyzer import EnhancedCIAnalyzer
                from .enhanced_ci_config_analyzer import EnhancedCIConfigAnalyzer
                from .enhanced_issue_analyzer import EnhancedIssueAnalyzer
                from .enhanced_mr_analyzer import EnhancedMRAnalyzer
                from .enhanced_performance_analyzer import EnhancedPerformanceAnalyzer
                from .enhanced_submodule_analyzer import EnhancedSubmoduleAnalyzer

                enhanced_analysis = {}

                # Initialize all analyzers with parallel processing
                analyzers = {
                    "issue": EnhancedIssueAnalyzer(client, max_workers=workers),
                    "mr": EnhancedMRAnalyzer(client),
                    "ci": EnhancedCIAnalyzer(client),
                    "ci_config": EnhancedCIConfigAnalyzer(client),
                    "submodule": EnhancedSubmoduleAnalyzer(client),
                    "performance": EnhancedPerformanceAnalyzer(
                        client, max_workers=workers
                    ),
                }

                # Run all KPI collections in parallel with shutdown detection
                console.print("[blue]📊 Running P1-P6 analyses in parallel...[/blue]")
                kpi_start_time = time.time()
                individual_times = {}

                try:
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=6
                    ) as executor:
                        # Submit all collection tasks with timing
                        collection_futures = {}
                        task_start_times = {}

                        for task_name, analyzer_obj in [
                            ("issue", analyzers["issue"]),
                            ("mr", analyzers["mr"]),
                            ("ci", analyzers["ci"]),
                            ("ci_config", analyzers["ci_config"]),
                            ("submodule", analyzers["submodule"]),
                            ("performance", analyzers["performance"]),
                        ]:
                            # Check for shutdown before starting each task
                            if shutdown_handler.is_shutdown_requested():
                                console.print(
                                    "[yellow]⚠️  Shutdown requested during KPI analysis setup[/yellow]"
                                )
                                shutdown_handler.set_data_context(
                                    storage, data_file, collected_repositories, {}
                                )
                                shutdown_handler.emergency_save()
                                sys.exit(0)

                            task_start_times[task_name] = time.time()
                        if task_name == "issue":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_issue_kpis, projects
                            )
                        elif task_name == "mr":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_mr_kpis, projects
                            )
                        elif task_name == "ci":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_ci_kpis, projects
                            )
                        elif task_name == "ci_config":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_ci_config_kpis, projects
                            )
                        elif task_name == "submodule":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_submodule_kpis, projects
                            )
                        elif task_name == "performance":
                            collection_futures[task_name] = executor.submit(
                                analyzer_obj.collect_performance_kpis, projects
                            )

                        # Wait for all collections to complete and gather results
                        metrics_results = {}
                        for analysis_type, future in collection_futures.items():
                            try:
                                # Check for shutdown before processing each result
                                if shutdown_handler.is_shutdown_requested():
                                    console.print(
                                        "[yellow]⚠️  Shutdown requested during KPI result processing[/yellow]"
                                    )
                                    # Save partial enhanced analysis
                                    shutdown_handler.set_data_context(
                                        storage,
                                        data_file,
                                        collected_repositories,
                                        metrics_results,
                                    )
                                    shutdown_handler.emergency_save()
                                    sys.exit(0)

                                metrics_results[analysis_type] = future.result()
                                individual_times[analysis_type] = (
                                    time.time() - task_start_times[analysis_type]
                                )
                                console.print(
                                    f"[green]✅ {analysis_type.upper()} metrics collected "
                                    f"({individual_times[analysis_type]:.1f}s)[/green]"
                                )
                            except Exception as e:
                                console.print(
                                    f"[red]❌ {analysis_type.upper()} collection failed: {str(e)}[/red]"
                                )
                                metrics_results[analysis_type] = []
                                individual_times[analysis_type] = (
                                    time.time() - task_start_times[analysis_type]
                                )

                except KeyboardInterrupt:
                    console.print(
                        "[yellow]⚠️  KeyboardInterrupt caught during KPI analysis[/yellow]"
                    )
                    shutdown_handler.set_data_context(
                        storage, data_file, collected_repositories, {}
                    )
                    shutdown_handler.emergency_save()
                    sys.exit(0)

                kpi_total_time = time.time() - kpi_start_time

                # Track Enhanced KPI performance in PerformanceTracker
                performance_tracker.track_enhanced_kpi_analysis(
                    kpi_times=individual_times,
                    total_duration=kpi_total_time,
                    parallel_enabled=True,
                )

                console.print(
                    f"[green]🚀 Parallel collection completed in {kpi_total_time:.1f}s[/green]"
                )

                # Generate analyses sequentially (fast, no API calls)
                console.print("[blue]📋 Generating analysis reports...[/blue]")

                # P1: Issue KPI Analysis
                if "issue" in metrics_results:
                    enhanced_analysis["issue_analysis"] = analyzers[
                        "issue"
                    ].generate_issue_kpi_analysis(metrics_results["issue"])
                    enhanced_analysis["issue_metrics"] = metrics_results["issue"]

                # P2: Merge Request & Code Review Quality
                if "mr" in metrics_results:
                    enhanced_analysis["mr_analysis"] = analyzers[
                        "mr"
                    ].generate_mr_kpi_analysis(metrics_results["mr"])
                    enhanced_analysis["mr_metrics"] = metrics_results["mr"]

                # P3: CI Runner Usage & Jenkins Webhooks
                if "ci" in metrics_results:
                    enhanced_analysis["ci_analysis"] = analyzers[
                        "ci"
                    ].generate_ci_kpi_analysis(metrics_results["ci"])
                    enhanced_analysis["ci_metrics"] = metrics_results["ci"]

                # P4: GitLab-CI Configuration Check
                if "ci_config" in metrics_results:
                    enhanced_analysis["ci_config_analysis"] = analyzers[
                        "ci_config"
                    ].generate_ci_config_analysis(metrics_results["ci_config"])
                    enhanced_analysis["ci_config_metrics"] = metrics_results[
                        "ci_config"
                    ]

                # P5: Submodule Network Graph
                if "submodule" in metrics_results:
                    enhanced_analysis["submodule_analysis"] = analyzers[
                        "submodule"
                    ].generate_submodule_analysis(metrics_results["submodule"])
                    enhanced_analysis["submodule_metrics"] = metrics_results[
                        "submodule"
                    ]

                # P6: Performance Guidelines & Caching
                if "performance" in metrics_results:
                    enhanced_analysis["performance_analysis"] = analyzers[
                        "performance"
                    ].generate_performance_analysis(metrics_results["performance"])
                    enhanced_analysis["performance_metrics"] = metrics_results[
                        "performance"
                    ]

                total_projects = len(projects) if projects else 0
                console.print(
                    f"[green]✅ Enhanced KPI analysis completed for {total_projects} projects[/green]"
                )

            # Save data to cache with performance stats (only when collecting fresh data)
            console.print("[cyan]💾 Saving data to cache...[/cyan]")
            analysis_timestamp = datetime.now()
            perf_stats = performance_tracker.get_performance_stats()

            # Handle incremental data merging
            final_repositories = analyzer.repositories
            if incremental and storage.data_exists():
                console.print(
                    "[cyan]🔄 Merging with cached data for complete dataset...[/cyan]"
                )
                final_repositories = _merge_with_cached_data(
                    analyzer.repositories, storage
                )
                console.print(
                    f"[green]📈 Final dataset: {len(final_repositories)} repositories total[/green]"
                )

            # Prepare data for storage
            cache_data = {
                "repositories": final_repositories,
                "enhanced_analysis": enhanced_analysis,
                "collection_metadata": {
                    "enhanced_kpis_enabled": not basic,
                    "incremental_used": incremental,
                    "original_project_count": original_count,
                    "analyzed_project_count": len(projects),
                    "final_repository_count": len(final_repositories),
                    "workers_used": workers,
                    "collection_timestamp": analysis_timestamp.isoformat(),
                },
            }

            storage.save_data(cache_data, analysis_timestamp, perf_stats)

            # Save separate performance JSON file
            perf_file = data_file.replace(".json", "-perf.json")
            import json
            from dataclasses import asdict

            try:
                with open(perf_file, "w", encoding="utf-8") as f:
                    # Convert dataclass to dict for JSON serialization
                    perf_dict = asdict(perf_stats)
                    json.dump(perf_dict, f, indent=2, ensure_ascii=False)
                if verbose:
                    console.print(
                        f"[blue]📊 Performance stats saved to {perf_file}[/blue]"
                    )
            except Exception as e:
                if verbose:
                    console.print(
                        f"[yellow]⚠️  Could not save performance file: {e}[/yellow]"
                    )

            # Show performance summary
            console.print(f"[green]✅ Data collected and cached in {data_file}[/green]")
            console.print(
                f"[blue]📊 Collection completed in {perf_stats.total_duration:.1f} seconds[/blue]"
            )
            console.print(
                f"[blue]🔗 Total API calls: {perf_stats.total_api_calls} ({perf_stats.total_failed_calls} failed)[/blue]"
            )

            # Show detailed performance stats if verbose
            if verbose:
                console.print(
                    "\n[magenta]📈 Detailed Performance Statistics:[/magenta]"
                )
                performance_tracker.print_live_stats()

            # Always show recommendations if available
            if perf_stats.recommendations:
                console.print("\n[yellow]💡 Performance Recommendations:[/yellow]")
                for rec in perf_stats.recommendations:
                    console.print(f"  • {rec}")

        # Check for shutdown before final analysis
        if shutdown_handler.is_shutdown_requested():
            console.print(
                "[yellow]⚠️  Shutdown requested before final analysis[/yellow]"
            )
            # Update shutdown handler with collected data
            if "final_repositories" in locals():
                shutdown_handler.set_data_context(
                    storage, data_file, final_repositories, enhanced_analysis
                )
            else:
                shutdown_handler.set_data_context(
                    storage, data_file, analyzer.repositories, enhanced_analysis
                )
            shutdown_handler.emergency_save()
            sys.exit(0)

        # Run analysis on the data (fast - no API calls)
        console.print("[cyan]Analyzing data and generating report...[/cyan]")
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing analysis...", total=100)

            progress.update(
                task, advance=25, description="[cyan]Analyzing repositories..."
            )
            analyzer.analyze_repositories()

            # Check for shutdown during analysis
            if shutdown_handler.is_shutdown_requested():
                console.print("[yellow]⚠️  Shutdown requested during analysis[/yellow]")
                if "final_repositories" in locals():
                    shutdown_handler.set_data_context(
                        storage, data_file, final_repositories, enhanced_analysis
                    )
                else:
                    shutdown_handler.set_data_context(
                        storage, data_file, analyzer.repositories, enhanced_analysis
                    )
                shutdown_handler.emergency_save()
                sys.exit(0)

            progress.update(
                task, advance=25, description="[cyan]Checking storage usage..."
            )
            analyzer.analyze_storage()

            progress.update(task, advance=25, description="[cyan]Analyzing activity...")
            analyzer.analyze_activity()

            progress.update(
                task, advance=15, description="[cyan]Analyzing pipelines..."
            )
            analyzer.analyze_pipelines()

            progress.update(task, advance=10, description="[cyan]Generating report...")

        # Generate HTML report with enhanced dashboard
        enhanced_generator = EnhancedHTMLReportGenerator()
        analysis_results = analyzer.get_analysis_results()

        # Generate critical issues and best practices for console output
        console.print(
            "\n[magenta]🔍 Analyzing Critical Issues and Recommendations...[/magenta]"
        )

        # Generate issues and practices using the same logic as the dashboard
        critical_issues = enhanced_generator._analyze_critical_issues(
            analysis_results["repositories"],
            enhanced_analysis or {},  # Use empty dict if no enhanced analysis
        )
        best_practices = enhanced_generator._generate_best_practices(
            analysis_results["repositories"], enhanced_analysis or {}
        )

        # Show top 3 critical issues in console
        if critical_issues:
            console.print("\n[red]🚨 TOP CRITICAL ISSUES FOUND:[/red]")
            for i, issue in enumerate(critical_issues[:3], 1):
                severity_color = {
                    "critical": "red",
                    "high": "yellow",
                    "warning": "blue",
                }.get(issue.severity, "white")
                console.print(
                    f"\n[{severity_color}]{i}. {issue.title}[/{severity_color}]"
                )
                console.print(f"   {issue.description}")
                if issue.affected_repos:
                    console.print(
                        f"   📁 Affected: {', '.join(issue.affected_repos[:2])}"
                    )
                # Show first implementation step
                if hasattr(issue, "recommendation") and issue.recommendation:
                    first_step = issue.recommendation.split("\n")[0].replace("# ", "")
                    console.print(f"   💡 Quick fix: {first_step}")

        # Show top best practices
        if best_practices:
            console.print("\n[green]✨ TOP OPTIMIZATION OPPORTUNITIES:[/green]")
            for i, practice in enumerate(best_practices[:2], 1):
                console.print(f"\n[green]{i}. {practice.title}[/green]")
                console.print(f"   {practice.description}")
                if practice.implementation_steps:
                    first_step = practice.implementation_steps[0].replace("# ", "")
                    console.print(f"   🚀 Action: {first_step}")

        # Show enhanced analysis note
        if enhanced_analysis:
            console.print(
                f"\n[cyan]📋 Enhanced KPI Analysis: {len(critical_issues)} issues and {len(best_practices)} practices in HTML report[/cyan]"
            )
        else:
            console.print(
                "\n[yellow]💡 Basic analysis only (use without --basic for P1-P6 Enhanced KPIs)[/yellow]"
            )
            console.print(
                f"[cyan]📋 Repository analysis with {len(critical_issues)} issues and {len(best_practices)} practices in HTML report[/cyan]"
            )

        # Use enhanced dashboard generation
        enhanced_generator.generate_enhanced_dashboard(
            repositories=analysis_results["repositories"],
            enhanced_analysis=enhanced_analysis,  # Use enhanced analysis from cache if available
            performance_stats=analysis_results.get("performance_stats"),
            output_file=output,
            enhanced_kpis_requested=not basic,  # Enhanced KPIs requested unless --basic flag used
        )

        output_path = Path(output)

        console.print(
            f"[green]✓ Report generated successfully: {output_path.absolute()}[/green]"
        )

        if not refresh_data and storage.data_exists():
            console.print(
                f"[yellow]Data is {storage.get_data_age()}. Use --refresh-data for latest data.[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


def _filter_changed_projects(
    client, projects: List[Dict[str, Any]], storage, console
) -> List[Dict[str, Any]]:
    """Filter projects to only include those that changed since last collection."""
    try:
        # Load cached data
        cached_data, _ = storage.load_data()

        # Handle both old and new data formats
        if isinstance(cached_data, list):
            repositories = cached_data
        elif "repositories" in cached_data:
            repositories = cached_data.get("repositories", [])
        else:
            repositories = []

        cached_repos = {repo["id"]: repo for repo in repositories}

        console.print(
            f"[blue]Comparing {len(projects)} current projects with {len(cached_repos)} cached repositories...[/blue]"
        )

        changed_projects = []
        skipped_count = 0

        for project in projects:
            project_id = project.get("id")
            current_activity = project.get("last_activity_at", "")

            # Check if we have cached data for this project
            if project_id in cached_repos:
                cached_activity = cached_repos[project_id].get("last_activity_at", "")

                # Compare last activity timestamps
                if current_activity == cached_activity:
                    skipped_count += 1
                    continue

            # Project is new or has changed
            changed_projects.append(project)

        console.print(
            f"[green]📊 Change detection: {len(changed_projects)} changed, {skipped_count} unchanged[/green]"
        )
        return changed_projects

    except Exception as e:
        console.print(
            f"[yellow]⚠️  Could not perform incremental filtering: {e}[/yellow]"
        )
        console.print("[yellow]Falling back to full scan...[/yellow]")
        return projects


def _run_enhanced_kpi_analysis(
    client, repositories: List[Dict], workers: int, console, verbose: bool
) -> Dict[str, Any]:
    """Run enhanced KPI analysis on cached repository data."""
    import concurrent.futures
    import time

    from .enhanced_ci_analyzer import EnhancedCIAnalyzer
    from .enhanced_ci_config_analyzer import EnhancedCIConfigAnalyzer
    from .enhanced_issue_analyzer import EnhancedIssueAnalyzer
    from .enhanced_mr_analyzer import EnhancedMRAnalyzer
    from .enhanced_performance_analyzer import EnhancedPerformanceAnalyzer
    from .enhanced_submodule_analyzer import EnhancedSubmoduleAnalyzer

    enhanced_analysis = {}

    # Convert repositories to projects format for enhanced analyzers
    projects = []
    for i, repo in enumerate(repositories):
        # Debug first 3 repos only for verbose output
        if verbose and i < 3:
            console.print(
                f"[yellow]Debug repo {i}: type={type(repo)}, has_id={hasattr(repo, 'id')}[/yellow]"
            )

        # Handle both dict and RepositoryStats objects
        if isinstance(repo, dict) and "id" in repo:
            projects.append(
                {
                    "id": repo["id"],
                    "name": repo.get("name", ""),
                    "path_with_namespace": repo.get("path_with_namespace", ""),
                    "last_activity_at": repo.get("last_activity", ""),
                }
            )
        elif hasattr(repo, "id"):  # RepositoryStats object
            projects.append(
                {
                    "id": repo.id,
                    "name": repo.name,
                    "path_with_namespace": repo.path_with_namespace,
                    "last_activity_at": (
                        repo.last_activity.isoformat() if repo.last_activity else ""
                    ),
                }
            )

    if verbose:
        console.print(
            f"[blue]🔍 Converted {len(repositories)} repositories to {len(projects)} projects for enhanced analysis[/blue]"
        )

    if not projects:
        console.print(
            "[yellow]⚠️  No valid repositories found for enhanced analysis[/yellow]"
        )
        return {}

    # Initialize all analyzers with parallel processing
    analyzers = {
        "issue": EnhancedIssueAnalyzer(client, max_workers=workers),
        "mr": EnhancedMRAnalyzer(client),
        "ci": EnhancedCIAnalyzer(client),
        "ci_config": EnhancedCIConfigAnalyzer(client),
        "submodule": EnhancedSubmoduleAnalyzer(client),
        "performance": EnhancedPerformanceAnalyzer(client, max_workers=workers),
    }

    # Run all KPI collections in parallel
    console.print(
        "[blue]📊 Running P1-P6 analyses in parallel on cached data...[/blue]"
    )
    kpi_start_time = time.time()
    individual_times = {}

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all collection tasks with timing
            collection_futures = {}
            task_start_times = {}

            for task_name, analyzer_obj in [
                ("issue", analyzers["issue"]),
                ("mr", analyzers["mr"]),
                ("ci", analyzers["ci"]),
                ("ci_config", analyzers["ci_config"]),
                ("submodule", analyzers["submodule"]),
                ("performance", analyzers["performance"]),
            ]:
                task_start_times[task_name] = time.time()
                if task_name == "issue":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_issue_kpis, projects
                    )
                elif task_name == "mr":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_mr_kpis, projects
                    )
                elif task_name == "ci":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_ci_kpis, projects
                    )
                elif task_name == "ci_config":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_ci_config_kpis, projects
                    )
                elif task_name == "submodule":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_submodule_kpis, projects
                    )
                elif task_name == "performance":
                    collection_futures[task_name] = executor.submit(
                        analyzer_obj.collect_performance_kpis, projects
                    )

            # Wait for all collections to complete and gather results
            metrics_results = {}
            for analysis_type, future in collection_futures.items():
                try:
                    metrics_results[analysis_type] = future.result()
                    individual_times[analysis_type] = (
                        time.time() - task_start_times[analysis_type]
                    )
                    console.print(
                        f"[green]✅ {analysis_type.upper()} metrics collected "
                        f"({individual_times[analysis_type]:.1f}s)[/green]"
                    )
                except Exception as e:
                    console.print(
                        f"[red]❌ {analysis_type.upper()} collection failed: {str(e)}[/red]"
                    )
                    metrics_results[analysis_type] = []
                    individual_times[analysis_type] = (
                        time.time() - task_start_times[analysis_type]
                    )

    except KeyboardInterrupt:
        console.print(
            "[yellow]⚠️  KeyboardInterrupt caught during enhanced KPI analysis[/yellow]"
        )
        return {}

    kpi_total_time = time.time() - kpi_start_time
    console.print(
        f"[green]🚀 Enhanced KPI collection completed in {kpi_total_time:.1f}s[/green]"
    )

    # Generate analyses sequentially (fast, no API calls)
    console.print("[blue]📋 Generating analysis reports...[/blue]")

    # P1: Issue KPI Analysis
    if "issue" in metrics_results:
        enhanced_analysis["issue_analysis"] = analyzers[
            "issue"
        ].generate_issue_kpi_analysis(metrics_results["issue"])
        enhanced_analysis["issue_metrics"] = metrics_results["issue"]

    # P2: Merge Request & Code Review Quality
    if "mr" in metrics_results:
        enhanced_analysis["mr_analysis"] = analyzers["mr"].generate_mr_kpi_analysis(
            metrics_results["mr"]
        )
        enhanced_analysis["mr_metrics"] = metrics_results["mr"]

    # P3: CI Runner Usage & Jenkins Webhooks
    if "ci" in metrics_results:
        enhanced_analysis["ci_analysis"] = analyzers["ci"].generate_ci_kpi_analysis(
            metrics_results["ci"]
        )
        enhanced_analysis["ci_metrics"] = metrics_results["ci"]

    # P4: GitLab-CI Configuration Check
    if "ci_config" in metrics_results:
        enhanced_analysis["ci_config_analysis"] = analyzers[
            "ci_config"
        ].generate_ci_config_analysis(metrics_results["ci_config"])
        enhanced_analysis["ci_config_metrics"] = metrics_results["ci_config"]

    # P5: Submodule Network Graph
    if "submodule" in metrics_results:
        enhanced_analysis["submodule_analysis"] = analyzers[
            "submodule"
        ].generate_submodule_analysis(metrics_results["submodule"])
        enhanced_analysis["submodule_metrics"] = metrics_results["submodule"]

    # P6: Performance Guidelines & Caching
    if "performance" in metrics_results:
        enhanced_analysis["performance_analysis"] = analyzers[
            "performance"
        ].generate_performance_analysis(metrics_results["performance"])
        enhanced_analysis["performance_metrics"] = metrics_results["performance"]

    console.print(
        f"[green]✅ Enhanced KPI analysis completed for {len(projects)} cached repositories[/green]"
    )

    return enhanced_analysis


def _merge_with_cached_data(new_repositories: List[Dict], storage) -> List[Dict]:
    """Merge new repository data with unchanged cached repositories."""
    try:
        cached_data, _ = storage.load_data()

        # Handle both old and new data formats
        if isinstance(cached_data, list):
            repositories = cached_data
        elif "repositories" in cached_data:
            repositories = cached_data.get("repositories", [])
        else:
            repositories = []

        cached_repos = {repo["id"]: repo for repo in repositories}

        # Create lookup for new data
        new_repo_ids = {repo["id"] for repo in new_repositories}

        # Start with new repositories
        merged_repositories = list(new_repositories)

        # Add unchanged repositories from cache
        for repo_id, cached_repo in cached_repos.items():
            if repo_id not in new_repo_ids:
                merged_repositories.append(cached_repo)

        return merged_repositories

    except Exception:
        # If merge fails, just return new data
        return new_repositories


@cli.command()
@click.option("--data-file", help="JSON data file to analyze")
@click.option("--output", help="Output HTML file", default="performance.html")
def performance(data_file, output):
    """Generate performance optimization dashboard from existing data."""
    if not data_file:
        console.print("[red]Error: --data-file is required[/red]")
        console.print(
            "Usage: python -m glabmetrics.main performance --data-file=data.json"
        )
        return

    try:
        console.print(
            f"[cyan]🚀 Analyzing performance issues from {data_file}...[/cyan]"
        )

        # Load data
        import json

        with open(data_file, "r") as f:
            data = json.load(f)

        repositories = data.get("repositories", [])
        if not repositories:
            console.print("[red]No repositories found in data file[/red]")
            return

        # Create performance analyzer
        analyzer = PerformanceAnalyzer(repositories)
        performance_report = analyzer.generate_performance_report()

        # Generate standalone HTML dashboard
        from .performance_analyzer import create_performance_dashboard_content

        summary = performance_report["summary"]
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(
            performance_report["issues"],
            key=lambda x: (severity_order[x.severity], -x.cost_impact_gb),
        )

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 GitLab Performance Optimization Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .dashboard-container {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; margin: 20px; padding: 30px; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; }}
        .metric-number {{ font-size: 2.5rem; font-weight: 900; }}
        .action-card {{ background: white; border-radius: 15px; padding: 25px; margin-bottom: 25px; border-left: 5px solid #007bff; }}
        .action-card.critical {{ border-left-color: #dc3545; }}
        .action-card.high {{ border-left-color: #fd7e14; }}
        .action-card.medium {{ border-left-color: #ffc107; }}
        .priority-badge {{ padding: 8px 15px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }}
        .priority-critical {{ background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; }}
        .priority-high {{ background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }}
        .priority-medium {{ background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; }}
        .code-block {{ background: #2d3748; color: #e2e8f0; border-radius: 8px; padding: 15px; font-family: monospace; }}
        .expected-result {{ background: linear-gradient(135deg, #11998e, #38ef7d); color: white; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .deadline-badge {{ background: #6f42c1; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="text-center mb-5">
            <h1 class="display-3 fw-bold mb-0" style="background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🚀 GitLab Performance Crisis
            </h1>
            <p class="lead text-muted">Critical Performance Issues Detected - Immediate Action Required</p>
        </div>

        <div class="alert alert-danger mb-4" role="alert">
            <h4 class="alert-heading">⚠️ SYSTEM PERFORMANCE EMERGENCY</h4>
            <p class="mb-0">
                <strong>{summary['total_issues']} performance issues</strong> found with
                <strong>{summary['total_waste_gb']:.1f} GB storage waste</strong> causing severe GitLab slowdowns!
            </p>
        </div>

        <div class="row mb-4">
            <div class="col-lg-3 col-md-6">
                <div class="metric-card" style="background: linear-gradient(135deg, #ff416c, #ff4b2b);">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-fire fa-2x me-3"></i>
                        <div>
                            <div class="metric-number">{summary['critical_issues']}</div>
                            <div>Critical Issues</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle fa-2x me-3"></i>
                        <div>
                            <div class="metric-number">{summary['high_issues']}</div>
                            <div>High Priority</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card" style="background: linear-gradient(135deg, #11998e, #38ef7d);">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-piggy-bank fa-2x me-3"></i>
                        <div>
                            <div class="metric-number">{summary['potential_savings_gb']:.0f} GB</div>
                            <div>Savings Potential</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card" style="background: linear-gradient(135deg, #4facfe, #00f2fe);">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-rocket fa-2x me-3"></i>
                        <div>
                            <div class="metric-number">{summary['optimization_potential_percent']:.0f}%</div>
                            <div>Speed Boost</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h2 class="mb-4">🔧 IMMEDIATE ACTIONS REQUIRED</h2>
        {create_performance_dashboard_content(performance_report)}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """

        with open(output, "w", encoding="utf-8") as f:
            f.write(html)

        # Console summary
        console.print(f"[green]✅ Performance dashboard generated: {output}[/green]")
        console.print(
            f"[red]🚨 {summary['critical_issues']} CRITICAL performance issues found![/red]"
        )
        console.print(
            f"[yellow]⚠️  {summary['total_waste_gb']:.1f} GB storage waste detected[/yellow]"
        )
        console.print(
            f"[blue]💡 {summary['optimization_potential_percent']:.0f}% system optimization possible[/blue]"
        )

        if summary["critical_issues"] > 0:
            console.print("\n[red]TOP CRITICAL ISSUE:[/red]")
            top_issue = sorted_issues[0]
            console.print(f"📛 {top_issue.repository}: {top_issue.impact_description}")
            console.print(f"💾 Potential savings: {top_issue.cost_impact_gb:.1f} GB")
            console.print(f"⏰ Fix urgency: {top_issue.urgency_days} days")

    except Exception as e:
        console.print(f"[red]Error generating performance dashboard: {e}[/red]")


if __name__ == "__main__":
    cli()
