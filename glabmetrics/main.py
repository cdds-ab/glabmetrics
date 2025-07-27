#!/usr/bin/env python3
"""Main CLI entry point for GitLab Statistics Analyzer."""

import multiprocessing
import re
import sys
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
from .performance_tracker import PerformanceTracker

console = Console()


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


@click.command()
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
def cli(
    gitlab_url: str,
    admin_token: str,
    output: Optional[str],
    data_file: Optional[str],
    verbose: bool,
    refresh_data: bool,
    incremental: bool,
    workers: Optional[int],
    basic: bool,
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
            else:
                # New format: structured data
                repositories = cached_data.get("repositories", [])
                enhanced_analysis = cached_data.get("enhanced_analysis")

            # Create analyzer with cached data
            analyzer = GitLabAnalyzer(None)  # No client needed for cached data
            analyzer.repositories = repositories

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

            # Run parallel data collection
            from .parallel_collector import ParallelGitLabCollector

            parallel_collector = ParallelGitLabCollector(
                gitlab_client=client,
                max_workers=workers,
                performance_tracker=performance_tracker,
            )

            if verbose:
                parallel_collector.debug_mode = True

            # Collect repositories in parallel
            collected_repositories = parallel_collector.collect_all_projects_parallel(
                projects
            )
            analyzer.repositories = collected_repositories

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

                # Run all KPI collections in parallel
                console.print("[blue]📊 Running P1-P6 analyses in parallel...[/blue]")
                kpi_start_time = time.time()
                individual_times = {}

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

        # Run analysis on the data (fast - no API calls)
        console.print("[cyan]Analyzing data and generating report...[/cyan]")
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing analysis...", total=100)

            progress.update(
                task, advance=25, description="[cyan]Analyzing repositories..."
            )
            analyzer.analyze_repositories()

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
        cached_data = storage.load_data()
        cached_repos = {
            repo["id"]: repo for repo in cached_data.get("repositories", [])
        }

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


def _merge_with_cached_data(new_repositories: List[Dict], storage) -> List[Dict]:
    """Merge new repository data with unchanged cached repositories."""
    try:
        cached_data = storage.load_data()
        cached_repos = {
            repo["id"]: repo for repo in cached_data.get("repositories", [])
        }

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


if __name__ == "__main__":
    cli()
