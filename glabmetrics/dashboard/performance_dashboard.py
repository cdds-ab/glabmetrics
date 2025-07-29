#!/usr/bin/env python3
"""Performance dashboard for GitLab optimization."""

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from dateutil.parser import parse as parse_date


@dataclass
class PerformanceIssue:
    """Represents a performance issue with impact and remediation."""

    repository: str
    issue_type: str
    severity: str  # critical, high, medium, low
    impact_description: str
    current_value: float
    recommended_value: float
    cost_impact_gb: float
    remediation_steps: List[str]
    urgency_days: int


class PerformanceDashboard:
    """Analyzes GitLab repositories for performance bottlenecks."""

    def __init__(self, repositories: List[Dict[str, Any]]):
        self.repositories = repositories

    def analyze_artifact_bloat(self) -> List[PerformanceIssue]:
        """Identify repositories with excessive artifact storage."""
        issues = []

        # Critical threshold: >1GB artifacts
        for repo in self.repositories:
            artifacts_mb = repo.get("artifacts_size_mb", 0)
            if artifacts_mb > 1000:  # >1GB
                issues.append(
                    PerformanceIssue(
                        repository=repo["name"],
                        issue_type="Artifact Bloat Critical",
                        severity="critical",
                        impact_description=f"Repository consumes {artifacts_mb:.0f}MB in artifacts, likely causing GitLab performance degradation",
                        current_value=artifacts_mb,
                        recommended_value=100,  # Max 100MB recommended
                        cost_impact_gb=artifacts_mb / 1024,
                        remediation_steps=[
                            f"# Cleanup artifacts for {repo['name']}",
                            "# 1. Check artifact retention policy",
                            f"curl --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' https://gitlab.example.com/api/v4/projects/{repo['id']}/jobs?scope[]=success&per_page=100",
                            "",
                            "# 2. Set aggressive artifact expiration (7 days)",
                            f"# In .gitlab-ci.yml for project {repo['id']}:",
                            "artifacts:",
                            "  expire_in: 7 days",
                            "  when: always",
                            "",
                            "# 3. Clean up existing artifacts via API",
                            f"# WARNING: This will delete ALL artifacts for project {repo['id']}",
                            f"curl --request DELETE --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' https://gitlab.example.com/api/v4/projects/{repo['id']}/artifacts",
                            "",
                            "# 4. Monitor storage reduction",
                            f"watch -n 60 'curl -s --header \"PRIVATE-TOKEN: $GITLAB_TOKEN\" https://gitlab.example.com/api/v4/projects/{repo['id']} | jq .statistics'",
                        ],
                        urgency_days=7,  # Fix within 1 week
                    )
                )

        return issues

    def analyze_repository_bloat(self) -> List[PerformanceIssue]:
        """Identify repositories with excessive size without proper LFS usage."""
        issues = []

        for repo in self.repositories:
            size_mb = repo.get("size_mb", 0)
            lfs_mb = repo.get("lfs_size_mb", 0)

            # Large repos without LFS
            if size_mb > 500 and lfs_mb == 0:
                issues.append(
                    PerformanceIssue(
                        repository=repo["name"],
                        issue_type="Repository Size Without LFS",
                        severity="high",
                        impact_description=f"Repository is {size_mb:.0f}MB without Git LFS, causing slow clones and network congestion",
                        current_value=size_mb,
                        recommended_value=100,
                        cost_impact_gb=size_mb / 1024,
                        remediation_steps=[
                            f"# Migrate large files to LFS for {repo['name']}",
                            "cd /path/to/repository",
                            "",
                            "# 1. Install Git LFS",
                            "git lfs install",
                            "",
                            "# 2. Find large files (>50MB)",
                            "find . -type f -size +50M | head -10",
                            "",
                            "# 3. Track large file types",
                            "git lfs track '*.zip'",
                            "git lfs track '*.tar.gz'",
                            "git lfs track '*.exe'",
                            "git lfs track '*.dll'",
                            "git lfs track '*.bin'",
                            "",
                            "# 4. Track specific large files",
                            "find . -size +50M -type f | while read file; do",
                            '    git lfs track "$file"',
                            "done",
                            "",
                            "# 5. Commit LFS configuration",
                            "git add .gitattributes",
                            "git commit -m 'Add Git LFS tracking for large files'",
                            "",
                            "# 6. Migrate existing files to LFS",
                            "git lfs migrate import --include='*.zip,*.exe,*.dll,*.bin'",
                            "",
                            "# 7. Push changes",
                            "git push --force",
                        ],
                        urgency_days=30,
                    )
                )

        return issues

    def analyze_inactive_storage_waste(self) -> List[PerformanceIssue]:
        """Identify inactive repositories consuming storage."""
        issues = []
        cutoff_date = datetime.now() - timedelta(days=365)

        for repo in self.repositories:
            try:
                last_activity = parse_date(repo.get("last_activity", "2020-01-01"))
                if last_activity.tzinfo is not None:
                    last_activity = last_activity.replace(tzinfo=None)

                size_mb = repo.get("size_mb", 0)
                artifacts_mb = repo.get("artifacts_size_mb", 0)
                total_storage = size_mb + artifacts_mb

                if last_activity < cutoff_date and total_storage > 100:
                    days_inactive = (datetime.now() - last_activity).days
                    issues.append(
                        PerformanceIssue(
                            repository=repo["name"],
                            issue_type="Inactive Storage Waste",
                            severity="medium",
                            impact_description=f"Repository inactive for {days_inactive} days but consuming {total_storage:.0f}MB storage",
                            current_value=total_storage,
                            recommended_value=0,  # Should be archived
                            cost_impact_gb=total_storage / 1024,
                            remediation_steps=[
                                f"# Archive inactive repository {repo['name']}",
                                f"# Repository has been inactive for {days_inactive} days",
                                "",
                                "# 1. Create backup (optional)",
                                f"git clone --mirror https://gitlab.example.com/group/{repo['name']}.git",
                                f"tar -czf {repo['name']}_backup_$(date +%Y%m%d).tar.gz {repo['name']}.git",
                                "",
                                "# 2. Archive via GitLab API",
                                f"curl --request POST --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                                f"     'https://gitlab.example.com/api/v4/projects/{repo['id']}/archive'",
                                "",
                                "# 3. Or move to archive group",
                                f"curl --request PUT --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                                f"     --data 'path={repo['name']}&namespace_id=ARCHIVE_GROUP_ID' \\",
                                f"     'https://gitlab.example.com/api/v4/projects/{repo['id']}'",
                                "",
                                "# 4. Update documentation",
                                f"echo 'Repository {repo['name']} archived on $(date) due to {days_inactive} days inactivity' >> ARCHIVED_REPOS.md",
                            ],
                            urgency_days=60,
                        )
                    )
            except:
                continue

        return issues

    def analyze_pipeline_performance(self) -> List[PerformanceIssue]:
        """Identify repositories with pipeline performance issues."""
        issues = []

        for repo in self.repositories:
            pipeline_count = repo.get("pipeline_count", 0)
            artifacts_mb = repo.get("artifacts_size_mb", 0)

            # High pipeline activity + high artifacts = performance issue
            if pipeline_count > 1000 and artifacts_mb > 500:
                artifact_per_pipeline = (
                    artifacts_mb / pipeline_count if pipeline_count > 0 else 0
                )

                issues.append(
                    PerformanceIssue(
                        repository=repo["name"],
                        issue_type="Pipeline Artifact Inefficiency",
                        severity="high",
                        impact_description=f"High pipeline activity ({pipeline_count} pipelines) generating excessive artifacts ({artifacts_mb:.0f}MB, {artifact_per_pipeline:.2f}MB/pipeline)",
                        current_value=artifact_per_pipeline,
                        recommended_value=0.1,  # Max 0.1MB per pipeline
                        cost_impact_gb=artifacts_mb / 1024,
                        remediation_steps=[
                            f"# Optimize pipeline artifacts for {repo['name']}",
                            "# Project has high pipeline frequency with large artifacts",
                            "",
                            "# 1. Analyze current artifact patterns",
                            f"curl --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                            f"     'https://gitlab.example.com/api/v4/projects/{repo['id']}/jobs?scope[]=success&per_page=10' \\",
                            f"     | jq '.[] | {{id, artifacts_file, name}}'",
                            "",
                            "# 2. Update .gitlab-ci.yml with smart artifact handling",
                            "artifacts:",
                            "  # Only keep artifacts for failed jobs",
                            "  when: on_failure",
                            "  # Short expiration",
                            "  expire_in: 3 days",
                            "  # Only essential files",
                            "  paths:",
                            "    - 'logs/*.log'",
                            "    - 'test-results.xml'",
                            "  # Exclude large build outputs",
                            "  exclude:",
                            "    - '*.exe'",
                            "    - '*.dll'",
                            "    - 'node_modules/'",
                            "",
                            "# 3. Implement artifact cleanup job",
                            "cleanup_artifacts:",
                            "  stage: cleanup",
                            "  script:",
                            f"    - curl --request DELETE --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' https://gitlab.example.com/api/v4/projects/{repo['id']}/artifacts",
                            "  rules:",
                            "    - if: '$CI_PIPELINE_SOURCE == \"schedule\"'",
                            "  when: manual",
                        ],
                        urgency_days=14,
                    )
                )

        return issues

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report."""
        all_issues = []

        # Collect all performance issues
        all_issues.extend(self.analyze_artifact_bloat())
        all_issues.extend(self.analyze_repository_bloat())
        all_issues.extend(self.analyze_inactive_storage_waste())
        all_issues.extend(self.analyze_pipeline_performance())

        # Calculate system-wide impact
        total_waste_gb = sum(issue.cost_impact_gb for issue in all_issues)
        critical_issues = len([i for i in all_issues if i.severity == "critical"])
        high_issues = len([i for i in all_issues if i.severity == "high"])

        # Calculate current system storage
        total_repo_size = (
            sum(repo.get("size_mb", 0) for repo in self.repositories) / 1024
        )
        total_artifacts = (
            sum(repo.get("artifacts_size_mb", 0) for repo in self.repositories) / 1024
        )

        return {
            "issues": all_issues,
            "summary": {
                "total_issues": len(all_issues),
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "total_waste_gb": total_waste_gb,
                "potential_savings_gb": total_waste_gb
                * 0.8,  # Assume 80% can be cleaned
                "current_storage_gb": total_repo_size + total_artifacts,
                "optimization_potential_percent": (
                    (total_waste_gb / (total_repo_size + total_artifacts)) * 100
                    if (total_repo_size + total_artifacts) > 0
                    else 0
                ),
            },
            "recommendations": {
                "immediate_actions": [i for i in all_issues if i.urgency_days <= 7],
                "medium_term_actions": [
                    i for i in all_issues if 7 < i.urgency_days <= 30
                ],
                "long_term_actions": [i for i in all_issues if i.urgency_days > 30],
            },
        }

    def generate_html_dashboard(self, performance_report: Dict[str, Any]) -> str:
        """Create HTML content for performance issues."""
        # Sort issues by severity and impact
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(
            performance_report["issues"],
            key=lambda x: (severity_order[x.severity], -x.cost_impact_gb),
        )

        content = ""
        for i, issue in enumerate(sorted_issues, 1):
            commands_preview = chr(10).join(issue.remediation_steps[:10])
            if len(issue.remediation_steps) > 10:
                commands_preview += (
                    f"\\n# ... and {len(issue.remediation_steps) - 10} more commands"
                )

            content += f"""
            <div class="action-card {issue.severity}">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h5 class="mb-2">
                            <span class="me-2">{i}.</span>
                            🚀 {issue.repository} - {issue.issue_type}
                            <span class="priority-badge priority-{issue.severity}">{issue.severity}</span>
                        </h5>
                        <p class="text-muted mb-2">{issue.impact_description}</p>
                    </div>
                    <div class="text-end">
                        <div class="deadline-badge mb-2">Fix in {issue.urgency_days} days</div>
                        <div>
                            <small class="text-muted">Current: {issue.current_value:.1f}MB</small><br>
                            <small class="text-muted">Target: {issue.recommended_value:.1f}MB</small>
                        </div>
                    </div>
                </div>
                
                <div class="expected-result">
                    <i class="fas fa-piggy-bank me-2"></i>
                    <strong>Storage Savings:</strong> {issue.cost_impact_gb:.1f} GB potential reduction
                </div>
                
                <details class="mt-3">
                    <summary class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-terminal me-2"></i>Show Remediation Commands
                    </summary>
                    <div class="code-block mt-2">
                        <pre><code>{commands_preview}</code></pre>
                    </div>
                </details>
            </div>
            """

        return content
