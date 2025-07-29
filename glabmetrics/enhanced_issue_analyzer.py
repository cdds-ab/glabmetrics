"""Enhanced Issue Analysis based on ChatGPT Prompt 1 - Ticket-KPI & älteste Issues."""

import concurrent.futures
import statistics
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from dateutil.parser import parse as parse_date
from rich.progress import Progress

from .gitlab_client import GitLabClient


@dataclass
class IssueKPIMetrics:
    """KPI metrics for issue management analysis."""

    project_id: int
    project_name: str
    path_with_namespace: str

    # Basic counts
    open_issues_count: int = 0
    total_issues_count: int = 0

    # Age analysis
    oldest_issues: List[Dict] = field(default_factory=list)  # Top 5 oldest
    avg_issue_age_days: float = 0.0
    issue_age_90th_percentile: float = 0.0

    # Alert flags
    is_critical_age: bool = False  # avg_age > 90 days
    is_high_volume: bool = False  # open_issues > 50
    alert_level: str = "green"  # green, yellow, red

    # Additional insights
    issues_over_30d: int = 0
    issues_over_90d: int = 0
    issues_over_365d: int = 0

    def calculate_alert_level(self):
        """Calculate overall alert level for this project."""
        if self.is_critical_age or self.is_high_volume or self.issues_over_365d > 0:
            self.alert_level = "red"
        elif (
            self.avg_issue_age_days > 30
            or self.open_issues_count > 20
            or self.issues_over_90d > 0
        ):
            self.alert_level = "yellow"
        else:
            self.alert_level = "green"


@dataclass
class IssueSystemAnalysis:
    """System-wide issue analysis results."""

    total_projects: int
    total_open_issues: int
    avg_issues_per_repo: float
    system_avg_age_days: float
    system_90th_percentile_days: float
    red_projects_count: int
    yellow_projects_count: int
    green_projects_count: int
    health_percentage: float
    critical_age_projects: List[IssueKPIMetrics]
    high_volume_projects: List[IssueKPIMetrics]
    oldest_issues_system_wide: List[Dict]
    analysis_timestamp: datetime

    @property
    def health_status(self) -> str:
        """Get health status string."""
        if self.health_percentage >= 80:
            return "🟢 Excellent"
        elif self.health_percentage >= 60:
            return "🟡 Good"
        elif self.health_percentage >= 40:
            return "🟠 Needs Attention"
        else:
            return "🔴 Critical"


class EnhancedIssueAnalyzer:
    """Enhanced Issue Analysis implementing ChatGPT Prompt 1 specifications."""

    def __init__(self, client: GitLabClient, max_workers: int = 8):
        self.client = client
        self.max_workers = max_workers
        self._lock = threading.Lock()
        self._processed_count = 0

    def collect_issue_kpis(self, projects: List[Dict]) -> List[IssueKPIMetrics]:
        """
        Collect issue KPIs for all projects following ChatGPT Prompt 1 pattern (Parallelized).

        collect_section: Fetch for each project:
        - id, path_with_namespace
        - open_issues_count
        - 5 oldest open issues: iid, title, created_at, author.username
        """
        if not projects:
            return []

        print(
            f"🎫 Collecting Issue KPIs for {len(projects)} projects (using {self.max_workers} workers)..."
        )

        # Reset progress tracking
        self._processed_count = 0
        issue_metrics = []

        # Use progress bar for better UX
        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing projects...", total=len(projects)
            )

            # Process projects in parallel
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:
                # Submit all projects for processing
                future_to_project = {
                    executor.submit(self._analyze_project_issues, project): project
                    for project in projects
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_project):
                    # Import and check for shutdown request
                    from .main import shutdown_handler

                    if shutdown_handler.is_shutdown_requested():
                        print("⚠️  Shutdown requested during issue analysis")
                        return issue_metrics  # Return partial results

                    project = future_to_project[future]
                    try:
                        metrics = future.result()
                        if metrics:
                            issue_metrics.append(metrics)

                        # Update progress
                        with self._lock:
                            self._processed_count += 1
                            progress.update(
                                task,
                                advance=1,
                                description=f"[cyan]Processed {self._processed_count}/{len(projects)} projects[/cyan]",
                            )

                    except Exception as e:
                        print(
                            f"    ⚠️ Error analyzing {project.get('name', 'Unknown')}: {e}"
                        )
                        # Add detailed logging for debugging
                        import traceback

                        print(f"    Stack trace: {traceback.format_exc()}")

                        # Still update progress for failed projects
                        with self._lock:
                            self._processed_count += 1
                            progress.update(task, advance=1)

        return issue_metrics

    def _analyze_project_issues(self, project: Dict) -> Optional[IssueKPIMetrics]:
        """Analyze issues for a single project."""
        project_id = project["id"]
        project_name = project.get("name", f"Project-{project_id}")
        path_with_namespace = project.get("path_with_namespace", "")

        metrics = IssueKPIMetrics(
            project_id=project_id,
            project_name=project_name,
            path_with_namespace=path_with_namespace,
        )

        # Get basic issue counts
        metrics.open_issues_count = project.get("open_issues_count", 0)

        # Get detailed issue data
        try:
            # Get all open issues sorted by creation date (oldest first)
            open_issues = self.client.get_project_issues(
                project_id, state="opened", per_page=100
            )

            # Debug: Print issue collection progress
            if hasattr(self, "_debug_enabled"):
                print(f"    Found {len(open_issues)} open issues for {project_name}")

            # Sort by created_at (oldest first)
            open_issues.sort(key=lambda x: x.get("created_at", ""))

            # Get oldest 5 issues with enriched data
            oldest_5 = []
            current_time = datetime.now()
            issue_ages = []

            for issue in open_issues[:5]:
                try:
                    created_at = parse_date(issue["created_at"])
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)

                    age_days = (current_time - created_at).days

                    oldest_issue = {
                        "iid": issue["iid"],
                        "title": issue["title"][:60]
                        + ("..." if len(issue["title"]) > 60 else ""),
                        "created_at": issue["created_at"],
                        "age_days": age_days,
                        "author_username": issue.get("author", {}).get(
                            "username", "Unknown"
                        ),
                        "web_url": issue.get("web_url", ""),
                    }
                    oldest_5.append(oldest_issue)

                except Exception:
                    continue

            metrics.oldest_issues = oldest_5

            # Calculate age statistics for all open issues
            for issue in open_issues:
                try:
                    created_at = parse_date(issue["created_at"])
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)

                    age_days = (current_time - created_at).days
                    issue_ages.append(age_days)

                    # Count issues by age brackets
                    if age_days > 365:
                        metrics.issues_over_365d += 1
                    elif age_days > 90:
                        metrics.issues_over_90d += 1
                    elif age_days > 30:
                        metrics.issues_over_30d += 1

                except Exception:
                    continue

            # Calculate statistics
            if issue_ages:
                metrics.avg_issue_age_days = statistics.mean(issue_ages)
                if len(issue_ages) >= 10:  # Need reasonable sample size
                    metrics.issue_age_90th_percentile = statistics.quantiles(
                        issue_ages, n=10
                    )[
                        8
                    ]  # 90th percentile
                else:
                    metrics.issue_age_90th_percentile = (
                        max(issue_ages) if issue_ages else 0
                    )

            # Set alert flags according to ChatGPT Prompt 1 criteria
            metrics.is_critical_age = metrics.avg_issue_age_days > 90
            metrics.is_high_volume = metrics.open_issues_count > 50
            metrics.calculate_alert_level()

            return metrics

        except Exception as e:
            print(f"    Error fetching issues for {project_name}: {e}")
            import traceback

            print(f"    Detailed error: {traceback.format_exc()}")
            return metrics  # Return metrics with basic info even if API calls fail

    def generate_issue_kpi_analysis(
        self, issue_metrics: List[IssueKPIMetrics]
    ) -> "IssueSystemAnalysis":
        """
        analyse_section: Generate comprehensive analysis of issue KPIs.

        Compute:
        - avg_issue_age_days = mean(today - created_at)
        - issue_age_90th_percentile
        """
        if not issue_metrics:
            return IssueSystemAnalysis(
                total_projects=0,
                total_open_issues=0,
                avg_issues_per_repo=0.0,
                system_avg_age_days=0.0,
                system_90th_percentile_days=0.0,
                red_projects_count=0,
                yellow_projects_count=0,
                green_projects_count=0,
                health_percentage=100.0,  # No projects = 100% healthy by default
                critical_age_projects=[],
                high_volume_projects=[],
                oldest_issues_system_wide=[],
                analysis_timestamp=datetime.now(),
            )

        # System-wide statistics
        total_open_issues = sum(m.open_issues_count for m in issue_metrics)
        avg_issues_per_repo = total_open_issues / len(issue_metrics)

        # Age statistics across all repos
        all_ages = []
        for metrics in issue_metrics:
            if metrics.oldest_issues:
                all_ages.extend([issue["age_days"] for issue in metrics.oldest_issues])

        system_avg_age = statistics.mean(all_ages) if all_ages else 0
        system_90th_percentile = (
            statistics.quantiles(all_ages, n=10)[8] if len(all_ages) >= 10 else 0
        )

        # Alert analysis
        red_projects = [m for m in issue_metrics if m.alert_level == "red"]
        yellow_projects = [m for m in issue_metrics if m.alert_level == "yellow"]
        green_projects = [m for m in issue_metrics if m.alert_level == "green"]

        # Top problematic projects
        critical_age_projects = sorted(
            [m for m in issue_metrics if m.is_critical_age],
            key=lambda x: x.avg_issue_age_days,
            reverse=True,
        )[:5]
        high_volume_projects = sorted(
            [m for m in issue_metrics if m.is_high_volume],
            key=lambda x: x.open_issues_count,
            reverse=True,
        )[:5]

        # Oldest issues across all projects
        all_oldest_issues = []
        for metrics in issue_metrics:
            for issue in metrics.oldest_issues:
                issue["project_name"] = metrics.project_name
                issue["project_path"] = metrics.path_with_namespace
                all_oldest_issues.append(issue)

        all_oldest_issues.sort(key=lambda x: x["age_days"], reverse=True)

        return IssueSystemAnalysis(
            total_projects=len(issue_metrics),
            total_open_issues=total_open_issues,
            avg_issues_per_repo=avg_issues_per_repo,
            system_avg_age_days=system_avg_age,
            system_90th_percentile_days=system_90th_percentile,
            red_projects_count=len(red_projects),
            yellow_projects_count=len(yellow_projects),
            green_projects_count=len(green_projects),
            health_percentage=(len(green_projects) / len(issue_metrics)) * 100,
            critical_age_projects=critical_age_projects,
            high_volume_projects=high_volume_projects,
            oldest_issues_system_wide=all_oldest_issues[:10],
            analysis_timestamp=datetime.now(),
        )

    def generate_markdown_report(
        self,
        analysis: IssueSystemAnalysis,
        detailed_metrics: List[IssueKPIMetrics] = None,
    ) -> str:
        """
        output_section: Generate Markdown table following ChatGPT Prompt 1 format.

        Generate a Markdown table with columns:
        Repo • Open Issues • Oldest5(links) • Avg Age • 90-Perc Age.
        Highlight (red) repos with avg_age > 90 days OR open_issues > 50.
        """
        if detailed_metrics is None:
            detailed_metrics = []

        markdown = []

        # Header with system statistics
        markdown.append("## 🎫 Issue KPI Analysis")
        markdown.append("")
        markdown.append("### System Overview")
        markdown.append(f"- **Total Projects:** {analysis.total_projects}")
        markdown.append(f"- **Total Open Issues:** {analysis.total_open_issues}")
        markdown.append(
            f"- **Average Issues per Repo:** {analysis.avg_issues_per_repo:.1f}"
        )
        markdown.append(
            f"- **System Average Age:** {analysis.system_avg_age_days:.1f} days"
        )
        markdown.append(
            f"- **Health Status:** {analysis.health_percentage:.1f}% projects healthy"
        )
        markdown.append("")

        # Alert summary
        markdown.append("### Alert Summary")
        markdown.append(f"- 🔴 **Critical:** {analysis.red_projects_count} projects")
        markdown.append(f"- 🟡 **Warning:** {analysis.yellow_projects_count} projects")
        markdown.append(f"- 🟢 **Healthy:** {analysis.green_projects_count} projects")
        markdown.append("")

        # Main table
        markdown.append("### Repository Details")
        markdown.append("")
        markdown.append(
            "| Repo | Open Issues | Oldest 5 Issues | Avg Age | 90th Perc | Status |"
        )
        markdown.append(
            "|------|-------------|------------------|---------|------------|--------|"
        )

        # Sort by alert level (red first) then by avg age
        sorted_metrics = sorted(
            detailed_metrics,
            key=lambda x: (
                0 if x.alert_level == "red" else 1 if x.alert_level == "yellow" else 2,
                -x.avg_issue_age_days,
            ),
        )

        for metrics in sorted_metrics:
            # Repository name with link
            repo_link = f"[{metrics.project_name}](https://gitlab.example.com/{metrics.path_with_namespace})"

            # Open issues count
            issues_cell = str(metrics.open_issues_count)
            if metrics.is_high_volume:
                issues_cell = f"**{issues_cell}**"

            # Oldest 5 issues with links
            oldest_cell = ""
            if metrics.oldest_issues:
                issue_links = []
                for issue in metrics.oldest_issues[
                    :3
                ]:  # Show top 3 to keep table readable
                    link = f"[#{issue['iid']}]({issue.get('web_url', '#')}) ({issue['age_days']}d)"
                    issue_links.append(link)
                oldest_cell = "<br>".join(issue_links)
                if len(metrics.oldest_issues) > 3:
                    oldest_cell += f"<br>+{len(metrics.oldest_issues) - 3} more"
            else:
                oldest_cell = "-"

            # Average age
            avg_age_cell = f"{metrics.avg_issue_age_days:.1f}d"
            if metrics.is_critical_age:
                avg_age_cell = f"**{avg_age_cell}**"

            # 90th percentile
            perc_90_cell = (
                f"{metrics.issue_age_90th_percentile:.1f}d"
                if metrics.issue_age_90th_percentile > 0
                else "-"
            )

            # Status indicator
            status_map = {
                "red": "🔴 Critical",
                "yellow": "🟡 Warning",
                "green": "🟢 Healthy",
            }
            status_cell = status_map.get(metrics.alert_level, "❓ Unknown")

            markdown.append(
                f"| {repo_link} | {issues_cell} | {oldest_cell} | {avg_age_cell} | {perc_90_cell} | {status_cell} |"
            )

        # Top concerns section
        if analysis.critical_age_projects:
            markdown.append("")
            markdown.append("### 🚨 Critical Age Projects (>90 days average)")
            for project in analysis.critical_age_projects:
                markdown.append(
                    f"- **{project.project_name}**: {project.avg_issue_age_days:.1f} days average"
                )

        if analysis.high_volume_projects:
            markdown.append("")
            markdown.append("### 📈 High Volume Projects (>50 open issues)")
            for project in analysis.high_volume_projects:
                markdown.append(
                    f"- **{project.project_name}**: {project.open_issues_count} open issues"
                )

        return "\n".join(markdown)
