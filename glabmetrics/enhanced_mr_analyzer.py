"""Enhanced Merge Request Analyzer - ChatGPT Prompt 2 Implementation"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

# import matplotlib.pyplot as plt  # Optional dependency - will skip chart if not available
from rich.console import Console
from rich.table import Table

from .gitlab_client import GitLabClient

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class MRKPIMetrics:
    """Merge Request KPI metrics for a single repository."""

    id: int
    path_with_namespace: str
    total_mrs_180d: int
    merged_mrs_180d: int
    avg_lead_time_hours: float
    median_lead_time_hours: float
    review_comments_avg: float
    stale_mrs_count: int
    stale_mrs_30d: List[Dict]  # MRs open >30 days
    mr_details: List[Dict]
    gitlab_url: str


@dataclass
class MRSystemAnalysis:
    """System-wide MR analysis results."""

    total_projects: int
    total_mrs_180d: int
    avg_system_lead_time: float
    median_system_lead_time: float
    avg_review_comments: float
    flagged_repositories: List[Dict]
    health_status: str


class EnhancedMRAnalyzer:
    """Analyzes merge request metrics according to ChatGPT Prompt 2."""

    def __init__(self, gitlab_client: GitLabClient):
        self.client = gitlab_client

    def collect_mr_kpis(self, projects: List[Dict]) -> List[MRKPIMetrics]:
        """
        ChatGPT Prompt 2 - collect_section:
        For each project gather:
        - id, path_with_namespace
        - merge_requests opened in last 180d: iid, created_at, merged_at
        - review notes per MR: /merge_requests/:iid/notes
        """
        console.print("[cyan]🔄 Collecting Merge Request KPIs...[/cyan]")

        metrics = []
        cutoff_date = datetime.now() - timedelta(days=180)

        for i, project in enumerate(projects, 1):
            console.print(
                f"[blue]Processing {project['path_with_namespace']} ({i}/{len(projects)})[/blue]"
            )

            try:
                project_id = project["id"]

                # Get merge requests from last 180 days
                mrs_180d = self.client.get_project_merge_requests(
                    project_id, created_after=cutoff_date.isoformat()
                )

                # Filter and collect MR details
                mr_details = []
                merged_mrs = []
                stale_mrs = []
                total_review_comments = 0

                for mr in mrs_180d:
                    created_at = datetime.fromisoformat(
                        mr["created_at"].replace("Z", "+00:00")
                    )
                    merged_at = None

                    if mr.get("merged_at"):
                        merged_at = datetime.fromisoformat(
                            mr["merged_at"].replace("Z", "+00:00")
                        )
                        merged_mrs.append(
                            {
                                "iid": mr["iid"],
                                "created_at": created_at,
                                "merged_at": merged_at,
                                "lead_time_hours": (
                                    merged_at - created_at
                                ).total_seconds()
                                / 3600,
                            }
                        )

                    # Check for stale MRs (open >30 days)
                    if mr["state"] == "opened":
                        days_open = (
                            datetime.now() - created_at.replace(tzinfo=None)
                        ).days
                        if days_open > 30:
                            stale_mrs.append(
                                {
                                    "iid": mr["iid"],
                                    "title": mr["title"],
                                    "created_at": created_at.isoformat(),
                                    "days_open": days_open,
                                    "web_url": mr.get(
                                        "web_url",
                                        f"{self.client.gitlab_url}/{project['path_with_namespace']}/-/merge_requests/{mr['iid']}",
                                    ),
                                }
                            )

                    # Get review comments (notes) for this MR
                    try:
                        notes = self.client.get_mr_discussions(project_id, mr["iid"])
                        review_comment_count = len(
                            [n for n in notes if n.get("individual_note", True)]
                        )
                        total_review_comments += review_comment_count

                        mr_details.append(
                            {
                                "iid": mr["iid"],
                                "title": mr["title"],
                                "state": mr["state"],
                                "created_at": created_at.isoformat(),
                                "merged_at": (
                                    merged_at.isoformat() if merged_at else None
                                ),
                                "review_comments": review_comment_count,
                                "web_url": mr.get(
                                    "web_url",
                                    f"{self.client.gitlab_url}/{project['path_with_namespace']}/-/merge_requests/{mr['iid']}",
                                ),
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not fetch notes for MR {mr['iid']} in {project['path_with_namespace']}: {e}"
                        )
                        mr_details.append(
                            {
                                "iid": mr["iid"],
                                "title": mr["title"],
                                "state": mr["state"],
                                "created_at": created_at.isoformat(),
                                "merged_at": (
                                    merged_at.isoformat() if merged_at else None
                                ),
                                "review_comments": 0,
                                "web_url": mr.get(
                                    "web_url",
                                    f"{self.client.gitlab_url}/{project['path_with_namespace']}/-/merge_requests/{mr['iid']}",
                                ),
                            }
                        )

                # Calculate metrics
                lead_times = [mr["lead_time_hours"] for mr in merged_mrs]
                avg_lead_time = statistics.mean(lead_times) if lead_times else 0.0
                median_lead_time = statistics.median(lead_times) if lead_times else 0.0

                review_comments_avg = (
                    total_review_comments / len(mrs_180d) if mrs_180d else 0.0
                )

                metrics.append(
                    MRKPIMetrics(
                        id=project_id,
                        path_with_namespace=project["path_with_namespace"],
                        total_mrs_180d=len(mrs_180d),
                        merged_mrs_180d=len(merged_mrs),
                        avg_lead_time_hours=avg_lead_time,
                        median_lead_time_hours=median_lead_time,
                        review_comments_avg=review_comments_avg,
                        stale_mrs_count=len(stale_mrs),
                        stale_mrs_30d=stale_mrs,
                        mr_details=mr_details,
                        gitlab_url=self.client.gitlab_url,
                    )
                )

            except Exception as e:
                logger.error(
                    f"Error analyzing MRs for {project['path_with_namespace']}: {e}"
                )
                continue

        console.print(
            f"[green]✅ Collected MR KPIs for {len(metrics)} projects[/green]"
        )
        return metrics

    def generate_mr_kpi_analysis(
        self, mr_metrics: List[MRKPIMetrics]
    ) -> MRSystemAnalysis:
        """
        ChatGPT Prompt 2 - analyse_section:
        Compute per repo:
        lead_time = mean(merged_at - created_at)
        review_comments_avg = total_notes / merged_MRs
        stale_MRs = count(open >30d)
        """
        console.print("[cyan]📊 Analyzing MR KPIs...[/cyan]")

        if not mr_metrics:
            return MRSystemAnalysis(
                total_projects=0,
                total_mrs_180d=0,
                avg_system_lead_time=0.0,
                median_system_lead_time=0.0,
                avg_review_comments=0.0,
                flagged_repositories=[],
                health_status="No data",
            )

        # System-wide calculations
        total_mrs = sum(m.total_mrs_180d for m in mr_metrics)
        all_lead_times = []
        all_review_comments = []
        flagged_repos = []

        for metric in mr_metrics:
            # Collect lead times for system average
            if metric.avg_lead_time_hours > 0:
                all_lead_times.append(metric.avg_lead_time_hours)

            # Collect review comments
            if metric.review_comments_avg > 0:
                all_review_comments.append(metric.review_comments_avg)

            # Flag repos with lead_time > 5 days (120 hours) OR stale_MRs > 3
            lead_time_days = metric.avg_lead_time_hours / 24
            if lead_time_days > 5 or metric.stale_mrs_count > 3:
                flagged_repos.append(
                    {
                        "repository": metric.path_with_namespace,
                        "lead_time_days": round(lead_time_days, 1),
                        "review_comments_avg": round(metric.review_comments_avg, 1),
                        "stale_mrs_count": metric.stale_mrs_count,
                        "reason": [],
                    }
                )

                if lead_time_days > 5:
                    flagged_repos[-1]["reason"].append(
                        f"Lead time > 5 days ({lead_time_days:.1f}d)"
                    )
                if metric.stale_mrs_count > 3:
                    flagged_repos[-1]["reason"].append(
                        f"Stale MRs > 3 ({metric.stale_mrs_count})"
                    )

        # System averages
        avg_system_lead_time = (
            statistics.mean(all_lead_times) if all_lead_times else 0.0
        )
        median_system_lead_time = (
            statistics.median(all_lead_times) if all_lead_times else 0.0
        )
        avg_review_comments = (
            statistics.mean(all_review_comments) if all_review_comments else 0.0
        )

        # Health status
        flagged_percentage = (
            (len(flagged_repos) / len(mr_metrics)) * 100 if mr_metrics else 0
        )
        if flagged_percentage == 0:
            health_status = "🟢 Excellent"
        elif flagged_percentage < 20:
            health_status = "🟡 Good"
        elif flagged_percentage < 50:
            health_status = "🟠 Needs Attention"
        else:
            health_status = "🔴 Critical"

        return MRSystemAnalysis(
            total_projects=len(mr_metrics),
            total_mrs_180d=total_mrs,
            avg_system_lead_time=avg_system_lead_time,
            median_system_lead_time=median_system_lead_time,
            avg_review_comments=avg_review_comments,
            flagged_repositories=flagged_repos,
            health_status=health_status,
        )

    def create_lead_time_chart(
        self,
        mr_metrics: List[MRKPIMetrics],
        output_path: str = "mr_lead_time_chart.png",
    ):
        """
        ChatGPT Prompt 2 - output_section:
        Create bar chart (matplotlib) of lead_time vs repos.
        """
        console.print("[cyan]📈 Creating lead time bar chart...[/cyan]")

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            console.print(
                "[yellow]⚠️ matplotlib not available, skipping chart generation[/yellow]"
            )
            return

        # Filter repositories with actual lead time data
        repos_with_data = [
            (m.path_with_namespace, m.avg_lead_time_hours / 24)
            for m in mr_metrics
            if m.avg_lead_time_hours > 0
        ]

        if not repos_with_data:
            console.print("[yellow]⚠️ No lead time data available for chart[/yellow]")
            return

        # Sort by lead time (descending)
        repos_with_data.sort(key=lambda x: x[1], reverse=True)

        # Take top 15 to avoid overcrowding
        repos_with_data = repos_with_data[:15]

        repo_names = [
            name.split("/")[-1] for name, _ in repos_with_data
        ]  # Just repo name
        lead_times = [time for _, time in repos_with_data]

        # Create bar chart
        plt.figure(figsize=(14, 8))
        bars = plt.bar(
            range(len(repo_names)),
            lead_times,
            color=["#ff4444" if t > 5 else "#44ff44" for t in lead_times],
        )

        plt.title(
            "Merge Request Lead Time by Repository (Last 180 Days)",
            fontsize=16,
            fontweight="bold",
        )
        plt.xlabel("Repository", fontsize=12)
        plt.ylabel("Average Lead Time (Days)", fontsize=12)
        plt.xticks(range(len(repo_names)), repo_names, rotation=45, ha="right")

        # Add value labels on bars
        for i, (bar, time) in enumerate(zip(bars, lead_times)):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                f"{time:.1f}d",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Add threshold line at 5 days
        plt.axhline(
            y=5, color="red", linestyle="--", alpha=0.7, label="5-day threshold"
        )
        plt.legend()

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        console.print(f"[green]✅ Lead time chart saved to {output_path}[/green]")

    def generate_markdown_report(
        self, analysis: MRSystemAnalysis, mr_metrics: List[MRKPIMetrics]
    ) -> str:
        """Generate comprehensive markdown report for MR KPIs."""
        report = []

        # Header
        report.append("## 🔄 Merge Request & Code Review Quality Analysis")
        report.append("")

        # System Overview
        report.append("### System Overview")
        report.append(f"- **Total Projects:** {analysis.total_projects}")
        report.append(f"- **Total MRs (180d):** {analysis.total_mrs_180d}")
        report.append(
            f"- **Average Lead Time:** {analysis.avg_system_lead_time / 24:.1f} days"
        )
        report.append(
            f"- **Median Lead Time:** {analysis.median_system_lead_time / 24:.1f} days"
        )
        report.append(
            f"- **Average Review Comments:** {analysis.avg_review_comments:.1f} per MR"
        )
        report.append(f"- **System Health:** {analysis.health_status}")
        report.append("")

        # Alert Summary
        report.append("### Alert Summary")
        flagged_count = len(analysis.flagged_repositories)
        healthy_count = analysis.total_projects - flagged_count

        report.append(f"- 🔴 **Flagged:** {flagged_count} projects")
        report.append(f"- 🟢 **Healthy:** {healthy_count} projects")
        report.append("")

        # Flagged Repositories Table
        if analysis.flagged_repositories:
            report.append("### 🚨 Flagged Repositories")
            report.append("")
            report.append(
                "| Repository | Lead Time | Review Comments | Stale MRs | Issues |"
            )
            report.append(
                "|------------|-----------|-----------------|-----------|--------|"
            )

            for repo in analysis.flagged_repositories:
                reasons = "; ".join(repo["reason"])
                report.append(
                    f"| [{repo['repository']}]({mr_metrics[0].gitlab_url}/{repo['repository']}) | {repo['lead_time_days']}d | {repo['review_comments_avg']} | {repo['stale_mrs_count']} | {reasons} |"
                )

            report.append("")

        # Repository Details
        report.append("### Repository Details")
        report.append("")
        report.append(
            "| Repo | MRs (180d) | Merged | Lead Time | Review Comments | Stale MRs | Status |"
        )
        report.append(
            "|------|------------|--------|-----------|-----------------|-----------|--------|"
        )

        for metric in sorted(
            mr_metrics, key=lambda x: x.avg_lead_time_hours, reverse=True
        ):
            lead_time_days = metric.avg_lead_time_hours / 24

            # Status determination
            status = "🟢 Healthy"
            if lead_time_days > 5 or metric.stale_mrs_count > 3:
                status = "🔴 Flagged"
            elif lead_time_days > 3 or metric.stale_mrs_count > 1:
                status = "🟡 Watch"

            # Stale MRs details
            stale_details = ""
            if metric.stale_mrs_30d:
                stale_links = []
                for stale_mr in metric.stale_mrs_30d[:3]:  # Show max 3
                    stale_links.append(
                        f"[#{stale_mr['iid']}]({stale_mr['web_url']}) ({stale_mr['days_open']}d)"
                    )
                stale_details = "<br>".join(stale_links)
                if len(metric.stale_mrs_30d) > 3:
                    stale_details += f"<br>+{len(metric.stale_mrs_30d) - 3} more"
            else:
                stale_details = "-"

            report.append(
                f"| [{metric.path_with_namespace}]({metric.gitlab_url}/{metric.path_with_namespace}) | {metric.total_mrs_180d} | {metric.merged_mrs_180d} | {lead_time_days:.1f}d | {metric.review_comments_avg:.1f} | {stale_details} | {status} |"
            )

        return "\n".join(report)

    def display_results_table(
        self, analysis: MRSystemAnalysis, mr_metrics: List[MRKPIMetrics]
    ):
        """Display results in a Rich table format."""
        # System Overview Table
        overview_table = Table(
            title="🔄 MR & Code Review System Overview", show_header=True
        )
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        overview_table.add_row("Total Projects", str(analysis.total_projects))
        overview_table.add_row("Total MRs (180d)", str(analysis.total_mrs_180d))
        overview_table.add_row(
            "Avg Lead Time", f"{analysis.avg_system_lead_time / 24:.1f} days"
        )
        overview_table.add_row(
            "Median Lead Time", f"{analysis.median_system_lead_time / 24:.1f} days"
        )
        overview_table.add_row(
            "Avg Review Comments", f"{analysis.avg_review_comments:.1f} per MR"
        )
        overview_table.add_row("System Health", analysis.health_status)

        console.print(overview_table)
        console.print()

        # Flagged Repositories Table
        if analysis.flagged_repositories:
            flagged_table = Table(title="🚨 Flagged Repositories", show_header=True)
            flagged_table.add_column("Repository", style="yellow")
            flagged_table.add_column("Lead Time", style="red")
            flagged_table.add_column("Stale MRs", style="bright_yellow")
            flagged_table.add_column("Issues", style="bright_red")

            for repo in analysis.flagged_repositories:
                reasons = "; ".join(repo["reason"])
                flagged_table.add_row(
                    repo["repository"],
                    f"{repo['lead_time_days']}d",
                    str(repo["stale_mrs_count"]),
                    reasons,
                )

            console.print(flagged_table)
