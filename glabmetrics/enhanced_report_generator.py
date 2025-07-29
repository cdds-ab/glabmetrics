"""Enhanced HTML Report Generator with Single-Page Tab Dashboard"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .dashboard.actionable_dashboard import ActionableDashboard
from .dashboard.comprehensive_dashboard import ComprehensiveDashboard
from .performance_analyzer import (
    PerformanceAnalyzer,
    create_performance_dashboard_content,
)


def get_attr_safe(obj, attr_name, default=None):
    """Safely get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(attr_name, default)
    else:
        return getattr(obj, attr_name, default)


@dataclass
class CriticalIssue:
    """Represents a critical issue found in the analysis."""

    title: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    affected_repos: List[str]
    recommendation: str
    source: str  # Which analysis generated this (P1-P6)
    priority: int  # 1=highest, 5=lowest


@dataclass
class BestPractice:
    """Represents a best practice recommendation."""

    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    effort: str  # 'high', 'medium', 'low'
    repositories: List[str]
    implementation_steps: List[str]


class EnhancedHTMLReportGenerator:
    """Generate enhanced single-page HTML dashboard with tabs for all 6 ChatGPT prompts."""

    def __init__(self, gitlab_url: str = ""):
        self.gitlab_url = gitlab_url

    def _safe_get(self, data, key, default=0):
        """Safely get value from dict or object attribute."""
        if isinstance(data, dict):
            return data.get(key, default)
        else:
            return getattr(data, key, default)

    def _analyze_critical_issues(
        self, repositories: List[Any], enhanced_analysis: Dict[str, Any]
    ) -> List[CriticalIssue]:
        """Analyze all data sources and extract critical issues prioritized by severity."""
        issues = []

        # P1: Issue Analysis - Critical Issues
        issue_analysis = enhanced_analysis.get("issue_analysis", {})
        if (
            hasattr(issue_analysis, "red_projects_count")
            and get_attr_safe(issue_analysis, "red_projects_count", 0) > 0
        ):
            issue_metrics = enhanced_analysis.get("issue_metrics", [])
            critical_repos = [
                m.path_with_namespace
                for m in issue_metrics
                if hasattr(m, "alert_level") and m.alert_level == "red"
            ]
            issues.append(
                CriticalIssue(
                    title="🚨 Critical Issue Backlog Crisis",
                    description=f"CRITICAL: {get_attr_safe(issue_analysis, 'red_projects_count', 0)} repositories have issue backlogs >30 days blocking development",
                    severity="critical",
                    affected_repos=critical_repos,
                    recommendation=f"# WEEK 1: Emergency issue triage\n"
                    f"# Schedule 2-hour sessions for {critical_repos[0] if critical_repos else 'affected repos'}\n"
                    f"# Close stale issues >90 days, label by priority\n"
                    f"# Expected result: 60% reduction in open issues",
                    source="P1: Issues",
                    priority=1,
                )
            )

        # P2: MR Analysis - Long Lead Times
        mr_analysis = enhanced_analysis.get("mr_analysis", {})
        if hasattr(mr_analysis, "flagged_repositories") and get_attr_safe(
            mr_analysis, "flagged_repositories", []
        ):
            flagged_repos = [
                repo["repository"]
                for repo in get_attr_safe(mr_analysis, "flagged_repositories", [])
            ]
            issues.append(
                CriticalIssue(
                    title="⏰ Merge Request Bottlenecks",
                    description=f"HIGH: {len(flagged_repos)} repositories have MR lead times >5 days, reducing development velocity by 40%",
                    severity="warning",
                    affected_repos=flagged_repos,
                    recommendation="# WEEK 1: Implement MR automation\n"
                    "# Add auto-merge for approved MRs: enable_auto_merge = true\n"
                    "# Configure reviewer assignment rules in project settings\n"
                    "# Expected result: 50% reduction in lead time",
                    source="P2: Code Review",
                    priority=2,
                )
            )

        # P3: CI/CD Issues
        ci_analysis = enhanced_analysis.get("ci_analysis", {})
        if (
            hasattr(ci_analysis, "system_success_rate")
            and get_attr_safe(ci_analysis, "system_success_rate", 100) < 85
        ):
            problematic_repos = []
            if hasattr(ci_analysis, "problematic_projects"):
                problematic_repos = [
                    p["repository"]
                    for p in get_attr_safe(ci_analysis, "problematic_projects", [])
                ]
            issues.append(
                CriticalIssue(
                    title="🔧 CI/CD Pipeline Failures",
                    description=f"CRITICAL: System CI success rate {get_attr_safe(ci_analysis, 'system_success_rate', 100):.1f}% indicates broken deployment process",
                    severity=(
                        "critical"
                        if get_attr_safe(ci_analysis, "system_success_rate", 100) < 70
                        else "warning"
                    ),
                    affected_repos=problematic_repos,
                    recommendation="# WEEK 1: Fix top 3 failing pipelines\n"
                    "# Check GitLab CI lint: https://gitlab.com/ci/lint\n"
                    "# Add pipeline debugging: CI_DEBUG_TRACE=true\n"
                    "# Expected result: >90% success rate",
                    source="P3: CI/CD",
                    priority=(
                        1
                        if get_attr_safe(ci_analysis, "system_success_rate", 100) < 70
                        else 3
                    ),
                )
            )

        # P4: Configuration Issues
        ci_config_analysis = enhanced_analysis.get("ci_config_analysis", {})
        if hasattr(ci_config_analysis, "best_practices_summary"):
            avg_score = get_attr_safe(
                ci_config_analysis, "best_practices_summary", {}
            ).get("avg_score", 100)
            if avg_score < 60:
                problematic_configs = []
                if hasattr(ci_config_analysis, "problematic_configs"):
                    problematic_configs = [
                        c["repository"]
                        for c in get_attr_safe(
                            ci_config_analysis, "problematic_configs", []
                        )
                    ]
                issues.append(
                    CriticalIssue(
                        title="Poor CI Configuration Quality",
                        description=f"Average CI configuration score is only {avg_score:.1f}/100",
                        severity="critical" if avg_score < 40 else "warning",
                        affected_repos=problematic_configs,
                        recommendation="Implement CI/CD best practices: caching, security scans, and pipeline optimization.",
                        source="P4: Configuration",
                        priority=2,
                    )
                )

        # P6: Performance Issues
        performance_analysis = enhanced_analysis.get("performance_analysis", {})
        if hasattr(performance_analysis, "worst_performers") and get_attr_safe(
            performance_analysis, "worst_performers", []
        ):
            slow_repos = [
                p["repo"]
                for p in get_attr_safe(performance_analysis, "worst_performers", [])
            ]
            issues.append(
                CriticalIssue(
                    title="Performance Optimization Needed",
                    description=f"{len(slow_repos)} repositories need performance optimization",
                    severity="warning",
                    affected_repos=slow_repos,
                    recommendation="Implement caching, optimize large files, and use Git LFS for binary assets.",
                    source="P6: Performance",
                    priority=3,
                )
            )

        # CRITICAL: Binary Files Performance Killer (Repository Analysis)
        binary_killers = []
        storage_waste = []

        for repo in repositories:
            size_mb = getattr(repo, "size_mb", 0)
            binary_count = getattr(repo, "binary_file_count", 0)
            days_inactive = getattr(repo, "days_since_last_activity", 0)
            repo_name = getattr(repo, "path_with_namespace", "unknown")

            # Performance killers: >500 binary files OR >1GB with binaries
            if binary_count > 500 or (size_mb > 1000 and binary_count > 50):
                binary_killers.append(
                    {
                        "name": repo_name,
                        "size_gb": size_mb / 1024,
                        "binary_count": binary_count,
                    }
                )

            # Storage waste: inactive >2 years or delete-marked
            if (
                days_inactive > 730
                or "_delete_" in repo_name.lower()
                or "obsolete" in repo_name.lower()
            ):
                storage_waste.append(
                    {
                        "name": repo_name,
                        "size_gb": size_mb / 1024,
                        "days_inactive": days_inactive,
                    }
                )

        # Add binary performance issue
        if binary_killers:
            top_offender = max(
                binary_killers, key=lambda x: x["binary_count"] * x["size_gb"]
            )
            issues.append(
                CriticalIssue(
                    title="🚨 Binary Files Killing GitLab Performance",
                    description=f"CRITICAL: {len(binary_killers)} repositories with massive binary files cause web UI timeouts. "
                    f"Worst: {top_offender['name']} ({top_offender['binary_count']:,} binaries, {top_offender['size_gb']:.1f}GB)",
                    severity="critical",
                    affected_repos=[repo["name"] for repo in binary_killers[:3]],
                    recommendation=f"# IMMEDIATE: Migrate to Git LFS\n"
                    f"cd {top_offender['name']} && git lfs migrate import --include='*.jpg,*.png,*.pdf,*.exe,*.bin'\n"
                    f"# Expected result: 70-90% size reduction, web UI loads in <5s\n"
                    f"# Performance impact: Web browsing from timeout to normal",
                    source="Repository Analysis",
                    priority=0,  # Highest priority
                )
            )

        # Add storage waste issue
        if len(storage_waste) > 100:
            total_waste_gb = sum(repo["size_gb"] for repo in storage_waste)
            issues.append(
                CriticalIssue(
                    title="📦 Repository Sprawl Wasting Resources",
                    description=f"HIGH: {len(storage_waste)} inactive/obsolete repositories waste {total_waste_gb:.1f}GB and slow maintenance by 60%",
                    severity="high",
                    affected_repos=[repo["name"] for repo in storage_waste[:5]],
                    recommendation=f"# WEEK 1: Archive {len([r for r in storage_waste if '_delete_' in r['name']])} pre-marked repos\n"
                    f"# gitlab-rails console: Project.where('path LIKE ?', '%_delete_%').find_each(&:archive!)\n"
                    f"# WEEK 2: Archive {len([r for r in storage_waste if r['days_inactive'] > 730])} stale repos\n"
                    f"# Expected result: {total_waste_gb:.1f}GB saved, 40-60% less maintenance overhead",
                    source="Repository Analysis",
                    priority=1,
                )
            )

        # Active repos without CI/CD
        active_no_ci = []
        for repo in repositories:
            days_inactive = getattr(repo, "days_since_last_activity", 999)
            pipeline_count = getattr(repo, "pipeline_count", 0)
            repo_name = getattr(repo, "path_with_namespace", "unknown")

            if days_inactive < 90 and pipeline_count == 0:
                active_no_ci.append(repo_name)

        if len(active_no_ci) > 15:
            issues.append(
                CriticalIssue(
                    title="🔧 Active Development Without CI/CD",
                    description=f"MEDIUM: {len(active_no_ci)} active repositories lack automation, increasing bug risk by 300%",
                    severity="warning",
                    affected_repos=active_no_ci[:5],
                    recommendation="# WEEK 1: Deploy CI templates for top 5 active repos\n"
                    "# Create .gitlab-ci.yml: stages: [test, build, deploy]\n"
                    "# Enable merge request pipelines in project settings\n"
                    "# Expected result: 50% reduction in production bugs",
                    source="Repository Analysis",
                    priority=2,
                )
            )

        # Sort by priority (0=highest priority)
        return sorted(issues, key=lambda x: x.priority)

    def _generate_best_practices(
        self, repositories: List[Any], enhanced_analysis: Dict[str, Any]
    ) -> List[BestPractice]:
        """Generate actionable best practice recommendations."""
        practices = []

        # CI/CD Best Practices
        ci_config_analysis = enhanced_analysis.get("ci_config_analysis", {})
        if hasattr(ci_config_analysis, "projects_with_ci_config"):
            total_projects = len(repositories)
            ci_coverage = (
                get_attr_safe(ci_config_analysis, "projects_with_ci_config", 0)
                / total_projects
                if total_projects > 0
                else 0
            )

            if ci_coverage < 0.8:  # Less than 80% CI coverage
                repos_without_ci = [
                    r.path_with_namespace for r in repositories[:5]
                ]  # Example repos
                practices.append(
                    BestPractice(
                        title="🚀 Complete CI/CD Coverage",
                        description=f"Only {ci_coverage*100:.1f}% of repositories have CI/CD - massive development efficiency gap",
                        impact="high",
                        effort="medium",
                        repositories=repos_without_ci,
                        implementation_steps=[
                            f"# WEEK 1: Create .gitlab-ci.yml template for {repos_without_ci[0] if repos_without_ci else 'primary repo'}",
                            "# Template: stages: [test, build, deploy] with Docker caching",
                            "# WEEK 2: Roll out to top 10 active repositories",
                            "# Expected impact: 3x faster deployment, 50% fewer bugs",
                            f"# Success metric: Achieve 90% CI coverage ({100-ci_coverage*100:.0f}% improvement)",
                        ],
                    )
                )

        # Performance Best Practices
        performance_analysis = enhanced_analysis.get("performance_analysis", {})
        if hasattr(performance_analysis, "projects_using_cache"):
            total_with_ci = (
                get_attr_safe(ci_config_analysis, "projects_with_ci_config", 1)
                if hasattr(ci_config_analysis, "projects_with_ci_config")
                else 1
            )
            cache_usage = (
                get_attr_safe(performance_analysis, "projects_using_cache", 0)
                / total_with_ci
                if total_with_ci > 0
                else 0
            )

            if cache_usage < 0.5:  # Less than 50% using caching
                practices.append(
                    BestPractice(
                        title="⚡ Pipeline Caching for 5x Speed",
                        description=f"Only {get_attr_safe(performance_analysis, 'projects_using_cache', 0)}/{total_with_ci} CI projects use caching - massive speed opportunity",
                        impact="high",
                        effort="low",
                        repositories=[],
                        implementation_steps=[
                            "# WEEK 1: Add caching to top 5 slowest pipelines",
                            "# Add to .gitlab-ci.yml: cache: paths: [node_modules/, .m2/repository/]",
                            "# Enable Docker layer caching: DOCKER_DRIVER=overlay2",
                            "# Expected result: 3-5x faster builds, 80% less CI resource usage",
                            f"# Target: Implement caching in {total_with_ci - get_attr_safe(performance_analysis, 'projects_using_cache', 0)} remaining projects",
                        ],
                    )
                )

        # Issue Management Best Practices
        issue_analysis = enhanced_analysis.get("issue_analysis", {})
        if (
            hasattr(issue_analysis, "system_avg_age_days")
            and get_attr_safe(issue_analysis, "system_avg_age_days", 0) > 20
        ):
            practices.append(
                BestPractice(
                    title="Implement Issue Triage Process",
                    description=f"Average issue age is {get_attr_safe(issue_analysis, 'system_avg_age_days', 0):.1f} days - too long for healthy development",
                    impact="medium",
                    effort="low",
                    repositories=[],
                    implementation_steps=[
                        "Weekly issue triage meetings",
                        "Label issues by priority and complexity",
                        "Set SLA targets for issue resolution",
                        "Automate stale issue management",
                    ],
                )
            )

        return practices

    def _calculate_repository_metrics(self, repositories: List[Any]) -> Dict[str, Any]:
        """Calculate traditional repository metrics from the repositories data."""
        if not repositories:
            return self._get_empty_metrics()

        total_repos = len(repositories)
        total_size_gb = sum(getattr(repo, "size_mb", 0) for repo in repositories) / 1024
        total_commits = sum(getattr(repo, "commit_count", 0) for repo in repositories)
        total_contributors = sum(
            getattr(repo, "contributor_count", 0) for repo in repositories
        )

        # Storage breakdown
        total_lfs_size_gb = (
            sum(getattr(repo, "lfs_size_mb", 0) for repo in repositories) / 1024
        )
        total_artifacts_size_gb = (
            sum(getattr(repo, "artifacts_size_mb", 0) for repo in repositories) / 1024
        )
        total_packages_size_gb = (
            sum(getattr(repo, "packages_size_mb", 0) for repo in repositories) / 1024
        )
        total_container_size_gb = (
            sum(getattr(repo, "container_registry_size_mb", 0) for repo in repositories)
            / 1024
        )

        # Activity metrics
        orphaned_count = sum(
            1 for repo in repositories if getattr(repo, "is_orphaned", False)
        )

        # Pipeline metrics
        repos_with_pipelines = sum(
            1 for repo in repositories if getattr(repo, "pipeline_count", 0) > 0
        )
        total_pipelines = sum(
            getattr(repo, "pipeline_count", 0) for repo in repositories
        )
        avg_pipeline_success = (
            sum(getattr(repo, "pipeline_success_rate", 0) for repo in repositories)
            / total_repos
            if total_repos > 0
            else 0
        )

        return {
            "total_repositories": total_repos,
            "total_size_gb": round(total_size_gb, 2),
            "total_commits": total_commits,
            "total_contributors": total_contributors,
            "total_lfs_size_gb": round(total_lfs_size_gb, 2),
            "total_artifacts_size_gb": round(total_artifacts_size_gb, 2),
            "total_packages_size_gb": round(total_packages_size_gb, 2),
            "total_container_size_gb": round(total_container_size_gb, 2),
            "orphaned_repositories": orphaned_count,
            "repositories_with_pipelines": repos_with_pipelines,
            "total_pipelines": total_pipelines,
            "avg_pipeline_success_rate": round(avg_pipeline_success, 1),
            "storage_breakdown": {
                "Repository Data": round(total_size_gb - total_lfs_size_gb, 2),
                "Git LFS Objects": round(total_lfs_size_gb, 2),
                "CI/CD Artifacts": round(total_artifacts_size_gb, 2),
                "Packages": round(total_packages_size_gb, 2),
                "Container Registry": round(total_container_size_gb, 2),
            },
        }

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "total_repositories": 0,
            "total_size_gb": 0.0,
            "total_commits": 0,
            "total_contributors": 0,
            "total_lfs_size_gb": 0.0,
            "total_artifacts_size_gb": 0.0,
            "total_packages_size_gb": 0.0,
            "total_container_size_gb": 0.0,
            "orphaned_repositories": 0,
            "repositories_with_pipelines": 0,
            "total_pipelines": 0,
            "avg_pipeline_success_rate": 0.0,
            "storage_breakdown": {},
        }

    def generate_enhanced_dashboard(
        self,
        repositories: List[Any],
        enhanced_analysis: Optional[Dict[str, Any]] = None,
        performance_stats: Optional[Any] = None,
        output_file: str = "enhanced_dashboard.html",
        enhanced_kpis_requested: bool = False,
    ) -> str:
        """Generate the complete enhanced dashboard."""

        if enhanced_analysis is None:
            # Fallback for basic analysis only when explicitly None
            return self._generate_basic_dashboard(
                repositories, output_file, enhanced_kpis_requested
            )

        # Generate the enhanced dashboard with all 6 prompts
        html_content = self._build_enhanced_html(
            repositories, enhanced_analysis, performance_stats
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def _build_enhanced_html(
        self,
        repositories: List[Any],
        enhanced_analysis: Dict[str, Any],
        performance_stats: Any,
    ) -> str:
        """Build the complete enhanced HTML dashboard."""

        # Store repositories and enhanced_analysis for use in tabs
        # Always convert to dicts for consistent dashboard compatibility
        self._repositories = self._convert_repositories_to_dicts(repositories)
        self.enhanced_analysis = enhanced_analysis

        # Extract analysis results
        issue_analysis = enhanced_analysis.get("issue_analysis", {})
        mr_analysis = enhanced_analysis.get("mr_analysis", {})
        ci_analysis = enhanced_analysis.get("ci_analysis", {})
        ci_config_analysis = enhanced_analysis.get("ci_config_analysis", {})
        submodule_analysis = enhanced_analysis.get("submodule_analysis", {})
        performance_analysis = enhanced_analysis.get("performance_analysis", {})

        # Extract metrics
        issue_metrics = enhanced_analysis.get("issue_metrics", [])
        mr_metrics = enhanced_analysis.get("mr_metrics", [])
        ci_metrics = enhanced_analysis.get("ci_metrics", [])
        ci_config_metrics = enhanced_analysis.get("ci_config_metrics", [])
        submodule_metrics = enhanced_analysis.get("submodule_metrics", [])
        performance_metrics = enhanced_analysis.get("performance_metrics", [])

        # Analyze critical issues and best practices
        critical_issues = self._analyze_critical_issues(repositories, enhanced_analysis)
        best_practices = self._generate_best_practices(repositories, enhanced_analysis)
        repository_metrics = self._calculate_repository_metrics(repositories)

        # Pass these to the executive dashboard
        self._current_critical_issues = critical_issues
        self._current_best_practices = best_practices
        self._current_repository_metrics = repository_metrics

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Enhanced GitLab Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        {self._get_enhanced_css()}
    </style>
</head>
<body>
    <!-- Header -->
    <nav class="navbar navbar-dark bg-primary shadow-sm">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-chart-line me-2"></i>
                🎯 Enhanced GitLab Analytics Dashboard
            </span>
            <div class="d-flex align-items-center text-white">
                <small class="me-3">
                    <i class="fas fa-clock me-1"></i>
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </small>
                <div class="input-group" style="width: 250px;">
                    <input type="text" id="globalSearch" class="form-control form-control-sm"
                           placeholder="🔍 Search repositories...">
                </div>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <!-- Alert Center -->
        {self._generate_alert_center(issue_analysis, mr_analysis, ci_analysis, ci_config_analysis, submodule_analysis, performance_analysis)}

        <!-- System Health Overview -->
        {self._generate_health_overview(issue_analysis, mr_analysis, ci_analysis, ci_config_analysis, submodule_analysis, performance_analysis)}

        <!-- Main Tab Navigation -->
        <div class="row mt-4">
            <div class="col">
                <ul class="nav nav-tabs nav-fill" id="mainTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="dashboard-tab" data-bs-toggle="tab"
                                data-bs-target="#dashboard" type="button" role="tab">
                            <i class="fas fa-tachometer-alt me-2"></i>📊 Executive Dashboard
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="issues-tab" data-bs-toggle="tab"
                                data-bs-target="#issues" type="button" role="tab">
                            <i class="fas fa-exclamation-triangle me-2"></i>📋 Issues (P1)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="mr-tab" data-bs-toggle="tab"
                                data-bs-target="#mr" type="button" role="tab">
                            <i class="fas fa-code-branch me-2"></i>🔄 Code Review (P2)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="ci-tab" data-bs-toggle="tab"
                                data-bs-target="#ci" type="button" role="tab">
                            <i class="fas fa-cogs me-2"></i>🏗️ CI/CD (P3)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="config-tab" data-bs-toggle="tab"
                                data-bs-target="#config" type="button" role="tab">
                            <i class="fas fa-file-code me-2"></i>⚙️ Config (P4)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="network-tab" data-bs-toggle="tab"
                                data-bs-target="#network" type="button" role="tab">
                            <i class="fas fa-project-diagram me-2"></i>🔗 Network (P5)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="performance-tab" data-bs-toggle="tab"
                                data-bs-target="#performance" type="button" role="tab">
                            <i class="fas fa-rocket me-2"></i>⚡ Performance (P6)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="actionable-tab" data-bs-toggle="tab"
                                data-bs-target="#actionable" type="button" role="tab">
                            <i class="fas fa-tasks me-2"></i>🎯 Actions (A1)
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="comprehensive-tab" data-bs-toggle="tab"
                                data-bs-target="#comprehensive" type="button" role="tab">
                            <i class="fas fa-chart-line me-2"></i>📊 Comprehensive (C1)
                        </button>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Tab Content -->
        <div class="tab-content mt-3" id="mainTabContent">
            <!-- Executive Dashboard Tab -->
            <div class="tab-pane fade show active" id="dashboard" role="tabpanel">
                {self._generate_executive_dashboard(repositories, enhanced_analysis, performance_stats)}
            </div>

            <!-- Issues Tab (P1) -->
            <div class="tab-pane fade" id="issues" role="tabpanel">
                {self._generate_issues_tab(issue_analysis, issue_metrics)}
            </div>

            <!-- Code Review Tab (P2) -->
            <div class="tab-pane fade" id="mr" role="tabpanel">
                {self._generate_mr_tab(mr_analysis, mr_metrics)}
            </div>

            <!-- CI/CD Tab (P3) -->
            <div class="tab-pane fade" id="ci" role="tabpanel">
                {self._generate_ci_tab(ci_analysis, ci_metrics)}
            </div>

            <!-- Configuration Tab (P4) -->
            <div class="tab-pane fade" id="config" role="tabpanel">
                {self._generate_config_tab(ci_config_analysis, ci_config_metrics)}
            </div>

            <!-- Network Tab (P5) -->
            <div class="tab-pane fade" id="network" role="tabpanel">
                {self._generate_network_tab(submodule_analysis, submodule_metrics)}
            </div>

            <!-- Performance Tab (P6) -->
            <div class="tab-pane fade" id="performance" role="tabpanel">
                {self._generate_performance_tab(performance_analysis, performance_metrics)}
            </div>

            <!-- Actionable Dashboard Tab (A1) -->
            <div class="tab-pane fade" id="actionable" role="tabpanel">
                {self._generate_actionable_tab()}
            </div>

            <!-- Comprehensive Dashboard Tab (C1) -->
            <div class="tab-pane fade" id="comprehensive" role="tabpanel">
                {self._generate_comprehensive_tab()}
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        {self._get_enhanced_javascript()}
    </script>
</body>
</html>
        """

        return html_template

    def _get_enhanced_css(self) -> str:
        """Enhanced CSS for the dashboard."""
        return """
        :root {
            --primary-color: #0d6efd;
            --success-color: #198754;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #0dcaf0;
            --dark-color: #212529;
        }

        body {
            background-color: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .health-card {
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .health-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }

        .health-card.excellent { border-left: 5px solid var(--success-color); }
        .health-card.good { border-left: 5px solid var(--info-color); }
        .health-card.warning { border-left: 5px solid var(--warning-color); }
        .health-card.critical { border-left: 5px solid var(--danger-color); }

        .metric-number {
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1;
        }

        .metric-label {
            font-size: 0.875rem;
            color: #6c757d;
            font-weight: 500;
        }

        .alert-center {
            background: linear-gradient(135deg, #ff6b6b, #ffa726);
            color: white;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(255,107,107,0.3);
        }

        .nav-tabs .nav-link {
            border: none;
            border-radius: 8px 8px 0 0;
            color: #495057;
            font-weight: 500;
            padding: 12px 20px;
            margin-right: 2px;
        }

        .nav-tabs .nav-link.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }

        .nav-tabs .nav-link:hover:not(.active) {
            background-color: #e9ecef;
            border-color: transparent;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }

        .data-table {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        .data-table th {
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
            border: none;
            padding: 12px;
        }

        .data-table td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }

        .data-table tbody tr:hover {
            background-color: #f8f9fa;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .filter-section {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        @media (max-width: 768px) {
            .nav-tabs {
                flex-direction: column;
            }

            .nav-tabs .nav-link {
                text-align: center;
                margin-bottom: 2px;
                margin-right: 0;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .metric-number {
                font-size: 2rem;
            }
        }

        .loading-spinner {
            display: none;
            text-align: center;
            padding: 40px;
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        """

    def _generate_alert_center(
        self,
        issue_analysis,
        mr_analysis,
        ci_analysis,
        ci_config_analysis,
        submodule_analysis,
        performance_analysis,
    ) -> str:
        """Generate the alert center section."""
        alerts = []

        # Collect alerts from all analyses
        if (
            hasattr(issue_analysis, "red_projects_count")
            and get_attr_safe(issue_analysis, "red_projects_count", 0) > 0
        ):
            alerts.append(
                f"🔴 {get_attr_safe(issue_analysis, 'red_projects_count', 0)} projects with critical issue backlogs"
            )

        if (
            hasattr(mr_analysis, "flagged_repositories")
            and len(get_attr_safe(mr_analysis, "flagged_repositories", [])) > 0
        ):
            alerts.append(
                f"🟡 {len(get_attr_safe(mr_analysis, 'flagged_repositories', []))} projects with long MR lead times"
            )

        if (
            hasattr(ci_analysis, "problematic_projects")
            and len(get_attr_safe(ci_analysis, "problematic_projects", [])) > 0
        ):
            alerts.append(
                f"🟠 {len(get_attr_safe(ci_analysis, 'problematic_projects', []))} projects with CI/CD issues"
            )

        if (
            hasattr(ci_config_analysis, "problematic_configs")
            and len(get_attr_safe(ci_config_analysis, "problematic_configs", [])) > 0
        ):
            alerts.append(
                f"⚙️ {len(get_attr_safe(ci_config_analysis, 'problematic_configs', []))} projects with config problems"
            )

        if (
            hasattr(submodule_analysis, "circular_dependencies")
            and len(get_attr_safe(submodule_analysis, "circular_dependencies", [])) > 0
        ):
            alerts.append(
                f"🔄 {len(get_attr_safe(submodule_analysis, 'circular_dependencies', []))} circular dependencies detected"
            )

        if (
            hasattr(performance_analysis, "worst_performers")
            and len(get_attr_safe(performance_analysis, "worst_performers", [])) > 0
        ):
            alerts.append(
                f"⚡ {len(get_attr_safe(performance_analysis, 'worst_performers', []))} projects need performance optimization"
            )

        if not alerts:
            alerts = ["🟢 No critical alerts - System is healthy!"]

        alerts_html = ""
        for alert in alerts[:5]:  # Show max 5 alerts
            alerts_html += (
                f'<span class="badge bg-warning text-dark me-2 mb-1">{alert}</span>'
            )

        return f"""
        <div class="alert-center p-3 mb-3">
            <div class="d-flex align-items-center justify-content-between">
                <div>
                    <h5 class="mb-1"><i class="fas fa-exclamation-triangle me-2"></i>Alert Center</h5>
                    <div>{alerts_html}</div>
                </div>
                <div class="text-end">
                    <div class="fs-2 fw-bold">{len([a for a in alerts if not a.startswith('🟢')])}</div>
                    <small>Active Alerts</small>
                </div>
            </div>
        </div>
        """

    def _generate_health_overview(
        self,
        issue_analysis,
        mr_analysis,
        ci_analysis,
        ci_config_analysis,
        submodule_analysis,
        performance_analysis,
    ) -> str:
        """Generate the system health overview cards."""

        def get_health_data(analysis, name, icon):
            if hasattr(analysis, "health_status"):
                status = analysis.health_status
                if "Excellent" in status:
                    return {"status": status, "class": "excellent", "score": 100}
                elif "Good" in status:
                    return {"status": status, "class": "good", "score": 80}
                elif "Attention" in status:
                    return {"status": status, "class": "warning", "score": 60}
                else:
                    return {"status": status, "class": "critical", "score": 40}
            return {"status": "No Data", "class": "critical", "score": 0}

        analyses = [
            (issue_analysis, "P1: Issues", "fas fa-exclamation-triangle"),
            (mr_analysis, "P2: Code Review", "fas fa-code-branch"),
            (ci_analysis, "P3: CI/CD", "fas fa-cogs"),
            (ci_config_analysis, "P4: Configuration", "fas fa-file-code"),
            (submodule_analysis, "P5: Network", "fas fa-project-diagram"),
            (performance_analysis, "P6: Performance", "fas fa-rocket"),
        ]

        cards_html = ""
        for analysis, name, icon in analyses:
            health_data = get_health_data(analysis, name, icon)
            cards_html += f"""
            <div class="col-md-2 col-sm-6 mb-3">
                <div class="card health-card {health_data['class']} h-100" onclick="switchToTab('{name.split(':')[0].lower()}')">
                    <div class="card-body text-center">
                        <i class="{icon} fa-2x mb-2 text-primary"></i>
                        <h6 class="card-title">{name}</h6>
                        <div class="metric-number">{health_data['score']}</div>
                        <div class="metric-label">{health_data['status']}</div>
                    </div>
                </div>
            </div>
            """

        return f"""
        <div class="row">
            {cards_html}
        </div>
        """

    def _generate_executive_dashboard(
        self, repositories, enhanced_analysis, performance_stats
    ) -> str:
        """Generate the executive dashboard tab content with critical issues and repository metrics."""

        # Get the analyzed data
        critical_issues = getattr(self, "_current_critical_issues", [])
        best_practices = getattr(self, "_current_best_practices", [])
        repository_metrics = getattr(self, "_current_repository_metrics", {})

        return f"""
        <!-- Critical Issues Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-danger text-white">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>🚨 Critical Issues & Action Items</h5>
                    </div>
                    <div class="card-body">
                        {self._generate_critical_issues_html(critical_issues)}
                    </div>
                </div>
            </div>
        </div>

        <!-- System Overview -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie me-2"></i>Storage Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="storageChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="stats-grid">
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="metric-number text-primary">{repository_metrics.get('total_repositories', 0)}</div>
                            <div class="metric-label">Total Repositories</div>
                        </div>
                    </div>
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="metric-number text-info">{repository_metrics.get('total_size_gb', 0):.1f} GB</div>
                            <div class="metric-label">Total Storage</div>
                        </div>
                    </div>
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="metric-number text-success">{repository_metrics.get('total_commits', 0):,}</div>
                            <div class="metric-label">Total Commits</div>
                        </div>
                    </div>
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="metric-number text-warning">{repository_metrics.get('orphaned_repositories', 0)}</div>
                            <div class="metric-label">Orphaned Repos</div>
                        </div>
                    </div>
                    <div class="card text-center">
                        <div class="card-body">
                            <div class="metric-number text-info">{repository_metrics.get('avg_pipeline_success_rate', 0):.1f}%</div>
                            <div class="metric-label">Pipeline Success</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Best Practices Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5><i class="fas fa-lightbulb me-2"></i>💡 Best Practice Recommendations</h5>
                    </div>
                    <div class="card-body">
                        {self._generate_best_practices_html(best_practices)}
                    </div>
                </div>
            </div>
        </div>

        <!-- Repository Analysis Table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-list me-2"></i>📊 Repository Overview</h5>
                        <div class="input-group" style="width: 300px;">
                            <input type="text" id="repoFilter" class="form-control" placeholder="Filter repositories...">
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table data-table" id="repositoryTable">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size</th>
                                        <th>Commits</th>
                                        <th>Contributors</th>
                                        <th>Issues</th>
                                        <th>MR Lead Time</th>
                                        <th>CI Status</th>
                                        <th>Overall Health</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {self._generate_repository_rows_enhanced(repositories, enhanced_analysis)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Storage Chart
            document.addEventListener('DOMContentLoaded', function() {{
                const storageData = {json.dumps(repository_metrics.get('storage_breakdown', {}))};
                const storageCtx = document.getElementById('storageChart');
                if (storageCtx && Object.keys(storageData).length > 0) {{
                    new Chart(storageCtx, {{
                        type: 'doughnut',
                        data: {{
                            labels: Object.keys(storageData),
                            datasets: [{{
                                data: Object.values(storageData),
                                backgroundColor: ['#0d6efd', '#6f42c1', '#fd7e14', '#20c997', '#dc3545'],
                                borderWidth: 2,
                                borderColor: '#fff'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{
                                    position: 'bottom'
                                }}
                            }}
                        }}
                    }});
                }}
            }});
        </script>
        """

    def _generate_repository_rows(self, repositories, enhanced_analysis) -> str:
        """Generate repository table rows for the overview."""
        rows_html = ""

        # Create lookup dictionaries for metrics
        issue_metrics = {
            m.path_with_namespace if hasattr(m, "path_with_namespace") else "": m
            for m in enhanced_analysis.get("issue_metrics", [])
        }
        mr_metrics = {
            m.path_with_namespace if hasattr(m, "path_with_namespace") else "": m
            for m in enhanced_analysis.get("mr_metrics", [])
        }
        ci_metrics = {
            m.path_with_namespace if hasattr(m, "path_with_namespace") else "": m
            for m in enhanced_analysis.get("ci_metrics", [])
        }
        config_metrics = {
            m.path_with_namespace if hasattr(m, "path_with_namespace") else "": m
            for m in enhanced_analysis.get("ci_config_metrics", [])
        }
        perf_metrics = {
            m.path_with_namespace if hasattr(m, "path_with_namespace") else "": m
            for m in enhanced_analysis.get("performance_metrics", [])
        }

        for repo in repositories[:20]:  # Limit to first 20 for performance
            repo_name = getattr(
                repo, "path_with_namespace", getattr(repo, "name", "Unknown")
            )

            # Get metrics for this repo
            issue_data = issue_metrics.get(repo_name)
            mr_data = mr_metrics.get(repo_name)
            ci_data = ci_metrics.get(repo_name)
            config_data = config_metrics.get(repo_name)
            perf_data = perf_metrics.get(repo_name)

            # Build row data
            issues_count = (
                getattr(issue_data, "open_issues_count", 0) if issue_data else 0
            )
            mr_lead_time = (
                f"{getattr(mr_data, 'avg_lead_time_hours', 0) / 24:.1f}d"
                if mr_data
                else "N/A"
            )
            ci_status = "✅" if getattr(ci_data, "total_pipelines_30d", 0) > 0 else "❌"
            config_score = (
                f"{getattr(config_data, 'best_practices_score', 0):.0f}"
                if config_data
                else "0"
            )
            perf_score = (
                f"{getattr(perf_data, 'performance_score', 0):.0f}"
                if perf_data
                else "0"
            )

            # Calculate overall health (simple average)
            health_scores = []
            if issue_data:
                health_scores.append(
                    90 if issues_count < 5 else 60 if issues_count < 20 else 30
                )
            if mr_data:
                health_scores.append(
                    90 if getattr(mr_data, "avg_lead_time_hours", 0) < 120 else 60
                )
            if ci_data:
                health_scores.append(
                    90 if getattr(ci_data, "total_pipelines_30d", 0) > 0 else 30
                )
            if config_data:
                health_scores.append(getattr(config_data, "best_practices_score", 0))
            if perf_data:
                health_scores.append(getattr(perf_data, "performance_score", 0))

            overall_health = (
                sum(health_scores) / len(health_scores) if health_scores else 50
            )
            health_class = (
                "success"
                if overall_health >= 80
                else "warning" if overall_health >= 60 else "danger"
            )
            health_icon = (
                "🟢" if overall_health >= 80 else "🟡" if overall_health >= 60 else "🔴"
            )

            rows_html += f"""
            <tr>
                <td><strong>{repo_name}</strong></td>
                <td><span class="badge bg-{'success' if issues_count == 0 else 'warning' if issues_count < 10 else 'danger'}">{issues_count}</span></td>
                <td>{mr_lead_time}</td>
                <td>{ci_status}</td>
                <td><span class="badge bg-{'success' if int(config_score) >= 80 else 'warning' if int(config_score) >= 60 else 'danger'}">{config_score}</span></td>
                <td><span class="badge bg-{'success' if int(perf_score) >= 80 else 'warning' if int(perf_score) >= 60 else 'danger'}">{perf_score}</span></td>
                <td>{health_icon} <span class="badge bg-{health_class}">{overall_health:.0f}</span></td>
            </tr>
            """

        return rows_html

    def _generate_issues_tab(self, issue_analysis, issue_metrics) -> str:
        """Generate the Issues tab (P1) content."""
        if (
            not issue_analysis
            or not isinstance(issue_analysis, dict)
            or "total_projects" not in issue_analysis
        ):
            return (
                "<div class='alert alert-info'>No issue analysis data available.</div>"
            )

        return f"""
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Issue Age Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="issueAgeChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Issue Statistics</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Total Projects:</span>
                                <strong>{get_attr_safe(issue_analysis, 'total_projects', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Open Issues:</span>
                                <strong class="text-warning">{get_attr_safe(issue_analysis, 'total_open_issues', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Avg Age:</span>
                                <strong>{get_attr_safe(issue_analysis, 'system_avg_age_days', 0):.1f} days</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>90th Percentile:</span>
                                <strong>{get_attr_safe(issue_analysis, 'system_90th_percentile_days', 0):.1f} days</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-header">
                        <h5>Health Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="text-center">
                            <div class="fs-1">{get_attr_safe(issue_analysis, 'health_status', 'Unknown')}</div>
                            <div class="mt-2">
                                <span class="badge bg-success me-1">🟢 {get_attr_safe(issue_analysis, 'green_projects_count', 0)}</span>
                                <span class="badge bg-warning me-1">🟡 {get_attr_safe(issue_analysis, 'yellow_projects_count', 0)}</span>
                                <span class="badge bg-danger">🔴 {get_attr_safe(issue_analysis, 'red_projects_count', 0)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list me-2"></i>Repository Issue Details</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table data-table">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Open Issues</th>
                                        <th>Avg Age (days)</th>
                                        <th>90th Percentile</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {self._generate_issue_rows(issue_metrics)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_issue_rows(self, issue_metrics) -> str:
        """Generate issue table rows."""
        rows_html = ""

        for metric in issue_metrics:
            if not hasattr(metric, "path_with_namespace"):
                continue

            status_class = (
                "success"
                if metric.alert_level == "green"
                else "warning" if metric.alert_level == "yellow" else "danger"
            )
            status_icon = (
                "🟢"
                if metric.alert_level == "green"
                else "🟡" if metric.alert_level == "yellow" else "🔴"
            )

            # Generate oldest issues links
            oldest_issues = ""
            for issue in metric.oldest_issues[:3]:
                oldest_issues += f"<a href='{issue.get('web_url', '#')}' target='_blank' class='badge bg-secondary me-1'>#{issue.get('iid', '?')}</a>"

            rows_html += f"""
            <tr>
                <td><strong>{metric.path_with_namespace}</strong></td>
                <td><span class="badge bg-{'success' if metric.open_issues_count == 0 else 'warning' if metric.open_issues_count < 10 else 'danger'}">{metric.open_issues_count}</span></td>
                <td>{metric.avg_issue_age_days:.1f}</td>
                <td>{metric.issue_age_90th_percentile:.1f}</td>
                <td>{status_icon} <span class="badge bg-{status_class}">{metric.alert_level.title()}</span></td>
                <td>{oldest_issues}</td>
            </tr>
            """

        return rows_html

    def _generate_mr_tab(self, mr_analysis, mr_metrics) -> str:
        """Generate the MR tab (P2) content."""
        if (
            not mr_analysis
            or not isinstance(mr_analysis, dict)
            or "total_projects" not in mr_analysis
        ):
            return "<div class='alert alert-info'>No MR analysis data available.</div>"

        return f"""
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-code-branch me-2"></i>MR Lead Time Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="mrLeadTimeChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Code Review Statistics</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Total MRs (180d):</span>
                                <strong>{get_attr_safe(mr_analysis, 'total_mrs_180d', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Avg Lead Time:</span>
                                <strong class="text-info">{get_attr_safe(mr_analysis, 'avg_system_lead_time', 0) / 24:.1f} days</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Median Lead Time:</span>
                                <strong>{get_attr_safe(mr_analysis, 'median_system_lead_time', 0) / 24:.1f} days</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Avg Reviews:</span>
                                <strong>{get_attr_safe(mr_analysis, 'avg_review_comments', 0):.1f} comments</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-header">
                        <h5>System Health</h5>
                    </div>
                    <div class="card-body text-center">
                        <div class="fs-1">{get_attr_safe(mr_analysis, 'health_status', 'Unknown')}</div>
                        <div class="mt-2">
                            <span class="badge bg-danger me-1">🔴 {len(get_attr_safe(mr_analysis, 'flagged_repositories', []))} Flagged</span>
                            <span class="badge bg-success">🟢 {get_attr_safe(mr_analysis, 'total_projects', 0) - len(get_attr_safe(mr_analysis, 'flagged_repositories', []))} Healthy</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_ci_tab(self, ci_analysis, ci_metrics) -> str:
        """Generate the CI tab (P3) content."""
        if (
            not ci_analysis
            or not isinstance(ci_analysis, dict)
            or "total_projects" not in ci_analysis
        ):
            return "<div class='alert alert-info'>No CI analysis data available.</div>"

        return f"""
        <div class="row">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs me-2"></i>CI Adoption</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="ciAdoptionChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line me-2"></i>Pipeline Success Rate</h5>
                    </div>
                    <div class="card-body">
                        <div class="text-center">
                            <div class="display-4 text-{'success' if get_attr_safe(ci_analysis, 'system_success_rate', 100) >= 90 else 'warning' if get_attr_safe(ci_analysis, 'system_success_rate', 100) >= 80 else 'danger'}">
                                {get_attr_safe(ci_analysis, 'system_success_rate', 100):.1f}%
                            </div>
                            <p class="text-muted">System Success Rate</p>
                        </div>
                        <hr>
                        <div class="row text-center">
                            <div class="col">
                                <div class="h5">{get_attr_safe(ci_analysis, 'total_pipelines_30d', 0)}</div>
                                <small class="text-muted">Total Pipelines</small>
                            </div>
                            <div class="col">
                                <div class="h5">{get_attr_safe(ci_analysis, 'projects_with_ci', 0)}</div>
                                <small class="text-muted">Projects with CI</small>
                            </div>
                            <div class="col">
                                <div class="h5">{get_attr_safe(ci_analysis, 'projects_with_jenkins', 0)}</div>
                                <small class="text-muted">Jenkins Integrations</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_config_tab(self, ci_config_analysis, ci_config_metrics) -> str:
        """Generate the Configuration tab (P4) content."""
        if (
            not ci_config_analysis
            or not isinstance(ci_config_analysis, dict)
            or "total_projects" not in ci_config_analysis
        ):
            return "<div class='alert alert-info'>No CI configuration analysis data available.</div>"

        return f"""
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-file-code me-2"></i>Configuration Quality Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="configQualityChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Configuration Statistics</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Projects with CI Config:</span>
                                <strong>{get_attr_safe(ci_config_analysis, 'projects_with_ci_config', 0)}/{get_attr_safe(ci_config_analysis, 'total_projects', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Avg Complexity:</span>
                                <strong>{get_attr_safe(ci_config_analysis, 'avg_config_complexity', 0):.0f} lines</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Avg Best Practices:</span>
                                <strong class="text-{'success' if get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('avg_score', 0) >= 80 else 'warning' if get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('avg_score', 0) >= 60 else 'danger'}">{get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('avg_score', 0):.1f}/100</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-header">
                        <h5>Quality Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="text-center">
                            <span class="badge bg-success me-1">🟢 {get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('excellent_configs', 0)} Excellent</span>
                            <span class="badge bg-warning me-1">🟡 {get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('good_configs', 0)} Good</span>
                            <span class="badge bg-danger">🔴 {get_attr_safe(ci_config_analysis, 'best_practices_summary', {}).get('needs_improvement', 0)} Poor</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_network_tab(self, submodule_analysis, submodule_metrics) -> str:
        """Generate the Network tab (P5) content."""
        if (
            not submodule_analysis
            or not isinstance(submodule_analysis, dict)
            or "total_projects" not in submodule_analysis
        ):
            return "<div class='alert alert-info'>No submodule network analysis data available.</div>"

        return f"""
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-project-diagram me-2"></i>Submodule Network Graph</h5>
                    </div>
                    <div class="card-body">
                        <div id="networkGraph" style="height: 400px; border: 1px solid #dee2e6; border-radius: 8px;">
                            <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                                <div class="text-center">
                                    <i class="fas fa-project-diagram fa-3x mb-3"></i>
                                    <p>Network visualization would be rendered here<br>
                                    <small>Submodule relationships: {get_attr_safe(submodule_analysis, 'total_submodule_relationships', 0)}</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Network Statistics</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Projects with Submodules:</span>
                                <strong>{get_attr_safe(submodule_analysis, 'projects_with_submodules', 0)}/{get_attr_safe(submodule_analysis, 'total_projects', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Total Relationships:</span>
                                <strong>{get_attr_safe(submodule_analysis, 'total_submodule_relationships', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Network Depth:</span>
                                <strong>{get_attr_safe(submodule_analysis, 'network_depth', 0)}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Circular Dependencies:</span>
                                <strong class="text-{'danger' if len(get_attr_safe(submodule_analysis, 'circular_dependencies', [])) > 0 else 'success'}">{len(get_attr_safe(submodule_analysis, 'circular_dependencies', []))}</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-header">
                        <h5>Network Health</h5>
                    </div>
                    <div class="card-body text-center">
                        <div class="fs-1">{get_attr_safe(submodule_analysis, 'health_status', 'Unknown')}</div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_performance_tab(
        self, performance_analysis, performance_metrics
    ) -> str:
        """Generate the Performance tab (P6) content with integrated performance analyzer."""

        # Generate performance optimization content from our analyzer
        if hasattr(self, "_repositories"):
            # _repositories are already converted to dicts in _build_enhanced_html
            analyzer = PerformanceAnalyzer(self._repositories)
            performance_report = analyzer.generate_performance_report()
            performance_content = create_performance_dashboard_content(
                performance_report
            )

            # Create summary metrics
            summary = performance_report["summary"]

            return f"""
            <div class="alert alert-warning mb-4" role="alert">
                <h4 class="alert-heading">🚨 Performance Crisis Detected!</h4>
                <p class="mb-0">
                    <strong>{summary['total_issues']} performance issues</strong> identified with
                    <strong>{summary['total_waste_gb']:.1f} GB storage waste</strong> and
                    <strong>{summary['optimization_potential_percent']:.0f}% optimization potential</strong>
                </p>
            </div>

            <div class="row mb-4">
                <div class="col-lg-3 col-md-6">
                    <div class="card border-danger">
                        <div class="card-body text-center">
                            <div class="display-4 text-danger">{summary['critical_issues']}</div>
                            <p class="card-text">Critical Issues</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="card border-warning">
                        <div class="card-body text-center">
                            <div class="display-4 text-warning">{summary['high_issues']}</div>
                            <p class="card-text">High Priority</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="card border-success">
                        <div class="card-body text-center">
                            <div class="display-4 text-success">{summary['potential_savings_gb']:.0f} GB</div>
                            <p class="card-text">Potential Savings</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="card border-info">
                        <div class="card-body text-center">
                            <div class="display-4 text-info">{summary['optimization_potential_percent']:.0f}%</div>
                            <p class="card-text">Optimization Potential</p>
                        </div>
                    </div>
                </div>
            </div>

            <h3 class="mb-4">🔧 Performance Issues & Solutions</h3>
            {performance_content}
            """

        # Fallback to original performance analysis if repositories not available
        if (
            not performance_analysis
            or not isinstance(performance_analysis, dict)
            or "total_projects" not in performance_analysis
        ):
            return "<div class='alert alert-info'>No performance analysis data available.</div>"

        cache_adoption = (
            (
                performance_analysis.get("projects_using_cache", 0)
                / performance_analysis.get("total_projects", 1)
                * 100
            )
            if performance_analysis.get("total_projects", 0) > 0
            else 0
        )
        lfs_adoption = (
            (
                performance_analysis.get("projects_using_lfs", 0)
                / performance_analysis.get("total_projects", 1)
                * 100
            )
            if performance_analysis.get("total_projects", 0) > 0
            else 0
        )

        return f"""
        <div class="row">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-rocket me-2"></i>Performance Adoption</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="performanceAdoptionChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-clock me-2"></i>Pipeline Performance</h5>
                    </div>
                    <div class="card-body">
                        <div class="text-center">
                            <div class="display-4 text-{'success' if get_attr_safe(performance_analysis, 'avg_pipeline_duration', 0) < 10 else 'warning' if get_attr_safe(performance_analysis, 'avg_pipeline_duration', 0) < 30 else 'danger'}">
                                {get_attr_safe(performance_analysis, 'avg_pipeline_duration', 0):.1f}min
                            </div>
                            <p class="text-muted">Average Pipeline Duration</p>
                        </div>
                        <hr>
                        <div class="row text-center">
                            <div class="col">
                                <div class="h5">{cache_adoption:.1f}%</div>
                                <small class="text-muted">Cache Adoption</small>
                            </div>
                            <div class="col">
                                <div class="h5">{lfs_adoption:.1f}%</div>
                                <small class="text-muted">LFS Usage</small>
                            </div>
                            <div class="col">
                                <div class="h5">{len(get_attr_safe(performance_analysis, 'best_performers', []))}</div>
                                <small class="text-muted">Top Performers</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_actionable_tab(self) -> str:
        """Generate the Actionable Dashboard tab (A1) content."""
        if hasattr(self, "_repositories"):
            # _repositories are already converted to dicts in _build_enhanced_html
            actionable_dashboard = ActionableDashboard(
                self._repositories, self.enhanced_analysis
            )
            actions = actionable_dashboard.analyze_and_generate_actions()
            return actionable_dashboard.generate_html_dashboard(actions)
        else:
            return """
            <div class="alert alert-warning">
                <h4>⚠️ Actionable Dashboard Unavailable</h4>
                <p>Repository data not available for actionable analysis.</p>
            </div>
            """

    def _generate_comprehensive_tab(self) -> str:
        """Generate the Comprehensive Dashboard tab (C1) content."""
        if hasattr(self, "_repositories"):
            # _repositories are already converted to dicts in _build_enhanced_html
            comprehensive_dashboard = ComprehensiveDashboard(
                self._repositories, self.enhanced_analysis
            )
            return comprehensive_dashboard.generate_html_dashboard()
        else:
            return """
            <div class="alert alert-warning">
                <h4>⚠️ Comprehensive Dashboard Unavailable</h4>
                <p>Repository data not available for comprehensive analysis.</p>
            </div>
            """

    def _convert_repositories_to_dicts(self, repositories):
        """Convert RepositoryStats objects to dicts for dashboard compatibility."""
        repositories_as_dicts = []
        for repo in repositories:
            if hasattr(repo, "__dict__"):  # RepositoryStats dataclass
                repo_dict = {
                    "id": repo.id,
                    "name": repo.name,
                    "path_with_namespace": repo.path_with_namespace,
                    "size_mb": repo.size_mb,
                    "artifacts_size_mb": repo.artifacts_size_mb,
                    "lfs_size_mb": repo.lfs_size_mb,
                    "pipeline_count": repo.pipeline_count,
                    "last_activity": repo.last_activity,
                    "last_activity_at": repo.last_activity,  # Alias for compatibility
                    "open_issues": getattr(repo, "open_issues", 0),
                    "open_mrs": getattr(repo, "open_mrs", 0),
                }
                repositories_as_dicts.append(repo_dict)
            else:  # Already a dict
                repositories_as_dicts.append(repo)
        return repositories_as_dicts

    def _get_enhanced_javascript(self) -> str:
        """Enhanced JavaScript for the dashboard."""
        return """
        // Tab switching function
        function switchToTab(tabName) {
            const tabMap = {
                'p1': 'issues-tab',
                'p2': 'mr-tab',
                'p3': 'ci-tab',
                'p4': 'config-tab',
                'p5': 'network-tab',
                'p6': 'performance-tab',
                'a1': 'actionable-tab',
                'c1': 'comprehensive-tab'
            };

            const tabId = tabMap[tabName] || tabName + '-tab';
            const tabElement = document.getElementById(tabId);
            if (tabElement) {
                const tab = new bootstrap.Tab(tabElement);
                tab.show();
            }
        }

        // Global search functionality
        document.getElementById('globalSearch').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const tables = document.querySelectorAll('.data-table tbody tr');

            tables.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });

        // Repository filter
        const repoFilter = document.getElementById('repoFilter');
        if (repoFilter) {
            repoFilter.addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#repositoryTable tbody tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }

        // Initialize charts when tabs are shown
        document.addEventListener('DOMContentLoaded', function() {
            // System trends chart
            const trendsCtx = document.getElementById('systemTrendsChart');
            if (trendsCtx) {
                new Chart(trendsCtx, {
                    type: 'line',
                    data: {
                        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                        datasets: [{
                            label: 'Issues Resolved',
                            data: [12, 19, 15, 25],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }, {
                            label: 'MRs Merged',
                            data: [8, 15, 12, 20],
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                            }
                        }
                    }
                });
            }
        });

        // Show loading spinner when switching tabs
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', function(e) {
                const targetPane = document.querySelector(e.target.getAttribute('data-bs-target'));
                if (targetPane) {
                    targetPane.classList.add('fade-in');
                }
            });
        });

        // Auto-refresh functionality (disabled by default)
        let autoRefreshInterval;
        function toggleAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            } else {
                autoRefreshInterval = setInterval(() => {
                    // Refresh data logic would go here
                    console.log('Auto-refreshing data...');
                }, 300000); // 5 minutes
            }
        }

        // Export functionality
        function exportToCSV(tableId) {
            const table = document.getElementById(tableId);
            if (!table) return;

            const rows = Array.from(table.querySelectorAll('tr'));
            const csv = rows.map(row => {
                const cells = Array.from(row.querySelectorAll('th, td'));
                return cells.map(cell => `"${cell.textContent.trim()}"`).join(',');
            }).join('\\n');

            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${tableId}_export_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
        """

    def _generate_basic_dashboard(
        self,
        repositories: List[Any],
        output_file: str,
        enhanced_kpis_requested: bool = False,
    ) -> str:
        """Generate basic dashboard with tab navigation when enhanced analysis is not available."""

        # Calculate basic repository metrics
        repository_metrics = self._calculate_repository_metrics(repositories)

        # Generate HTML with tab-based navigation
        basic_html = self._build_basic_html_with_tabs(
            repositories, repository_metrics, enhanced_kpis_requested
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(basic_html)

        return output_file

    def _build_basic_html_with_tabs(
        self,
        repositories: List[Any],
        repository_metrics: Dict[str, Any],
        enhanced_kpis_requested: bool = False,
    ) -> str:
        """Build basic HTML dashboard with tab navigation."""

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitLab Instance Analysis Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {self._get_enhanced_css()}
    </style>
</head>
<body>
    <!-- Header -->
    <nav class="navbar navbar-dark bg-primary shadow-sm">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-chart-line me-2"></i>
                GitLab Instance Analysis Dashboard
            </span>
            <div class="d-flex align-items-center text-white">
                <small class="me-3">
                    <i class="fas fa-clock me-1"></i>
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </small>
                <div class="input-group" style="width: 250px;">
                    <input type="text" id="globalSearch" class="form-control form-control-sm"
                           placeholder="🔍 Search repositories...">
                </div>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <!-- Enhanced Analysis Notice -->
        {self._generate_analysis_mode_notice(enhanced_kpis_requested)}

        <!-- Main Tab Navigation -->
        <div class="row">
            <div class="col">
                <ul class="nav nav-tabs nav-fill" id="mainTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="overview-tab" data-bs-toggle="tab"
                                data-bs-target="#overview" type="button" role="tab">
                            <i class="fas fa-tachometer-alt me-2"></i>System Overview
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="repositories-tab" data-bs-toggle="tab"
                                data-bs-target="#repositories" type="button" role="tab">
                            <i class="fas fa-folder me-2"></i>Repository Details
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="storage-tab" data-bs-toggle="tab"
                                data-bs-target="#storage" type="button" role="tab">
                            <i class="fas fa-hdd me-2"></i>Storage Analysis
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="insights-tab" data-bs-toggle="tab"
                                data-bs-target="#insights" type="button" role="tab">
                            <i class="fas fa-lightbulb me-2"></i>Recommendations
                        </button>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Tab Content -->
        <div class="tab-content mt-3" id="tabContent">
            <!-- System Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                {self._generate_system_overview_tab(repositories, repository_metrics)}
            </div>

            <!-- Repository Details Tab -->
            <div class="tab-pane fade" id="repositories" role="tabpanel">
                {self._generate_repository_details_tab(repositories)}
            </div>

            <!-- Storage Analysis Tab -->
            <div class="tab-pane fade" id="storage" role="tabpanel">
                {self._generate_storage_analysis_tab(repositories, repository_metrics)}
            </div>

            <!-- Recommendations Tab -->
            <div class="tab-pane fade" id="insights" role="tabpanel">
                {self._generate_recommendations_tab(repositories)}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        {self._get_dashboard_javascript()}
    </script>
</body>
</html>
        """

        return html_template

    def _generate_critical_issues_html(self, critical_issues):
        """Generate HTML for critical issues section."""
        if not critical_issues:
            return """
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>No Critical Issues Found</h6>
                <p class="mb-0">Your GitLab instance appears to be in good health!</p>
            </div>
            """

        issues_html = ""
        for issue in critical_issues[:5]:  # Show top 5 critical issues
            severity_class = {
                "critical": "danger",
                "warning": "warning",
                "info": "info",
            }.get(issue.severity, "secondary")

            severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                issue.severity, "⚪"
            )

            affected_repos_text = ""
            if issue.affected_repos:
                affected_repos_text = (
                    f"<br><small><strong>Affected:</strong> {', '.join(issue.affected_repos[:3])}"
                    + (
                        f" (+{len(issue.affected_repos)-3} more)"
                        if len(issue.affected_repos) > 3
                        else ""
                    )
                    + "</small>"
                )

            issues_html += f"""
            <div class="alert alert-{severity_class} border-start border-{severity_class} border-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="alert-heading">{severity_icon} {issue.title}</h6>
                        <p class="mb-2">{issue.description}</p>
                        <div class="mb-2">
                            <strong>💡 Recommendation:</strong> {issue.recommendation}
                        </div>
                        <small class="text-muted">
                            <i class="fas fa-tag me-1"></i>Source: {issue.source}
                            {affected_repos_text}
                        </small>
                    </div>
                    <span class="badge bg-{severity_class}">Priority {issue.priority}</span>
                </div>
            </div>
            """

        return issues_html

    def _generate_best_practices_html(self, best_practices):
        """Generate HTML for best practices section."""
        if not best_practices:
            return """
            <div class="alert alert-info">
                <h6><i class="fas fa-info-circle me-2"></i>No Specific Recommendations</h6>
                <p class="mb-0">Your current configuration looks good! Keep monitoring for optimization opportunities.</p>
            </div>
            """

        practices_html = ""
        for practice in best_practices[:3]:  # Show top 3 best practices
            impact_class = {"high": "success", "medium": "warning", "low": "info"}.get(
                practice.impact, "secondary"
            )

            effort_class = {
                "low": "success",
                "medium": "warning",
                "high": "danger",
            }.get(practice.effort, "secondary")

            steps_html = ""
            for i, step in enumerate(practice.implementation_steps[:4], 1):
                steps_html += f"<li>{step}</li>"

            practices_html += f"""
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">{practice.title}</h6>
                        <div>
                            <span class="badge bg-{impact_class} me-1">Impact: {practice.impact.title()}</span>
                            <span class="badge bg-{effort_class}">Effort: {practice.effort.title()}</span>
                        </div>
                    </div>
                    <p class="card-text">{practice.description}</p>
                    <div class="accordion accordion-flush" id="practice{hash(practice.title) % 10000}">
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                                        data-bs-target="#collapse{hash(practice.title) % 10000}" aria-expanded="false">
                                    <i class="fas fa-list-ol me-2"></i>Implementation Steps
                                </button>
                            </h2>
                            <div id="collapse{hash(practice.title) % 10000}" class="accordion-collapse collapse">
                                <div class="accordion-body">
                                    <ol>{steps_html}</ol>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """

        return practices_html

    def _generate_repository_rows_enhanced(self, repositories, enhanced_analysis):
        """Generate enhanced repository table rows with original metrics."""
        rows_html = ""

        # Create lookup dictionaries for metrics
        issue_metrics = {
            getattr(m, "path_with_namespace", ""): m
            for m in enhanced_analysis.get("issue_metrics", [])
        }
        mr_metrics = {
            getattr(m, "path_with_namespace", ""): m
            for m in enhanced_analysis.get("mr_metrics", [])
        }
        ci_metrics = {
            getattr(m, "path_with_namespace", ""): m
            for m in enhanced_analysis.get("ci_metrics", [])
        }

        for repo in repositories[:20]:  # Limit to first 20 for performance
            repo_name = getattr(
                repo, "path_with_namespace", getattr(repo, "name", "Unknown")
            )

            # Original repository metrics
            size_mb = getattr(repo, "size_mb", 0)
            commits = getattr(repo, "commit_count", 0)
            contributors = getattr(repo, "contributor_count", 0)

            # Enhanced metrics
            issue_data = issue_metrics.get(repo_name)
            mr_data = mr_metrics.get(repo_name)
            ci_data = ci_metrics.get(repo_name)

            issues_count = (
                getattr(issue_data, "open_issues_count", 0) if issue_data else 0
            )
            mr_lead_time = (
                f"{getattr(mr_data, 'avg_lead_time_hours', 0) / 24:.1f}d"
                if mr_data and getattr(mr_data, "avg_lead_time_hours", 0) > 0
                else "N/A"
            )
            ci_status = (
                "✅"
                if ci_data and getattr(ci_data, "total_pipelines_30d", 0) > 0
                else "❌"
            )

            # Calculate overall health
            health_score = 50  # Base score
            if issues_count == 0:
                health_score += 15
            elif issues_count < 5:
                health_score += 10
            if commits > 100:
                health_score += 10
            elif commits > 10:
                health_score += 5
            if contributors > 3:
                health_score += 10
            elif contributors > 1:
                health_score += 5
            if ci_data and getattr(ci_data, "total_pipelines_30d", 0) > 0:
                health_score += 15

            health_class = (
                "success"
                if health_score >= 80
                else "warning" if health_score >= 60 else "danger"
            )
            health_icon = (
                "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
            )

            rows_html += f"""
            <tr>
                <td><strong>{repo_name}</strong></td>
                <td>{size_mb:.1f} MB</td>
                <td>{commits:,}</td>
                <td>{contributors}</td>
                <td><span class="badge bg-{'success' if issues_count == 0 else 'warning' if issues_count < 10 else 'danger'}">{issues_count}</span></td>
                <td>{mr_lead_time}</td>
                <td>{ci_status}</td>
                <td>{health_icon} <span class="badge bg-{health_class}">{health_score}</span></td>
            </tr>
            """

        return rows_html

    def _generate_system_overview_tab(self, repositories, repository_metrics):
        """Generate the System Overview tab content."""
        from datetime import datetime

        total_repos = len(repositories)
        total_size_gb = sum(getattr(repo, "size_mb", 0) for repo in repositories) / 1024
        total_commits = sum(getattr(repo, "commit_count", 0) for repo in repositories)
        active_repos = [
            repo
            for repo in repositories
            if (datetime.now() - getattr(repo, "last_activity", datetime.min)).days < 30
        ]

        return f"""
        <div class="row">
            <div class="col-12">
                <h3><i class="fas fa-chart-bar me-2"></i>System Overview</h3>
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="card metric-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-folder fa-2x text-primary mb-2"></i>
                                <h3 class="text-primary">{total_repos:,}</h3>
                                <p class="card-text">Total Repositories</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-hdd fa-2x text-info mb-2"></i>
                                <h3 class="text-info">{total_size_gb:.1f} GB</h3>
                                <p class="card-text">Total Storage</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-code-branch fa-2x text-success mb-2"></i>
                                <h3 class="text-success">{total_commits:,}</h3>
                                <p class="card-text">Total Commits</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-pulse fa-2x text-warning mb-2"></i>
                                <h3 class="text-warning">{len(active_repos):,}</h3>
                                <p class="card-text">Active Repositories</p>
                                <small class="text-muted">(last 30 days)</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_repository_details_tab(self, repositories):
        """Generate the Repository Details tab content."""
        from datetime import datetime

        sorted_repos = sorted(
            repositories, key=lambda x: getattr(x, "size_mb", 0), reverse=True
        )

        rows_html = ""
        for repo in sorted_repos:
            name = getattr(
                repo, "path_with_namespace", getattr(repo, "name", "Unknown")
            )
            size_mb = getattr(repo, "size_mb", 0)
            commits = getattr(repo, "commit_count", 0)
            contributors = getattr(repo, "contributor_count", 0)
            last_activity = getattr(repo, "last_activity", datetime.min)
            binary_files = getattr(repo, "binary_files", [])

            days_since_activity = (
                (datetime.now() - last_activity).days
                if last_activity != datetime.min
                else 999
            )
            activity_status = (
                "Active"
                if days_since_activity < 30
                else "Stale" if days_since_activity < 90 else "Inactive"
            )
            activity_class = (
                "success"
                if days_since_activity < 30
                else "warning" if days_since_activity < 90 else "danger"
            )

            binary_status = (
                f"<span class='badge bg-warning'>{len(binary_files)} binary files</span>"
                if binary_files
                else "<span class='badge bg-success'>Clean</span>"
            )

            rows_html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td>{size_mb:.2f} MB</td>
                <td>{commits:,}</td>
                <td>{contributors}</td>
                <td>{last_activity.strftime('%Y-%m-%d') if last_activity != datetime.min else 'Unknown'}</td>
                <td><span class="badge bg-{activity_class}">{activity_status}</span></td>
                <td>{binary_status}</td>
            </tr>
            """

        return f"""
        <div class="row">
            <div class="col-12">
                <h3><i class="fas fa-list me-2"></i>Repository Details</h3>
                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover" id="repositoryDetailsTable">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size</th>
                                        <th>Commits</th>
                                        <th>Contributors</th>
                                        <th>Last Activity</th>
                                        <th>Status</th>
                                        <th>Binary Files</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows_html}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_storage_analysis_tab(self, repositories, repository_metrics):
        """Generate the Storage Analysis tab content."""

        total_storage = sum(getattr(repo, "size_mb", 0) for repo in repositories)
        lfs_storage = sum(getattr(repo, "lfs_size_mb", 0) for repo in repositories)
        artifacts_storage = sum(
            getattr(repo, "artifacts_size_mb", 0) for repo in repositories
        )

        largest_repos = sorted(
            repositories, key=lambda x: getattr(x, "size_mb", 0), reverse=True
        )[:10]

        largest_rows = ""
        max_size = max(getattr(r, "size_mb", 0.1) for r in repositories)
        for repo in largest_repos:
            name = getattr(
                repo, "path_with_namespace", getattr(repo, "name", "Unknown")
            )
            size_mb = getattr(repo, "size_mb", 0)
            commits = getattr(repo, "commit_count", 0)

            largest_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{size_mb:.2f} MB</td>
                <td>{commits:,}</td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar" role="progressbar"
                             style="width: {(size_mb / max_size) * 100:.1f}%">
                            {size_mb:.1f} MB
                        </div>
                    </div>
                </td>
            </tr>
            """

        return f"""
        <div class="row">
            <div class="col-md-6">
                <h3><i class="fas fa-chart-pie me-2"></i>Storage Breakdown</h3>
                <div class="card">
                    <div class="card-body">
                        <canvas id="storageChart" height="300"></canvas>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <h3><i class="fas fa-trophy me-2"></i>Largest Repositories</h3>
                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size</th>
                                        <th>Commits</th>
                                        <th>Usage</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {largest_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        const storageData = {{
            'Repository Data': {(total_storage - lfs_storage - artifacts_storage):.1f},
            'LFS Objects': {lfs_storage:.1f},
            'Artifacts': {artifacts_storage:.1f}
        }};

        const ctx = document.getElementById('storageChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(storageData),
                datasets: [{{
                    data: Object.values(storageData),
                    backgroundColor: ['#0d6efd', '#6f42c1', '#fd7e14'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        </script>
        """

    def _generate_recommendations_tab(self, repositories):
        """Generate the Recommendations tab content."""
        from datetime import datetime

        binary_repos = [
            repo
            for repo in repositories
            if getattr(repo, "binary_files", [])
            and len(getattr(repo, "binary_files", [])) > 0
        ]

        inactive_repos = [
            repo
            for repo in repositories
            if (datetime.now() - getattr(repo, "last_activity", datetime.min)).days > 90
        ]

        large_repos = [
            repo for repo in repositories if getattr(repo, "size_mb", 0) > 100
        ]

        recommendations_html = ""

        if binary_repos:
            binary_list = ""
            for repo in binary_repos[:5]:
                repo_name = getattr(
                    repo, "path_with_namespace", getattr(repo, "name", "Unknown")
                )
                binary_list += f"<li><i class='fas fa-folder me-1'></i>{repo_name}</li>"

            more_binary = (
                f"<li><small class='text-muted'>... and {len(binary_repos)-5} more</small></li>"
                if len(binary_repos) > 5
                else ""
            )

            recommendations_html += f"""
            <div class="card mb-3 border-warning">
                <div class="card-header bg-warning text-dark">
                    <h5><i class="fas fa-file-archive me-2"></i>Git LFS Migration Recommended</h5>
                </div>
                <div class="card-body">
                    <p><strong>Impact:</strong> High | <strong>Effort:</strong> Medium</p>
                    <p>{len(binary_repos)} repositories contain binary files that should be migrated to Git LFS.</p>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Affected Repositories:</h6>
                            <ul class="list-unstyled">
                                {binary_list}
                                {more_binary}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Implementation Steps:</h6>
                            <ol class="small">
                                <li>Install Git LFS on development machines</li>
                                <li>Track binary file types with <code>git lfs track</code></li>
                                <li>Migrate existing binary files</li>
                                <li>Update CI/CD pipelines if needed</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
            """

        if not binary_repos and not inactive_repos and not large_repos:
            recommendations_html = """
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h5><i class="fas fa-check-circle me-2"></i>Repository Health Excellent</h5>
                </div>
                <div class="card-body">
                    <p class="mb-0">Your GitLab instance appears to be well-maintained!</p>
                    <hr>
                    <small class="text-muted">
                        <strong>Consider:</strong> Run with <code>--enhanced-kpis</code> for AI-powered insights.
                    </small>
                </div>
            </div>
            """

        return f"""
        <div class="row">
            <div class="col-12">
                <h3><i class="fas fa-lightbulb me-2"></i>Optimization Recommendations</h3>
                {recommendations_html}
            </div>
        </div>
        """

    def _get_dashboard_javascript(self):
        """Get basic dashboard JavaScript."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const globalSearch = document.getElementById('globalSearch');
            if (globalSearch) {
                globalSearch.addEventListener('input', function(e) {
                    const searchTerm = e.target.value.toLowerCase();
                    const tables = document.querySelectorAll('.table tbody tr');

                    tables.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(searchTerm) ? '' : 'none';
                    });
                });
            }

            document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
                tab.addEventListener('shown.bs.tab', function(e) {
                    const targetPane = document.querySelector(e.target.getAttribute('data-bs-target'));
                    if (targetPane) {
                        targetPane.classList.add('fade-in');
                    }
                });
            });
        });
        """

    def _generate_analysis_mode_notice(self, enhanced_kpis_requested: bool) -> str:
        """Generate appropriate notice based on whether enhanced KPIs were requested."""
        if enhanced_kpis_requested:
            # Enhanced KPIs were requested but data is missing/incomplete
            return """
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Enhanced Analysis Incomplete</strong> - Some enhanced KPI data is missing. This may be due to incremental mode or data collection issues.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>"""
        else:
            # Basic mode - suggest enhanced KPIs
            return """
        <div class="alert alert-info alert-dismissible fade show" role="alert">
            <i class="fas fa-info-circle me-2"></i>
            <strong>Basic Analysis Mode</strong> - Run with <code>--enhanced-kpis</code> to enable AI-powered insights and critical issue detection.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>"""
