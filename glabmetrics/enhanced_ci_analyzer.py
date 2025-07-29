"""Enhanced CI Runner & Jenkins Webhooks Analyzer - ChatGPT Prompt 3 Implementation"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from .gitlab_client import GitLabClient

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class CIRunnerMetrics:
    """CI Runner metrics for a single repository."""

    id: int
    path_with_namespace: str
    total_pipelines_30d: int
    successful_pipelines: int
    failed_pipelines: int
    success_rate: float
    avg_duration_minutes: float
    median_duration_minutes: float
    runners_used: List[Dict]  # Runner details
    pipeline_frequency: float  # pipelines per day
    latest_pipeline_status: str
    webhook_configured: bool
    webhook_url: Optional[str]
    jenkins_integration: bool
    pipeline_details: List[Dict]
    gitlab_url: str


@dataclass
class CISystemAnalysis:
    """System-wide CI analysis results."""

    total_projects: int
    total_pipelines_30d: int
    system_success_rate: float
    avg_duration_minutes: float
    projects_with_ci: int
    projects_with_webhooks: int
    projects_with_jenkins: int
    most_active_ci_projects: List[Dict]
    problematic_projects: List[Dict]  # Low success rate or long duration
    runner_utilization: Dict[str, Any]
    health_status: str


class EnhancedCIAnalyzer:
    """Analyzes CI Runner usage and Jenkins webhooks according to ChatGPT Prompt 3."""

    def __init__(self, gitlab_client: GitLabClient):
        self.client = gitlab_client

    def collect_ci_kpis(self, projects: List[Dict]) -> List[CIRunnerMetrics]:
        """
        ChatGPT Prompt 3 - collect_section:
        For each project gather:
        - id, path_with_namespace
        - pipelines from last 30d: status, duration, runner_id
        - webhook configurations: url, jenkins_url if exists
        """
        console.print("[cyan]🏗️ Collecting CI Runner & Jenkins KPIs...[/cyan]")

        metrics = []
        cutoff_date = datetime.now() - timedelta(days=30)

        for i, project in enumerate(projects, 1):
            console.print(
                f"[blue]Processing {project['path_with_namespace']} ({i}/{len(projects)})[/blue]"
            )

            try:
                project_id = project["id"]

                # Get pipelines from last 30 days
                pipelines_30d = self.client.get_project_pipelines(
                    project_id, updated_after=cutoff_date.isoformat()
                )

                # Analyze pipeline data
                successful_pipelines = 0
                failed_pipelines = 0
                durations = []
                runners_used = {}
                pipeline_details = []

                for pipeline in pipelines_30d:
                    status = pipeline.get("status", "unknown")
                    duration = pipeline.get("duration")

                    if status == "success":
                        successful_pipelines += 1
                    elif status in ["failed", "canceled", "skipped"]:
                        failed_pipelines += 1

                    if duration:
                        durations.append(duration / 60)  # Convert to minutes

                    # Get detailed pipeline info
                    try:
                        detailed_pipeline = self.client.get_pipeline_details(
                            project_id, pipeline["id"]
                        )
                        if detailed_pipeline:
                            # Extract runner information
                            jobs = self.client.get_pipeline_jobs(
                                project_id, pipeline["id"]
                            )
                            for job in jobs:
                                runner = job.get("runner")
                                if runner:
                                    runner_id = runner.get("id")
                                    if runner_id:
                                        if runner_id not in runners_used:
                                            runners_used[runner_id] = {
                                                "id": runner_id,
                                                "description": runner.get(
                                                    "description", "Unknown"
                                                ),
                                                "is_shared": runner.get(
                                                    "is_shared", False
                                                ),
                                                "job_count": 0,
                                            }
                                        runners_used[runner_id]["job_count"] += 1

                            pipeline_details.append(
                                {
                                    "id": pipeline["id"],
                                    "status": status,
                                    "duration": duration,
                                    "created_at": pipeline.get("created_at"),
                                    "web_url": pipeline.get(
                                        "web_url",
                                        f"{self.client.gitlab_url}/{project['path_with_namespace']}/-/pipelines/{pipeline['id']}",
                                    ),
                                }
                            )
                    except Exception as e:
                        logger.warning(
                            f"Could not get detailed pipeline info for {pipeline['id']}: {e}"
                        )

                # Calculate metrics
                total_completed = successful_pipelines + failed_pipelines
                success_rate = (
                    (successful_pipelines / total_completed * 100)
                    if total_completed > 0
                    else 0
                )
                avg_duration = statistics.mean(durations) if durations else 0
                median_duration = statistics.median(durations) if durations else 0
                pipeline_frequency = len(pipelines_30d) / 30.0  # per day

                # Check for webhook configurations
                webhook_configured = False
                webhook_url = None
                jenkins_integration = False

                try:
                    # Get project hooks
                    hooks = self.client.get_project_hooks(project_id)
                    for hook in hooks:
                        webhook_configured = True
                        url = hook.get("url", "")
                        if not webhook_url:  # Store first webhook URL
                            webhook_url = url
                        if "jenkins" in url.lower():
                            jenkins_integration = True
                except Exception as e:
                    logger.warning(
                        f"Could not fetch hooks for {project['path_with_namespace']}: {e}"
                    )

                # Latest pipeline status
                latest_status = (
                    pipelines_30d[0].get("status", "none") if pipelines_30d else "none"
                )

                metrics.append(
                    CIRunnerMetrics(
                        id=project_id,
                        path_with_namespace=project["path_with_namespace"],
                        total_pipelines_30d=len(pipelines_30d),
                        successful_pipelines=successful_pipelines,
                        failed_pipelines=failed_pipelines,
                        success_rate=success_rate,
                        avg_duration_minutes=avg_duration,
                        median_duration_minutes=median_duration,
                        runners_used=list(runners_used.values()),
                        pipeline_frequency=pipeline_frequency,
                        latest_pipeline_status=latest_status,
                        webhook_configured=webhook_configured,
                        webhook_url=webhook_url,
                        jenkins_integration=jenkins_integration,
                        pipeline_details=pipeline_details[:10],  # Limit to latest 10
                        gitlab_url=self.client.gitlab_url,
                    )
                )

            except Exception as e:
                logger.error(
                    f"Error analyzing CI for {project['path_with_namespace']}: {e}"
                )
                continue

        console.print(
            f"[green]✅ Collected CI KPIs for {len(metrics)} projects[/green]"
        )
        return metrics

    def generate_ci_kpi_analysis(
        self, ci_metrics: List[CIRunnerMetrics]
    ) -> CISystemAnalysis:
        """
        ChatGPT Prompt 3 - analyse_section:
        Compute per repo:
        success_rate = successful_pipelines / total_pipelines
        avg_duration = mean(pipeline_durations)
        webhook usage and Jenkins integrations
        """
        console.print("[cyan]🔍 Analyzing CI KPIs...[/cyan]")

        if not ci_metrics:
            return CISystemAnalysis(
                total_projects=0,
                total_pipelines_30d=0,
                system_success_rate=0.0,
                avg_duration_minutes=0.0,
                projects_with_ci=0,
                projects_with_webhooks=0,
                projects_with_jenkins=0,
                most_active_ci_projects=[],
                problematic_projects=[],
                runner_utilization={},
                health_status="No data",
            )

        # System-wide calculations
        total_pipelines = sum(m.total_pipelines_30d for m in ci_metrics)
        _ = len([m for m in ci_metrics if m.total_pipelines_30d > 0])
        projects_with_webhooks = len([m for m in ci_metrics if m.webhook_configured])
        projects_with_jenkins = len([m for m in ci_metrics if m.jenkins_integration])

        # Projects with ANY form of CI (GitLab + Jenkins)
        projects_with_any_ci = len(
            [
                m
                for m in ci_metrics
                if m.total_pipelines_30d > 0 or m.jenkins_integration
            ]
        )
        projects_with_ci = projects_with_any_ci  # Use comprehensive count

        # Success rate calculation (weighted by pipeline count)
        total_successful = sum(m.successful_pipelines for m in ci_metrics)
        total_completed = sum(
            m.successful_pipelines + m.failed_pipelines for m in ci_metrics
        )
        system_success_rate = (
            (total_successful / total_completed * 100) if total_completed > 0 else 0
        )

        # Average duration (weighted by pipeline count)
        durations_weighted = []
        for metric in ci_metrics:
            if metric.total_pipelines_30d > 0 and metric.avg_duration_minutes > 0:
                # Weight by number of pipelines
                for _ in range(metric.total_pipelines_30d):
                    durations_weighted.append(metric.avg_duration_minutes)

        avg_duration = statistics.mean(durations_weighted) if durations_weighted else 0

        # Most active CI projects (by pipeline frequency)
        most_active = sorted(
            [m for m in ci_metrics if m.total_pipelines_30d > 0],
            key=lambda x: x.pipeline_frequency,
            reverse=True,
        )[:5]

        most_active_projects = [
            {
                "repository": m.path_with_namespace,
                "pipelines_30d": m.total_pipelines_30d,
                "frequency": f"{m.pipeline_frequency:.1f}/day",
                "success_rate": f"{m.success_rate:.1f}%",
            }
            for m in most_active
        ]

        # Problematic projects (success rate <80% OR avg duration >60min)
        problematic = []
        for metric in ci_metrics:
            if metric.total_pipelines_30d > 0:  # Only consider projects with CI
                issues = []
                if metric.success_rate < 80:
                    issues.append(f"Low success rate ({metric.success_rate:.1f}%)")
                if metric.avg_duration_minutes > 60:
                    issues.append(
                        f"Long duration ({metric.avg_duration_minutes:.1f}min)"
                    )

                if issues:
                    problematic.append(
                        {
                            "repository": metric.path_with_namespace,
                            "success_rate": metric.success_rate,
                            "avg_duration": metric.avg_duration_minutes,
                            "issues": issues,
                        }
                    )

        # Runner utilization
        all_runners = {}
        for metric in ci_metrics:
            for runner in metric.runners_used:
                runner_id = runner["id"]
                if runner_id not in all_runners:
                    all_runners[runner_id] = {
                        "id": runner_id,
                        "description": runner["description"],
                        "is_shared": runner["is_shared"],
                        "total_jobs": 0,
                        "projects_using": 0,
                    }
                all_runners[runner_id]["total_jobs"] += runner["job_count"]
                all_runners[runner_id]["projects_using"] += 1

        runner_utilization = {
            "total_runners": len(all_runners),
            "shared_runners": len([r for r in all_runners.values() if r["is_shared"]]),
            "private_runners": len(
                [r for r in all_runners.values() if not r["is_shared"]]
            ),
            "top_runners": sorted(
                all_runners.values(), key=lambda x: x["total_jobs"], reverse=True
            )[:5],
        }

        # Health status
        ci_adoption = (projects_with_ci / len(ci_metrics)) * 100 if ci_metrics else 0

        if system_success_rate >= 90 and ci_adoption >= 80:
            health_status = "🟢 Excellent"
        elif system_success_rate >= 80 and ci_adoption >= 60:
            health_status = "🟡 Good"
        elif system_success_rate >= 70 or ci_adoption >= 40:
            health_status = "🟠 Needs Attention"
        else:
            health_status = "🔴 Critical"

        return CISystemAnalysis(
            total_projects=len(ci_metrics),
            total_pipelines_30d=total_pipelines,
            system_success_rate=system_success_rate,
            avg_duration_minutes=avg_duration,
            projects_with_ci=projects_with_ci,
            projects_with_webhooks=projects_with_webhooks,
            projects_with_jenkins=projects_with_jenkins,
            most_active_ci_projects=most_active_projects,
            problematic_projects=problematic,
            runner_utilization=runner_utilization,
            health_status=health_status,
        )

    def generate_markdown_report(
        self, analysis: CISystemAnalysis, ci_metrics: List[CIRunnerMetrics]
    ) -> str:
        """Generate comprehensive markdown report for CI KPIs."""
        report = []

        # Header
        report.append("## 🏗️ CI Runner Usage & Jenkins Webhooks Analysis")
        report.append("")

        # System Overview
        report.append("### System Overview")
        report.append(f"- **Total Projects:** {analysis.total_projects}")
        gitlab_ci_count = (
            len([m for m in ci_metrics if m.total_pipelines_30d > 0])
            if hasattr(self, "ci_metrics")
            else 0
        )
        jenkins_count = analysis.projects_with_jenkins

        report.append(
            f"- **Projects with CI:** {analysis.projects_with_ci} ({(analysis.projects_with_ci/analysis.total_projects*100):.1f}%)"
        )
        report.append(f"  - GitLab CI: {gitlab_ci_count} projects")
        report.append(f"  - Jenkins Integration: {jenkins_count} projects")
        report.append(f"- **Total Pipelines (30d):** {analysis.total_pipelines_30d}")
        report.append(f"- **System Success Rate:** {analysis.system_success_rate:.1f}%")
        report.append(
            f"- **Average Duration:** {analysis.avg_duration_minutes:.1f} minutes"
        )
        report.append(
            f"- **Projects with Webhooks:** {analysis.projects_with_webhooks}"
        )
        report.append(f"- **Jenkins Integrations:** {analysis.projects_with_jenkins}")
        report.append(f"- **System Health:** {analysis.health_status}")
        report.append("")

        # Runner Utilization
        report.append("### 🏃 Runner Utilization")
        ru = analysis.runner_utilization
        report.append(f"- **Total Runners:** {ru['total_runners']}")
        report.append(f"- **Shared Runners:** {ru['shared_runners']}")
        report.append(f"- **Private Runners:** {ru['private_runners']}")
        report.append("")

        if ru["top_runners"]:
            report.append("#### Top Runners by Usage")
            report.append("| Runner | Description | Type | Jobs | Projects |")
            report.append("|--------|-------------|------|------|----------|")
            for runner in ru["top_runners"]:
                runner_type = "Shared" if runner["is_shared"] else "Private"
                report.append(
                    f"| {runner['id']} | {runner['description']} | {runner_type} | {runner['total_jobs']} | {runner['projects_using']} |"
                )
            report.append("")

        # Most Active CI Projects
        if analysis.most_active_ci_projects:
            report.append("### 🚀 Most Active CI Projects")
            report.append("| Repository | Pipelines (30d) | Frequency | Success Rate |")
            report.append(
                "|------------|------------------|-----------|--------------|"
            )
            for project in analysis.most_active_ci_projects:
                report.append(
                    f"| [{project['repository']}]({ci_metrics[0].gitlab_url}/{project['repository']}) | {project['pipelines_30d']} | {project['frequency']} | {project['success_rate']} |"
                )
            report.append("")

        # Problematic Projects
        if analysis.problematic_projects:
            report.append("### 🚨 Problematic Projects")
            report.append("| Repository | Success Rate | Avg Duration | Issues |")
            report.append("|------------|--------------|--------------|--------|")
            for project in analysis.problematic_projects:
                issues = "; ".join(project["issues"])
                report.append(
                    f"| [{project['repository']}]({ci_metrics[0].gitlab_url}/{project['repository']}) | {project['success_rate']:.1f}% | {project['avg_duration']:.1f}min | {issues} |"
                )
            report.append("")

        # Repository Details
        report.append("### Repository Details")
        report.append("")
        report.append(
            "| Repo | Pipelines (30d) | Success Rate | Avg Duration | Webhooks | Jenkins | Latest Status |"
        )
        report.append(
            "|------|------------------|--------------|--------------|----------|---------|---------------|"
        )

        # Sort by pipeline activity
        sorted_metrics = sorted(
            ci_metrics, key=lambda x: x.total_pipelines_30d, reverse=True
        )

        for metric in sorted_metrics:
            webhook_status = "✅" if metric.webhook_configured else "❌"
            jenkins_status = "✅" if metric.jenkins_integration else "❌"

            # Status icon
            status_icons = {
                "success": "🟢",
                "failed": "🔴",
                "running": "🟡",
                "pending": "⏳",
                "canceled": "⚪",
                "skipped": "⚪",
                "none": "⚫",
            }
            status_display = f"{status_icons.get(metric.latest_pipeline_status, '❓')} {metric.latest_pipeline_status}"

            report.append(
                f"| [{metric.path_with_namespace}]({metric.gitlab_url}/{metric.path_with_namespace}) | {metric.total_pipelines_30d} | {metric.success_rate:.1f}% | {metric.avg_duration_minutes:.1f}min | {webhook_status} | {jenkins_status} | {status_display} |"
            )

        return "\n".join(report)

    def display_results_table(
        self, analysis: CISystemAnalysis, ci_metrics: List[CIRunnerMetrics]
    ):
        """Display results in a Rich table format."""
        # System Overview Table
        overview_table = Table(
            title="🏗️ CI Runner & Jenkins System Overview", show_header=True
        )
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        overview_table.add_row("Total Projects", str(analysis.total_projects))
        overview_table.add_row(
            "Projects with CI",
            f"{analysis.projects_with_ci} ({(analysis.projects_with_ci/analysis.total_projects*100):.1f}%)",
        )
        overview_table.add_row(
            "Total Pipelines (30d)", str(analysis.total_pipelines_30d)
        )
        overview_table.add_row(
            "System Success Rate", f"{analysis.system_success_rate:.1f}%"
        )
        overview_table.add_row(
            "Avg Duration", f"{analysis.avg_duration_minutes:.1f} min"
        )
        overview_table.add_row(
            "Projects with Webhooks", str(analysis.projects_with_webhooks)
        )
        overview_table.add_row(
            "Jenkins Integrations", str(analysis.projects_with_jenkins)
        )
        overview_table.add_row("System Health", analysis.health_status)

        console.print(overview_table)
        console.print()

        # Problematic Projects Table
        if analysis.problematic_projects:
            problematic_table = Table(
                title="🚨 Problematic CI Projects", show_header=True
            )
            problematic_table.add_column("Repository", style="yellow")
            problematic_table.add_column("Success Rate", style="red")
            problematic_table.add_column("Avg Duration", style="bright_yellow")
            problematic_table.add_column("Issues", style="bright_red")

            for project in analysis.problematic_projects:
                issues = "; ".join(project["issues"])
                problematic_table.add_row(
                    project["repository"],
                    f"{project['success_rate']:.1f}%",
                    f"{project['avg_duration']:.1f}min",
                    issues,
                )

            console.print(problematic_table)
            console.print()

        # Runner Utilization Table
        ru = analysis.runner_utilization
        if ru["top_runners"]:
            runner_table = Table(title="🏃 Top Runner Utilization", show_header=True)
            runner_table.add_column("Runner ID", style="cyan")
            runner_table.add_column("Description", style="white")
            runner_table.add_column("Type", style="blue")
            runner_table.add_column("Jobs", style="green")
            runner_table.add_column("Projects", style="yellow")

            for runner in ru["top_runners"]:
                runner_type = "Shared" if runner["is_shared"] else "Private"
                runner_table.add_row(
                    str(runner["id"]),
                    runner["description"],
                    runner_type,
                    str(runner["total_jobs"]),
                    str(runner["projects_using"]),
                )

            console.print(runner_table)
