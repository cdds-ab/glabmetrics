#!/usr/bin/env python3
"""Main CLI entry point for GitLab Statistics Analyzer."""

import click
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress

from .gitlab_client import GitLabClient
from .analyzer import GitLabAnalyzer
from .report_generator import HTMLReportGenerator
from .data_storage import GitLabDataStorage
from .performance_tracker import PerformanceTracker

console = Console()


@click.command()
@click.argument("gitlab_url", type=str)
@click.argument("admin_token", type=str)
@click.option(
    "--output",
    "-o",
    default="gitlab_report.html",
    help="Output HTML file path (default: gitlab_report.html)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--refresh-data",
    "-r",
    is_flag=True,
    help="Refresh data from GitLab API (default: use cached data if available)",
)
@click.option(
    "--data-file",
    "-d",
    default="gitlab_data.json",
    help="Data file path (default: gitlab_data.json)",
)
@click.option(
    "--skip-binary-scan",
    is_flag=True,
    help="Skip binary file detection (faster collection)",
)
def cli(
    gitlab_url: str,
    admin_token: str,
    output: str,
    verbose: bool,
    refresh_data: bool,
    data_file: str,
    skip_binary_scan: bool,
):
    """
    GitLab Statistics Analyzer

    Analyzes a GitLab instance and generates a comprehensive HTML report.

    GITLAB_URL: The base URL of the GitLab instance (e.g., https://gitlab.example.com)
    ADMIN_TOKEN: Admin access token for the GitLab API
    """
    if verbose:
        console.print("[green]Starting GitLab analysis...[/green]")

    try:
        # Initialize data storage
        storage = GitLabDataStorage(data_file)

        # Check if we should use cached data or refresh from API
        if not refresh_data and storage.data_exists():
            console.print(
                f"[cyan]Using cached data ({storage.get_data_age()}). Use --refresh-data to fetch new data.[/cyan]"
            )

            # Load cached data
            repositories, analysis_timestamp = storage.load_data()

            # Create analyzer with cached data
            analyzer = GitLabAnalyzer(None)  # No client needed for cached data
            analyzer.repositories = repositories
        else:
            # Fresh data collection from GitLab API
            console.print("[cyan]Collecting fresh data from GitLab API...[/cyan]")
            if skip_binary_scan:
                console.print("[yellow]Skipping binary file detection for faster collection...[/yellow]")

            # Initialize performance tracker
            performance_tracker = PerformanceTracker()
            performance_tracker.start_collection()

            # Initialize GitLab client with performance tracking
            client = GitLabClient(gitlab_url, admin_token, performance_tracker)

            # Test connection
            if not client.test_connection():
                console.print("[red]Error: Could not connect to GitLab instance or invalid token[/red]")
                sys.exit(1)

            if verbose:
                console.print("[green]✓ Connection established[/green]")
                console.print(f"[blue]GitLab Version: {client.get_gitlab_version()}[/blue]")

            # Initialize analyzer
            analyzer = GitLabAnalyzer(client)
            analyzer.skip_binary_scan = skip_binary_scan  # Pass flag to analyzer

            # Run data collection with progress bar
            with Progress() as progress:
                task = progress.add_task("[cyan]Collecting GitLab data...", total=100)

                # Collect data
                progress.update(task, advance=50, description="[cyan]Fetching projects...")
                performance_tracker.set_repository_count(len(client.get_projects()))
                analyzer.collect_project_data()

                progress.update(task, advance=30, description="[cyan]Saving data to cache...")

                # Save data to cache with performance stats
                analysis_timestamp = datetime.now()
                perf_stats = performance_tracker.get_performance_stats()
                storage.save_data(analyzer.repositories, analysis_timestamp, perf_stats)

                progress.update(task, advance=20, description="[cyan]Cache saved!")

            # Performance stats already retrieved above

            # Show performance summary
            console.print(f"[green]✓ Data collected and cached in {data_file}[/green]")
            console.print(f"[blue]Collection completed in {perf_stats.total_duration:.1f} seconds[/blue]")
            console.print(
                f"[blue]Total API calls: {perf_stats.total_api_calls} ({perf_stats.total_failed_calls} failed)[/blue]"
            )

            if verbose:
                performance_tracker.print_live_stats()

        # Run analysis on the data (fast - no API calls)
        console.print("[cyan]Analyzing data and generating report...[/cyan]")
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing analysis...", total=100)

            progress.update(task, advance=25, description="[cyan]Analyzing repositories...")
            analyzer.analyze_repositories()

            progress.update(task, advance=25, description="[cyan]Checking storage usage...")
            analyzer.analyze_storage()

            progress.update(task, advance=25, description="[cyan]Analyzing activity...")
            analyzer.analyze_activity()

            progress.update(task, advance=15, description="[cyan]Analyzing pipelines...")
            analyzer.analyze_pipelines()

            progress.update(task, advance=10, description="[cyan]Generating report...")

        # Generate HTML report
        report_generator = HTMLReportGenerator()
        analysis_results = analyzer.get_analysis_results()
        html_content = report_generator.generate_report(analysis_results)

        # Write report to file
        output_path = Path(output)
        output_path.write_text(html_content, encoding="utf-8")

        console.print(f"[green]✓ Report generated successfully: {output_path.absolute()}[/green]")

        if not refresh_data and storage.data_exists():
            console.print(f"[yellow]Data is {storage.get_data_age()}. Use --refresh-data for latest data.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    cli()
