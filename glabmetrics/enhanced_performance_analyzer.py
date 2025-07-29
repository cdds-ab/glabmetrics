"""Enhanced Performance Guidelines & Caching Analyzer - ChatGPT Prompt 6 Implementation"""

import concurrent.futures
import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .gitlab_client import GitLabClient

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class PerformanceMetrics:
    """Performance and caching metrics for a single repository."""

    id: int
    path_with_namespace: str

    # CI Performance
    avg_pipeline_duration: float  # minutes
    cache_usage: Dict[str, Any]  # Cache configuration analysis
    dockerfile_optimizations: List[str]  # Optimization suggestions

    # Repository Performance
    repository_size_mb: float
    lfs_usage: Dict[str, Any]  # LFS configuration and usage
    large_files: List[Dict]  # Files >10MB

    # Build Performance
    dependency_caching: Dict[str, Any]  # npm, pip, maven, etc.
    build_tool_configs: List[Dict]  # Build optimization configs found

    # Performance Score
    performance_score: float  # 0-100 based on best practices
    performance_issues: List[str]
    performance_recommendations: List[str]

    gitlab_url: str


@dataclass
class PerformanceSystemAnalysis:
    """System-wide performance analysis results."""

    total_projects: int
    avg_pipeline_duration: float
    projects_using_cache: int
    projects_using_lfs: int
    projects_with_large_files: int
    common_performance_issues: Dict[str, int]
    best_performers: List[Dict]  # Top projects by performance score
    worst_performers: List[Dict]  # Bottom projects needing attention
    optimization_opportunities: Dict[str, int]
    health_status: str


class EnhancedPerformanceAnalyzer:
    """Analyzes performance guidelines and caching according to ChatGPT Prompt 6."""

    def __init__(self, gitlab_client: GitLabClient, max_workers: int = 8):
        self.client = gitlab_client
        self.max_workers = max_workers
        self._lock = threading.Lock()
        self._processed_count = 0

    def collect_performance_kpis(
        self, projects: List[Dict]
    ) -> List[PerformanceMetrics]:
        """
        ChatGPT Prompt 6 - collect_section (Parallelized):
        For each project gather:
        - id, path_with_namespace
        - CI performance: pipeline durations, cache configs
        - Repository size, LFS usage, large files
        - Build configurations: package.json, requirements.txt, pom.xml
        """
        if not projects:
            return []

        console.print(
            f"[cyan]⚡ Collecting Performance & Caching KPIs for {len(projects)} projects "
            f"(using {self.max_workers} workers)...[/cyan]"
        )

        # Reset progress tracking
        self._processed_count = 0
        metrics = []

        # Import graceful shutdown handler
        from .main import shutdown_handler

        # Use progress bar for better UX
        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing projects...", total=len(projects)
            )

            # Process projects in parallel with shutdown detection
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:
                # Submit all projects for processing
                future_to_project = {
                    executor.submit(self._analyze_single_project, project): project
                    for project in projects
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_project):
                    # Check for shutdown request
                    if shutdown_handler.is_shutdown_requested():
                        console.print(
                            "[yellow]⚠️  Shutdown requested during performance analysis[/yellow]"
                        )
                        return metrics  # Return partial results

                    project = future_to_project[future]
                    try:
                        metric = future.result()
                        if metric:
                            metrics.append(metric)

                        # Update progress
                        with self._lock:
                            self._processed_count += 1
                            progress.update(
                                task,
                                advance=1,
                                description=f"[cyan]Processed {self._processed_count}/{len(projects)} projects[/cyan]",
                            )

                    except Exception as e:
                        logger.error(
                            f"Error analyzing performance for {project['path_with_namespace']}: {e}"
                        )
                        # Still update progress for failed projects
                        with self._lock:
                            self._processed_count += 1
                            progress.update(task, advance=1)

        console.print(
            f"[green]✅ Collected Performance KPIs for {len(metrics)} projects[/green]"
        )
        return metrics

    def _analyze_single_project(self, project: Dict) -> PerformanceMetrics:
        """Analyze performance metrics for a single project (thread-safe)."""
        try:
            project_id = project["id"]

            # Get basic project statistics
            repo_size = project.get("statistics", {}).get("repository_size", 0) / (
                1024 * 1024
            )  # MB
            lfs_size = project.get("statistics", {}).get("lfs_objects_size", 0) / (
                1024 * 1024
            )  # MB

            # Analyze CI performance
            ci_analysis = self._analyze_ci_performance(project_id)

            # Analyze repository performance
            repo_analysis = self._analyze_repository_performance(
                project_id, repo_size, lfs_size
            )

            # Analyze build configurations
            build_analysis = self._analyze_build_configurations(project_id)

            # Calculate performance score
            perf_score, issues, recommendations = self._calculate_performance_score(
                ci_analysis, repo_analysis, build_analysis
            )

            return PerformanceMetrics(
                id=project_id,
                path_with_namespace=project["path_with_namespace"],
                avg_pipeline_duration=ci_analysis["avg_duration"],
                cache_usage=ci_analysis["cache_config"],
                dockerfile_optimizations=ci_analysis["dockerfile_optimizations"],
                repository_size_mb=repo_size,
                lfs_usage=repo_analysis["lfs_config"],
                large_files=repo_analysis["large_files"],
                dependency_caching=build_analysis["dependency_caching"],
                build_tool_configs=build_analysis["configs"],
                performance_score=perf_score,
                performance_issues=issues,
                performance_recommendations=recommendations,
                gitlab_url=self.client.gitlab_url,
            )

        except Exception as e:
            logger.error(
                f"Error analyzing performance for {project['path_with_namespace']}: {e}"
            )
            # Return basic metrics instead of None to maintain project count
            return PerformanceMetrics(
                id=project.get("id", 0),
                path_with_namespace=project.get("path_with_namespace", "unknown"),
                avg_pipeline_duration=0.0,
                cache_usage={"enabled": False, "types": [], "efficiency": "unknown"},
                dockerfile_optimizations=[],
                repository_size_mb=project.get("statistics", {}).get(
                    "repository_size", 0
                )
                / (1024 * 1024),
                lfs_usage={"enabled": False, "size_mb": 0.0, "efficiency": "good"},
                large_files=[],
                dependency_caching={
                    "npm": False,
                    "pip": False,
                    "maven": False,
                    "gradle": False,
                },
                build_tool_configs=[],
                performance_score=50.0,  # Neutral score for failed analysis
                performance_issues=[
                    "Analysis failed - unable to collect detailed metrics"
                ],
                performance_recommendations=["Retry analysis with better connectivity"],
                gitlab_url=self.client.gitlab_url,
            )

    def _analyze_ci_performance(self, project_id: int) -> Dict[str, Any]:
        """Analyze CI pipeline performance and caching."""
        analysis = {
            "avg_duration": 0.0,
            "cache_config": {"enabled": False, "types": [], "efficiency": "unknown"},
            "dockerfile_optimizations": [],
        }

        try:
            # Get recent pipelines (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            pipelines = self.client.get_project_pipelines(
                project_id, updated_after=cutoff_date.isoformat()
            )

            # Calculate average duration
            durations = []
            for pipeline in pipelines[:10]:  # Last 10 pipelines
                if pipeline.get("duration"):
                    durations.append(pipeline["duration"] / 60)  # Convert to minutes

            if durations:
                analysis["avg_duration"] = sum(durations) / len(durations)

            # Analyze .gitlab-ci.yml for caching
            try:
                ci_file = self.client.get_repository_file(project_id, ".gitlab-ci.yml")
                if ci_file:
                    import base64

                    ci_content = base64.b64decode(ci_file["content"]).decode("utf-8")
                    cache_analysis = self._analyze_cache_config(ci_content)
                    analysis["cache_config"] = cache_analysis
            except Exception:
                pass

            # Analyze Dockerfile for optimizations
            try:
                dockerfile = self.client.get_repository_file(project_id, "Dockerfile")
                if dockerfile:
                    import base64

                    dockerfile_content = base64.b64decode(dockerfile["content"]).decode(
                        "utf-8"
                    )
                    optimizations = self._analyze_dockerfile_performance(
                        dockerfile_content
                    )
                    analysis["dockerfile_optimizations"] = optimizations
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Error analyzing CI performance: {e}")

        return analysis

    def _analyze_cache_config(self, ci_content: str) -> Dict[str, Any]:
        """Analyze GitLab CI cache configuration."""
        cache_config = {"enabled": False, "types": [], "efficiency": "unknown"}

        try:
            import yaml

            config = yaml.safe_load(ci_content)

            cache_types = []

            # Global cache
            if "cache" in config:
                cache_config["enabled"] = True
                cache_types.append("global")

            # Job-level caches
            for key, value in config.items():
                if isinstance(value, dict) and "cache" in value:
                    cache_config["enabled"] = True

                    cache_def = value["cache"]
                    if isinstance(cache_def, dict):
                        # Analyze cache paths to determine type
                        paths = cache_def.get("paths", [])
                        for path in paths:
                            if "node_modules" in path or "npm" in path:
                                cache_types.append("npm")
                            elif "pip" in path or "__pycache__" in path:
                                cache_types.append("pip")
                            elif "maven" in path or ".m2" in path:
                                cache_types.append("maven")
                            elif "gradle" in path or ".gradle" in path:
                                cache_types.append("gradle")
                            elif "docker" in path:
                                cache_types.append("docker")

            cache_config["types"] = list(set(cache_types))

            # Estimate efficiency based on configuration quality
            if cache_config["enabled"]:
                if len(cache_types) > 1:
                    cache_config["efficiency"] = "good"
                elif cache_types:
                    cache_config["efficiency"] = "basic"
                else:
                    cache_config["efficiency"] = "minimal"

        except Exception as e:
            logger.debug(f"Error analyzing cache config: {e}")

        return cache_config

    def _analyze_dockerfile_performance(self, dockerfile_content: str) -> List[str]:
        """Analyze Dockerfile for performance optimizations."""
        optimizations = []
        lines = dockerfile_content.split("\n")

        # Check for multi-stage builds
        from_count = len(
            [line for line in lines if line.strip().upper().startswith("FROM")]
        )
        if from_count == 1:
            optimizations.append("Consider multi-stage builds to reduce image size")

        # Check for layer optimization
        run_commands = len(
            [line for line in lines if line.strip().upper().startswith("RUN")]
        )
        if run_commands > 5:
            optimizations.append("Consider combining RUN commands to reduce layers")

        # Check for specific optimizations
        dockerfile_lower = dockerfile_content.lower()

        if (
            "apt-get update" in dockerfile_lower
            and "apt-get clean" not in dockerfile_lower
        ):
            optimizations.append("Add apt-get clean after package installation")

        if (
            "pip install" in dockerfile_lower
            and "--no-cache-dir" not in dockerfile_lower
        ):
            optimizations.append("Use pip install --no-cache-dir to reduce image size")

        if (
            "npm install" in dockerfile_lower
            and "npm cache clean" not in dockerfile_lower
        ):
            optimizations.append("Clear npm cache after installation")

        # Check for .dockerignore
        # Note: We would need to check if .dockerignore exists, but skipping for now

        return optimizations

    def _analyze_repository_performance(
        self, project_id: int, repo_size_mb: float, lfs_size_mb: float
    ) -> Dict[str, Any]:
        """Analyze repository size and LFS usage."""
        analysis = {
            "lfs_config": {
                "enabled": lfs_size_mb > 0,
                "size_mb": lfs_size_mb,
                "efficiency": "good",
            },
            "large_files": [],
        }

        # Assess LFS efficiency
        if repo_size_mb > 100:  # Large repository
            if lfs_size_mb == 0:
                analysis["lfs_config"]["efficiency"] = "consider_lfs"
            elif lfs_size_mb < repo_size_mb * 0.1:  # Less than 10% in LFS
                analysis["lfs_config"]["efficiency"] = "underutilized"

        # Note: Getting actual large files would require repository tree analysis
        # which is expensive, so we'll estimate based on size patterns
        if repo_size_mb > 500:
            analysis["large_files"].append(
                {
                    "type": "estimated",
                    "message": "Repository >500MB may contain large files",
                    "recommendation": "Consider using Git LFS for large files",
                }
            )

        return analysis

    def _analyze_build_configurations(self, project_id: int) -> Dict[str, Any]:
        """Analyze build tool configurations for performance optimizations."""
        analysis = {
            "dependency_caching": {
                "npm": False,
                "pip": False,
                "maven": False,
                "gradle": False,
            },
            "configs": [],
        }

        # Check for various build configuration files
        config_files = [
            ("package.json", self._analyze_npm_config),
            ("requirements.txt", self._analyze_pip_config),
            ("pom.xml", self._analyze_maven_config),
            ("build.gradle", self._analyze_gradle_config),
            ("Pipfile", self._analyze_pipenv_config),
        ]

        for filename, analyzer in config_files:
            try:
                file_content = self.client.get_repository_file(project_id, filename)
                if file_content:
                    import base64

                    content = base64.b64decode(file_content["content"]).decode("utf-8")
                    config_analysis = analyzer(content)
                    if config_analysis:
                        analysis["configs"].append(
                            {"file": filename, "analysis": config_analysis}
                        )
            except Exception:
                continue

        return analysis

    def _analyze_npm_config(self, content: str) -> Dict[str, Any]:
        """Analyze package.json for performance optimizations."""
        try:
            config = json.loads(content)
            analysis = {"type": "npm", "optimizations": []}

            # Check for production dependencies separation
            if "devDependencies" in config and "dependencies" in config:
                analysis["optimizations"].append(
                    "Good separation of dev/prod dependencies"
                )

            # Check for scripts that could benefit from caching
            scripts = config.get("scripts", {})
            if "build" in scripts or "test" in scripts:
                analysis["optimizations"].append(
                    "Build/test scripts present - consider CI caching"
                )

            return analysis
        except Exception:
            return None

    def _analyze_pip_config(self, content: str) -> Dict[str, Any]:
        """Analyze requirements.txt for performance optimizations."""
        analysis = {"type": "pip", "optimizations": []}

        lines = content.split("\n")
        pinned_versions = len(
            [
                line
                for line in lines
                if "==" in line and not line.strip().startswith("#")
            ]
        )
        total_deps = len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
        )

        if total_deps > 0:
            pinned_ratio = pinned_versions / total_deps
            if pinned_ratio > 0.8:
                analysis["optimizations"].append(
                    "Good version pinning for reproducible builds"
                )
            else:
                analysis["optimizations"].append(
                    "Consider pinning more dependency versions"
                )

        return analysis

    def _analyze_maven_config(self, content: str) -> Dict[str, Any]:
        """Analyze pom.xml for performance optimizations."""
        analysis = {"type": "maven", "optimizations": []}

        if "<repositories>" in content:
            analysis["optimizations"].append("Custom repositories configured")

        if "<dependencyManagement>" in content:
            analysis["optimizations"].append("Good dependency management structure")

        return analysis

    def _analyze_gradle_config(self, content: str) -> Dict[str, Any]:
        """Analyze build.gradle for performance optimizations."""
        analysis = {"type": "gradle", "optimizations": []}

        if "repositories {" in content:
            analysis["optimizations"].append("Repositories configured")

        if "gradle.projectsEvaluated" in content:
            analysis["optimizations"].append("Advanced Gradle configuration detected")

        return analysis

    def _analyze_pipenv_config(self, content: str) -> Dict[str, Any]:
        """Analyze Pipfile for performance optimizations."""
        analysis = {"type": "pipenv", "optimizations": []}

        if "[dev-packages]" in content:
            analysis["optimizations"].append("Good separation of dev/prod dependencies")

        return analysis

    def _calculate_performance_score(
        self, ci_analysis: Dict, repo_analysis: Dict, build_analysis: Dict
    ) -> tuple:
        """Calculate overall performance score and generate recommendations."""
        score = 0
        issues = []
        recommendations = []

        # CI Performance (40 points)
        if ci_analysis["avg_duration"] > 0:
            if ci_analysis["avg_duration"] < 5:  # < 5 minutes
                score += 20
            elif ci_analysis["avg_duration"] < 15:  # < 15 minutes
                score += 15
            elif ci_analysis["avg_duration"] < 30:  # < 30 minutes
                score += 10
            else:
                issues.append(
                    f"Long pipeline duration ({ci_analysis['avg_duration']:.1f} min)"
                )
                recommendations.append("Optimize pipeline to reduce build time")

        # Cache Usage (20 points)
        if ci_analysis["cache_config"]["enabled"]:
            if ci_analysis["cache_config"]["efficiency"] == "good":
                score += 20
            elif ci_analysis["cache_config"]["efficiency"] == "basic":
                score += 15
            else:
                score += 10
        else:
            issues.append("No CI caching configured")
            recommendations.append("Implement CI caching to speed up builds")

        # Repository Size (20 points)
        if repo_analysis["lfs_config"]["enabled"]:
            score += 15
        elif repo_analysis["lfs_config"]["efficiency"] == "consider_lfs":
            issues.append("Large repository without LFS")
            recommendations.append("Consider using Git LFS for large files")

        if len(repo_analysis["large_files"]) == 0:
            score += 5

        # Build Configuration (20 points)
        if build_analysis["configs"]:
            score += 10
            for config in build_analysis["configs"]:
                if config["analysis"] and config["analysis"].get("optimizations"):
                    score += min(10, len(config["analysis"]["optimizations"]) * 2)
        else:
            recommendations.append(
                "Add build configuration files for dependency management"
            )

        # Ensure score doesn't exceed 100
        score = min(100, score)

        return score, issues, recommendations

    def generate_performance_analysis(
        self, performance_metrics: List[PerformanceMetrics]
    ) -> PerformanceSystemAnalysis:
        """
        ChatGPT Prompt 6 - analyse_section:
        Analyze system-wide performance patterns, caching adoption, and optimization opportunities.
        """
        console.print("[cyan]🔍 Analyzing Performance & Caching KPIs...[/cyan]")

        if not performance_metrics:
            return PerformanceSystemAnalysis(
                total_projects=0,
                avg_pipeline_duration=0.0,
                projects_using_cache=0,
                projects_using_lfs=0,
                projects_with_large_files=0,
                common_performance_issues={},
                best_performers=[],
                worst_performers=[],
                optimization_opportunities={},
                health_status="No data",
            )

        # Calculate system metrics
        durations = [
            m.avg_pipeline_duration
            for m in performance_metrics
            if m.avg_pipeline_duration > 0
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        projects_using_cache = len(
            [m for m in performance_metrics if m.cache_usage["enabled"]]
        )
        projects_using_lfs = len(
            [m for m in performance_metrics if m.lfs_usage["enabled"]]
        )
        projects_with_large_files = len(
            [m for m in performance_metrics if m.large_files]
        )

        # Analyze common performance issues
        issue_counts = {}
        for metric in performance_metrics:
            for issue in metric.performance_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # Find best and worst performers
        sorted_by_score = sorted(
            performance_metrics, key=lambda x: x.performance_score, reverse=True
        )

        best_performers = [
            {
                "repo": m.path_with_namespace,
                "score": m.performance_score,
                "duration": m.avg_pipeline_duration,
                "uses_cache": m.cache_usage["enabled"],
                "uses_lfs": m.lfs_usage["enabled"],
            }
            for m in sorted_by_score[:5]
        ]

        worst_performers = [
            {
                "repo": m.path_with_namespace,
                "score": m.performance_score,
                "issues": len(m.performance_issues),
                "main_issues": m.performance_issues[:2],
            }
            for m in sorted_by_score[-5:]
            if m.performance_score < 60
        ]

        # Optimization opportunities
        optimization_counts = {}
        for metric in performance_metrics:
            for rec in metric.performance_recommendations:
                optimization_counts[rec] = optimization_counts.get(rec, 0) + 1

        # Health status
        avg_score = sum(m.performance_score for m in performance_metrics) / len(
            performance_metrics
        )
        cache_adoption = (projects_using_cache / len(performance_metrics)) * 100

        if avg_score >= 80 and cache_adoption >= 70:
            health_status = "🟢 Excellent"
        elif avg_score >= 60 and cache_adoption >= 50:
            health_status = "🟡 Good"
        elif avg_score >= 40 or cache_adoption >= 30:
            health_status = "🟠 Needs Attention"
        else:
            health_status = "🔴 Critical"

        return PerformanceSystemAnalysis(
            total_projects=len(performance_metrics),
            avg_pipeline_duration=avg_duration,
            projects_using_cache=projects_using_cache,
            projects_using_lfs=projects_using_lfs,
            projects_with_large_files=projects_with_large_files,
            common_performance_issues=issue_counts,
            best_performers=best_performers,
            worst_performers=worst_performers,
            optimization_opportunities=optimization_counts,
            health_status=health_status,
        )

    def generate_markdown_report(
        self,
        analysis: PerformanceSystemAnalysis,
        performance_metrics: List[PerformanceMetrics],
    ) -> str:
        """Generate comprehensive markdown report for Performance & Caching KPIs."""
        report = []

        # Header
        report.append("## ⚡ Performance Guidelines & Caching Analysis")
        report.append("")

        # System Overview
        cache_adoption = (
            (analysis.projects_using_cache / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )
        lfs_adoption = (
            (analysis.projects_using_lfs / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )

        report.append("### System Overview")
        report.append(f"- **Total Projects:** {analysis.total_projects}")
        report.append(
            f"- **Average Pipeline Duration:** {analysis.avg_pipeline_duration:.1f} minutes"
        )
        report.append(
            f"- **Projects Using Cache:** {analysis.projects_using_cache} ({cache_adoption:.1f}%)"
        )
        report.append(
            f"- **Projects Using LFS:** {analysis.projects_using_lfs} ({lfs_adoption:.1f}%)"
        )
        report.append(
            f"- **Projects with Large Files:** {analysis.projects_with_large_files}"
        )
        report.append(f"- **System Health:** {analysis.health_status}")
        report.append("")

        # Performance Champions
        if analysis.best_performers:
            report.append("### 🏆 Performance Champions")
            report.append("| Repository | Score | Duration (min) | Cache | LFS |")
            report.append("|------------|-------|----------------|-------|-----|")
            for perf in analysis.best_performers:
                cache_icon = "✅" if perf["uses_cache"] else "❌"
                lfs_icon = "✅" if perf["uses_lfs"] else "❌"
                report.append(
                    f"| [{perf['repo']}]({performance_metrics[0].gitlab_url}/{perf['repo']}) | {perf['score']:.1f} | {perf['duration']:.1f} | {cache_icon} | {lfs_icon} |"
                )
            report.append("")

        # Performance Issues
        if analysis.worst_performers:
            report.append("### 🚨 Performance Issues")
            report.append("| Repository | Score | Issues | Main Problems |")
            report.append("|------------|-------|--------|---------------|")
            for perf in analysis.worst_performers:
                main_issues = (
                    "; ".join(perf["main_issues"])
                    if perf["main_issues"]
                    else "Multiple issues"
                )
                report.append(
                    f"| [{perf['repo']}]({performance_metrics[0].gitlab_url}/{perf['repo']}) | {perf['score']:.1f} | {perf['issues']} | {main_issues} |"
                )
            report.append("")

        # Common Performance Issues
        if analysis.common_performance_issues:
            report.append("### 📊 Common Performance Issues")
            sorted_issues = sorted(
                analysis.common_performance_issues.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for issue, count in sorted_issues[:5]:
                percentage = (
                    (count / analysis.total_projects * 100)
                    if analysis.total_projects > 0
                    else 0
                )
                report.append(f"- **{issue}:** {count} projects ({percentage:.1f}%)")
            report.append("")

        # Optimization Opportunities
        if analysis.optimization_opportunities:
            report.append("### 💡 Top Optimization Opportunities")
            sorted_opportunities = sorted(
                analysis.optimization_opportunities.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for opportunity, count in sorted_opportunities[:5]:
                percentage = (
                    (count / analysis.total_projects * 100)
                    if analysis.total_projects > 0
                    else 0
                )
                report.append(
                    f"- **{opportunity}:** {count} projects ({percentage:.1f}%)"
                )
            report.append("")

        # Repository Performance Details
        report.append("### Repository Performance Details")
        report.append("")
        report.append(
            "| Repo | Score | Duration (min) | Cache | LFS | Issues | Top Recommendation |"
        )
        report.append(
            "|------|-------|----------------|-------|-----|--------|---------------------|"
        )

        # Sort by performance score (descending)
        sorted_metrics = sorted(
            performance_metrics, key=lambda x: x.performance_score, reverse=True
        )

        for metric in sorted_metrics:
            cache_status = "✅" if metric.cache_usage["enabled"] else "❌"
            lfs_status = "✅" if metric.lfs_usage["enabled"] else "❌"
            issue_count = len(metric.performance_issues)
            top_rec = (
                metric.performance_recommendations[0]
                if metric.performance_recommendations
                else "None"
            )
            if len(top_rec) > 40:
                top_rec = top_rec[:37] + "..."

            report.append(
                f"| [{metric.path_with_namespace}]({metric.gitlab_url}/{metric.path_with_namespace}) | {metric.performance_score:.1f} | {metric.avg_pipeline_duration:.1f} | {cache_status} | {lfs_status} | {issue_count} | {top_rec} |"
            )

        return "\n".join(report)

    def display_results_table(self, analysis: PerformanceSystemAnalysis):
        """Display results in a Rich table format."""
        # System Overview Table
        overview_table = Table(
            title="⚡ Performance & Caching System Overview", show_header=True
        )
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        cache_adoption = (
            (analysis.projects_using_cache / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )
        lfs_adoption = (
            (analysis.projects_using_lfs / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )

        overview_table.add_row("Total Projects", str(analysis.total_projects))
        overview_table.add_row(
            "Avg Pipeline Duration", f"{analysis.avg_pipeline_duration:.1f} min"
        )
        overview_table.add_row(
            "Cache Adoption", f"{analysis.projects_using_cache} ({cache_adoption:.1f}%)"
        )
        overview_table.add_row(
            "LFS Adoption", f"{analysis.projects_using_lfs} ({lfs_adoption:.1f}%)"
        )
        overview_table.add_row(
            "Projects with Large Files", str(analysis.projects_with_large_files)
        )
        overview_table.add_row("System Health", analysis.health_status)

        console.print(overview_table)
        console.print()

        # Best Performers Table
        if analysis.best_performers:
            perf_table = Table(title="🏆 Top Performance Champions", show_header=True)
            perf_table.add_column("Repository", style="cyan")
            perf_table.add_column("Score", style="green")
            perf_table.add_column("Duration", style="yellow")
            perf_table.add_column("Optimizations", style="blue")

            for perf in analysis.best_performers[:5]:
                optimizations = []
                if perf["uses_cache"]:
                    optimizations.append("Cache")
                if perf["uses_lfs"]:
                    optimizations.append("LFS")
                opt_str = ", ".join(optimizations) if optimizations else "Basic"

                perf_table.add_row(
                    perf["repo"],
                    f"{perf['score']:.1f}",
                    f"{perf['duration']:.1f}min",
                    opt_str,
                )

            console.print(perf_table)
