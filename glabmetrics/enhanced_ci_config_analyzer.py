"""Enhanced GitLab-CI Configuration Check Analyzer - ChatGPT Prompt 4 Implementation"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.table import Table

from .gitlab_client import GitLabClient

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class CIConfigMetrics:
    """CI Configuration metrics for a single repository."""

    id: int
    path_with_namespace: str
    has_gitlab_ci: bool
    config_content: Optional[str]
    stages_defined: List[str]
    jobs_count: int
    uses_docker: bool
    uses_cache: bool
    uses_artifacts: bool
    security_scans: List[str]  # Types of security scanning
    deployment_stages: List[str]
    config_complexity: int  # Lines of YAML
    syntax_valid: bool
    syntax_errors: List[str]
    best_practices_score: float  # 0-100
    recommendations: List[str]
    gitlab_url: str


@dataclass
class CIConfigSystemAnalysis:
    """System-wide CI configuration analysis results."""

    total_projects: int
    projects_with_ci_config: int
    avg_config_complexity: float
    common_patterns: Dict[str, int]
    security_adoption: Dict[str, int]
    best_practices_summary: Dict[str, Any]
    problematic_configs: List[Dict]
    exemplary_configs: List[Dict]
    health_status: str


class EnhancedCIConfigAnalyzer:
    """Analyzes GitLab-CI configuration files according to ChatGPT Prompt 4."""

    def __init__(self, gitlab_client: GitLabClient):
        self.client = gitlab_client

    def collect_ci_config_kpis(self, projects: List[Dict]) -> List[CIConfigMetrics]:
        """
        ChatGPT Prompt 4 - collect_section:
        For each project gather:
        - id, path_with_namespace
        - .gitlab-ci.yml content and structure analysis
        - stages, jobs, docker usage, caching, security scans
        """
        console.print("[cyan]⚙️ Collecting GitLab-CI Configuration KPIs...[/cyan]")

        metrics = []

        for i, project in enumerate(projects, 1):
            console.print(
                f"[blue]Processing {project['path_with_namespace']} ({i}/{len(projects)})[/blue]"
            )

            try:
                project_id = project["id"]

                # Try to get .gitlab-ci.yml file
                ci_config_content = None
                has_gitlab_ci = False

                try:
                    ci_file = self.client.get_repository_file(
                        project_id, ".gitlab-ci.yml"
                    )
                    if ci_file:
                        ci_config_content = ci_file.get("content", "")
                        if ci_config_content:
                            # Decode base64 if needed
                            import base64

                            try:
                                ci_config_content = base64.b64decode(
                                    ci_config_content
                                ).decode("utf-8")
                                has_gitlab_ci = True
                            except Exception:
                                has_gitlab_ci = False
                except Exception as e:
                    logger.debug(
                        f"No .gitlab-ci.yml found in {project['path_with_namespace']}: {e}"
                    )

                if has_gitlab_ci and ci_config_content:
                    # Analyze CI configuration
                    analysis = self._analyze_ci_config(ci_config_content)

                    metrics.append(
                        CIConfigMetrics(
                            id=project_id,
                            path_with_namespace=project["path_with_namespace"],
                            has_gitlab_ci=True,
                            config_content=ci_config_content,
                            stages_defined=analysis["stages"],
                            jobs_count=analysis["jobs_count"],
                            uses_docker=analysis["uses_docker"],
                            uses_cache=analysis["uses_cache"],
                            uses_artifacts=analysis["uses_artifacts"],
                            security_scans=analysis["security_scans"],
                            deployment_stages=analysis["deployment_stages"],
                            config_complexity=analysis["complexity"],
                            syntax_valid=analysis["syntax_valid"],
                            syntax_errors=analysis["syntax_errors"],
                            best_practices_score=analysis["best_practices_score"],
                            recommendations=analysis["recommendations"],
                            gitlab_url=self.client.gitlab_url,
                        )
                    )
                else:
                    # No CI config found
                    metrics.append(
                        CIConfigMetrics(
                            id=project_id,
                            path_with_namespace=project["path_with_namespace"],
                            has_gitlab_ci=False,
                            config_content=None,
                            stages_defined=[],
                            jobs_count=0,
                            uses_docker=False,
                            uses_cache=False,
                            uses_artifacts=False,
                            security_scans=[],
                            deployment_stages=[],
                            config_complexity=0,
                            syntax_valid=True,
                            syntax_errors=[],
                            best_practices_score=0.0,
                            recommendations=["Add .gitlab-ci.yml to enable CI/CD"],
                            gitlab_url=self.client.gitlab_url,
                        )
                    )

            except Exception as e:
                logger.error(
                    f"Error analyzing CI config for {project['path_with_namespace']}: {e}"
                )
                continue

        console.print(
            f"[green]✅ Collected CI Config KPIs for {len(metrics)} projects[/green]"
        )
        return metrics

    def _analyze_ci_config(self, config_content: str) -> Dict[str, Any]:
        """Analyze GitLab-CI YAML configuration content."""
        analysis = {
            "stages": [],
            "jobs_count": 0,
            "uses_docker": False,
            "uses_cache": False,
            "uses_artifacts": False,
            "security_scans": [],
            "deployment_stages": [],
            "complexity": len(config_content.split("\n")),
            "syntax_valid": True,
            "syntax_errors": [],
            "best_practices_score": 0.0,
            "recommendations": [],
        }

        try:
            # Parse YAML
            config = yaml.safe_load(config_content)
            if not config:
                analysis["syntax_valid"] = False
                analysis["syntax_errors"].append("Empty or invalid YAML")
                return analysis

            # Extract stages
            if "stages" in config:
                analysis["stages"] = config["stages"]

            # Count jobs and analyze features
            docker_patterns = ["image:", "services:", "docker:"]
            cache_patterns = ["cache:", "paths:", "key:"]
            artifacts_patterns = ["artifacts:", "paths:", "reports:"]
            security_patterns = {
                "sast": ["sast", "security", "sonarqube"],
                "dependency_scanning": ["dependency", "npm audit", "pip-audit"],
                "container_scanning": ["container_scanning", "trivy", "clair"],
                "secret_detection": ["secret_detection", "gitleaks"],
                "license_scanning": ["license_scanning"],
            }

            for key, value in config.items():
                if key.startswith(".") or key in [
                    "stages",
                    "variables",
                    "before_script",
                    "after_script",
                ]:
                    continue

                # This is likely a job
                analysis["jobs_count"] += 1

                if isinstance(value, dict):
                    job_content = str(value).lower()
                    config_section = yaml.dump(value).lower()

                    # Check for Docker usage
                    if any(pattern in config_section for pattern in docker_patterns):
                        analysis["uses_docker"] = True

                    # Check for cache usage
                    if any(pattern in config_section for pattern in cache_patterns):
                        analysis["uses_cache"] = True

                    # Check for artifacts
                    if any(pattern in config_section for pattern in artifacts_patterns):
                        analysis["uses_artifacts"] = True

                    # Check for security scans
                    for scan_type, patterns in security_patterns.items():
                        if any(pattern in job_content for pattern in patterns):
                            if scan_type not in analysis["security_scans"]:
                                analysis["security_scans"].append(scan_type)

                    # Check for deployment stages
                    if "stage" in value:
                        stage = value["stage"].lower()
                        if any(
                            deploy_word in stage
                            for deploy_word in [
                                "deploy",
                                "production",
                                "staging",
                                "release",
                            ]
                        ):
                            if stage not in analysis["deployment_stages"]:
                                analysis["deployment_stages"].append(stage)

            # Calculate best practices score
            score = 0
            recommendations = []

            # Has stages defined (+20)
            if analysis["stages"]:
                score += 20
            else:
                recommendations.append(
                    "Define explicit stages for better pipeline organization"
                )

            # Uses Docker (+15)
            if analysis["uses_docker"]:
                score += 15
            else:
                recommendations.append(
                    "Consider using Docker images for consistent builds"
                )

            # Uses caching (+15)
            if analysis["uses_cache"]:
                score += 15
            else:
                recommendations.append(
                    "Implement caching to speed up pipeline execution"
                )

            # Uses artifacts (+10)
            if analysis["uses_artifacts"]:
                score += 10
            else:
                recommendations.append(
                    "Use artifacts to pass data between pipeline stages"
                )

            # Has security scans (+25)
            if analysis["security_scans"]:
                score += min(25, len(analysis["security_scans"]) * 8)
            else:
                recommendations.append(
                    "Add security scanning (SAST, dependency scanning)"
                )

            # Has deployment stages (+15)
            if analysis["deployment_stages"]:
                score += 15
            else:
                recommendations.append(
                    "Define deployment stages for automated releases"
                )

            # Configuration complexity bonus/malus
            if 50 <= analysis["complexity"] <= 200:
                score += 10  # Good complexity
            elif analysis["complexity"] > 300:
                recommendations.append(
                    "Consider splitting complex CI config into multiple files"
                )
            elif analysis["complexity"] < 20:
                recommendations.append(
                    "CI configuration seems minimal, consider adding more stages"
                )

            analysis["best_practices_score"] = min(100, score)
            analysis["recommendations"] = recommendations

        except yaml.YAMLError as e:
            analysis["syntax_valid"] = False
            analysis["syntax_errors"].append(f"YAML syntax error: {str(e)}")
        except Exception as e:
            analysis["syntax_errors"].append(f"Analysis error: {str(e)}")

        return analysis

    def generate_ci_config_analysis(
        self, ci_config_metrics: List[CIConfigMetrics]
    ) -> CIConfigSystemAnalysis:
        """
        ChatGPT Prompt 4 - analyse_section:
        Compute system-wide CI configuration patterns and best practices adoption.
        """
        console.print("[cyan]🔍 Analyzing CI Configuration KPIs...[/cyan]")

        if not ci_config_metrics:
            return CIConfigSystemAnalysis(
                total_projects=0,
                projects_with_ci_config=0,
                avg_config_complexity=0.0,
                common_patterns={},
                security_adoption={},
                best_practices_summary={},
                problematic_configs=[],
                exemplary_configs=[],
                health_status="No data",
            )

        projects_with_ci = [m for m in ci_config_metrics if m.has_gitlab_ci]
        projects_with_ci_count = len(projects_with_ci)

        # Calculate average complexity
        complexities = [
            m.config_complexity for m in projects_with_ci if m.config_complexity > 0
        ]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0

        # Common patterns analysis
        common_patterns = {
            "docker_usage": len([m for m in projects_with_ci if m.uses_docker]),
            "cache_usage": len([m for m in projects_with_ci if m.uses_cache]),
            "artifacts_usage": len([m for m in projects_with_ci if m.uses_artifacts]),
            "has_stages": len([m for m in projects_with_ci if m.stages_defined]),
        }

        # Security adoption
        all_security_scans = {}
        for metric in projects_with_ci:
            for scan in metric.security_scans:
                all_security_scans[scan] = all_security_scans.get(scan, 0) + 1

        # Best practices summary
        scores = [m.best_practices_score for m in projects_with_ci]
        best_practices_summary = {
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "excellent_configs": len([s for s in scores if s >= 80]),
            "good_configs": len([s for s in scores if 60 <= s < 80]),
            "needs_improvement": len([s for s in scores if s < 60]),
        }

        # Problematic configs (low score or syntax errors)
        problematic_configs = []
        for metric in ci_config_metrics:
            issues = []
            if not metric.syntax_valid:
                issues.extend(metric.syntax_errors)
            if metric.has_gitlab_ci and metric.best_practices_score < 40:
                issues.append(
                    f"Low best practices score ({metric.best_practices_score:.1f})"
                )

            if issues:
                problematic_configs.append(
                    {
                        "repository": metric.path_with_namespace,
                        "score": metric.best_practices_score,
                        "issues": issues,
                    }
                )

        # Exemplary configs (high score)
        exemplary_configs = []
        for metric in projects_with_ci:
            if metric.best_practices_score >= 80:
                exemplary_configs.append(
                    {
                        "repository": metric.path_with_namespace,
                        "score": metric.best_practices_score,
                        "features": [],
                    }
                )

                features = []
                if metric.uses_docker:
                    features.append("Docker")
                if metric.uses_cache:
                    features.append("Caching")
                if metric.security_scans:
                    features.append(f"Security ({', '.join(metric.security_scans)})")
                if metric.deployment_stages:
                    features.append("Deployment")
                exemplary_configs[-1]["features"] = features

        # Sort by score
        exemplary_configs.sort(key=lambda x: x["score"], reverse=True)

        # Health status
        ci_adoption = (
            (projects_with_ci_count / len(ci_config_metrics)) * 100
            if ci_config_metrics
            else 0
        )
        avg_score = best_practices_summary["avg_score"]

        if ci_adoption >= 80 and avg_score >= 70:
            health_status = "🟢 Excellent"
        elif ci_adoption >= 60 and avg_score >= 50:
            health_status = "🟡 Good"
        elif ci_adoption >= 40 or avg_score >= 30:
            health_status = "🟠 Needs Attention"
        else:
            health_status = "🔴 Critical"

        return CIConfigSystemAnalysis(
            total_projects=len(ci_config_metrics),
            projects_with_ci_config=projects_with_ci_count,
            avg_config_complexity=avg_complexity,
            common_patterns=common_patterns,
            security_adoption=all_security_scans,
            best_practices_summary=best_practices_summary,
            problematic_configs=problematic_configs,
            exemplary_configs=exemplary_configs,
            health_status=health_status,
        )

    def generate_markdown_report(
        self, analysis: CIConfigSystemAnalysis, ci_config_metrics: List[CIConfigMetrics]
    ) -> str:
        """Generate comprehensive markdown report for CI Configuration KPIs."""
        report = []

        # Header
        report.append("## ⚙️ GitLab-CI Configuration Check Analysis")
        report.append("")

        # System Overview
        report.append("### System Overview")
        ci_adoption = (
            (analysis.projects_with_ci_config / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )
        report.append(f"- **Total Projects:** {analysis.total_projects}")
        report.append(
            f"- **Projects with CI Config:** {analysis.projects_with_ci_config} ({ci_adoption:.1f}%)"
        )
        report.append(
            f"- **Average Config Complexity:** {analysis.avg_config_complexity:.0f} lines"
        )
        report.append(
            f"- **Average Best Practices Score:** {analysis.best_practices_summary['avg_score']:.1f}/100"
        )
        report.append(f"- **System Health:** {analysis.health_status}")
        report.append("")

        # Configuration Patterns
        report.append("### 📊 Configuration Patterns")
        cp = analysis.common_patterns
        total_with_ci = analysis.projects_with_ci_config
        if total_with_ci > 0:
            report.append(
                f"- **Docker Usage:** {cp.get('docker_usage', 0)} projects ({cp.get('docker_usage', 0)/total_with_ci*100:.1f}%)"
            )
            report.append(
                f"- **Cache Usage:** {cp.get('cache_usage', 0)} projects ({cp.get('cache_usage', 0)/total_with_ci*100:.1f}%)"
            )
            report.append(
                f"- **Artifacts Usage:** {cp.get('artifacts_usage', 0)} projects ({cp.get('artifacts_usage', 0)/total_with_ci*100:.1f}%)"
            )
            report.append(
                f"- **Explicit Stages:** {cp.get('has_stages', 0)} projects ({cp.get('has_stages', 0)/total_with_ci*100:.1f}%)"
            )
        report.append("")

        # Security Adoption
        if analysis.security_adoption:
            report.append("### 🔒 Security Scanning Adoption")
            for scan_type, count in sorted(
                analysis.security_adoption.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total_with_ci * 100) if total_with_ci > 0 else 0
                report.append(
                    f"- **{scan_type.upper()}:** {count} projects ({percentage:.1f}%)"
                )
            report.append("")

        # Best Practices Summary
        bp = analysis.best_practices_summary
        report.append("### 🏆 Best Practices Summary")
        report.append(
            f"- **Excellent Configs (≥80 score):** {bp['excellent_configs']} projects"
        )
        report.append(
            f"- **Good Configs (60-79 score):** {bp['good_configs']} projects"
        )
        report.append(
            f"- **Needs Improvement (<60 score):** {bp['needs_improvement']} projects"
        )
        report.append("")

        # Exemplary Configurations
        if analysis.exemplary_configs:
            report.append("### 🌟 Exemplary Configurations")
            report.append("| Repository | Score | Features |")
            report.append("|------------|-------|----------|")
            for config in analysis.exemplary_configs[:5]:  # Top 5
                features = (
                    ", ".join(config["features"])
                    if config["features"]
                    else "Basic setup"
                )
                report.append(
                    f"| [{config['repository']}]({ci_config_metrics[0].gitlab_url}/{config['repository']}) | {config['score']:.1f} | {features} |"
                )
            report.append("")

        # Problematic Configurations
        if analysis.problematic_configs:
            report.append("### 🚨 Problematic Configurations")
            report.append("| Repository | Score | Issues |")
            report.append("|------------|-------|--------|")
            for config in analysis.problematic_configs:
                issues = "; ".join(
                    config["issues"][:2]
                )  # Limit to avoid very long lines
                if len(config["issues"]) > 2:
                    issues += f" (+{len(config['issues'])-2} more)"
                report.append(
                    f"| [{config['repository']}]({ci_config_metrics[0].gitlab_url}/{config['repository']}) | {config['score']:.1f} | {issues} |"
                )
            report.append("")

        # Repository Details
        report.append("### Repository Configuration Details")
        report.append("")
        report.append(
            "| Repo | CI Config | Jobs | Stages | Docker | Cache | Security | Score | Status |"
        )
        report.append(
            "|------|-----------|------|--------|--------|-------|----------|-------|--------|"
        )

        # Sort by best practices score (descending)
        sorted_metrics = sorted(
            [m for m in ci_config_metrics if m.has_gitlab_ci],
            key=lambda x: x.best_practices_score,
            reverse=True,
        )

        # Add projects without CI at the end
        no_ci_projects = [m for m in ci_config_metrics if not m.has_gitlab_ci]
        sorted_metrics.extend(no_ci_projects)

        for metric in sorted_metrics:
            if metric.has_gitlab_ci:
                ci_status = "✅"
                jobs = str(metric.jobs_count)
                stages = (
                    ", ".join(metric.stages_defined[:3])
                    if metric.stages_defined
                    else "-"
                )
                if len(metric.stages_defined) > 3:
                    stages += f" (+{len(metric.stages_defined)-3})"
                docker = "✅" if metric.uses_docker else "❌"
                cache = "✅" if metric.uses_cache else "❌"
                security = (
                    ", ".join(metric.security_scans[:2])
                    if metric.security_scans
                    else "❌"
                )
                if len(metric.security_scans) > 2:
                    security += f" (+{len(metric.security_scans)-2})"
                score = f"{metric.best_practices_score:.1f}"

                # Status based on score
                if metric.best_practices_score >= 80:
                    status = "🟢 Excellent"
                elif metric.best_practices_score >= 60:
                    status = "🟡 Good"
                elif metric.best_practices_score >= 40:
                    status = "🟠 Needs Work"
                else:
                    status = "🔴 Poor"

            else:
                ci_status = "❌"
                jobs = "-"
                stages = "-"
                docker = "-"
                cache = "-"
                security = "-"
                score = "0"
                status = "⚫ No CI"

            report.append(
                f"| [{metric.path_with_namespace}]({metric.gitlab_url}/{metric.path_with_namespace}) | {ci_status} | {jobs} | {stages} | {docker} | {cache} | {security} | {score} | {status} |"
            )

        return "\n".join(report)

    def display_results_table(self, analysis: CIConfigSystemAnalysis):
        """Display results in a Rich table format."""
        # System Overview Table
        overview_table = Table(
            title="⚙️ GitLab-CI Configuration System Overview", show_header=True
        )
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        ci_adoption = (
            (analysis.projects_with_ci_config / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )

        overview_table.add_row("Total Projects", str(analysis.total_projects))
        overview_table.add_row(
            "Projects with CI Config",
            f"{analysis.projects_with_ci_config} ({ci_adoption:.1f}%)",
        )
        overview_table.add_row(
            "Avg Config Complexity", f"{analysis.avg_config_complexity:.0f} lines"
        )
        overview_table.add_row(
            "Avg Best Practices Score",
            f"{analysis.best_practices_summary['avg_score']:.1f}/100",
        )
        overview_table.add_row("System Health", analysis.health_status)

        console.print(overview_table)
        console.print()

        # Best Practices Summary
        bp_table = Table(title="🏆 Best Practices Distribution", show_header=True)
        bp_table.add_column("Category", style="cyan")
        bp_table.add_column("Count", style="green")
        bp_table.add_column("Percentage", style="yellow")

        bp = analysis.best_practices_summary
        total_with_ci = analysis.projects_with_ci_config

        bp_table.add_row(
            "Excellent (≥80)",
            str(bp["excellent_configs"]),
            (
                f"{bp['excellent_configs']/total_with_ci*100:.1f}%"
                if total_with_ci > 0
                else "0%"
            ),
        )
        bp_table.add_row(
            "Good (60-79)",
            str(bp["good_configs"]),
            (
                f"{bp['good_configs']/total_with_ci*100:.1f}%"
                if total_with_ci > 0
                else "0%"
            ),
        )
        bp_table.add_row(
            "Needs Improvement (<60)",
            str(bp["needs_improvement"]),
            (
                f"{bp['needs_improvement']/total_with_ci*100:.1f}%"
                if total_with_ci > 0
                else "0%"
            ),
        )

        console.print(bp_table)
