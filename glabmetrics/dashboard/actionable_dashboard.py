#!/usr/bin/env python3
"""Actionable dashboard with concrete recommendations."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from dateutil.parser import parse as parse_date


@dataclass
class ActionItem:
    """Represents a concrete action item with priority and details."""

    title: str
    description: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    impact: str  # 'high', 'medium', 'low'
    effort: str  # 'low', 'medium', 'high'
    affected_repos: List[str]
    action_type: str  # 'ci_cd', 'storage', 'issues', 'code_review', 'security'
    commands: List[str]  # Concrete bash commands
    expected_result: str
    deadline: str  # Suggested completion timeframe


class ActionableDashboard:
    """Generates actionable dashboards with concrete recommendations."""

    def __init__(self, repositories: List[Dict], enhanced_analysis: Dict = None):
        self.repositories = repositories
        self.enhanced_analysis = enhanced_analysis or {}

    def analyze_and_generate_actions(self) -> List[ActionItem]:
        """Analyze data and generate concrete action items."""
        actions = []

        # 1. CRITICAL: Repositories without CI/CD (considering Jenkins integration)
        no_ci_repos = []
        repos_with_external_ci = []

        for r in self.repositories:
            pipeline_count = r.get("pipeline_count", 0)

            # Check if repository has external CI integration (Jenkins, etc.)
            has_external_ci = False

            # Check enhanced analysis for Jenkins webhooks if available
            if self.enhanced_analysis and "ci_metrics" in self.enhanced_analysis:
                ci_metrics = self.enhanced_analysis["ci_metrics"]
                repo_ci_data = next(
                    (
                        m
                        for m in ci_metrics
                        if (m.get("id") if isinstance(m, dict) else m.id) == r.get("id")
                    ),
                    None,
                )
                if repo_ci_data and (
                    repo_ci_data.get("jenkins_integration")
                    if isinstance(repo_ci_data, dict)
                    else repo_ci_data.jenkins_integration
                ):
                    has_external_ci = True
                    repos_with_external_ci.append(r["name"])

            # Only flag as "no CI" if no GitLab pipelines AND no external CI
            if pipeline_count == 0 and not has_external_ci:
                no_ci_repos.append(r)

        if no_ci_repos:
            # Build smart description
            jenkins_note = ""
            if repos_with_external_ci:
                jenkins_note = f" (Note: {len(repos_with_external_ci)} repositories have Jenkins integration and are excluded)"

            actions.append(
                ActionItem(
                    title="Implement CI/CD for repositories without automation",
                    description=f"{len(no_ci_repos)} repositories have no CI/CD automation (GitLab or Jenkins), blocking automated testing and deployment{jenkins_note}",
                    priority="critical",
                    impact="high",
                    effort="medium",
                    affected_repos=[r["name"] for r in no_ci_repos[:10]],
                    action_type="ci_cd",
                    commands=[
                        "# For each repository, add .gitlab-ci.yml:",
                        "cat > .gitlab-ci.yml << 'EOF'",
                        "stages:",
                        "  - test",
                        "  - build",
                        "",
                        "test:",
                        "  stage: test",
                        "  script:",
                        "    - echo 'Running tests...'",
                        "    # Add your test commands here",
                        "",
                        "build:",
                        "  stage: build",
                        "  script:",
                        "    - echo 'Building application...'",
                        "    # Add your build commands here",
                        "EOF",
                        "",
                        "git add .gitlab-ci.yml",
                        "git commit -m 'Add CI/CD pipeline configuration'",
                        "git push",
                    ],
                    expected_result=f"Enable automated testing and deployment for {len(no_ci_repos)} repositories",
                    deadline="2 weeks",
                )
            )

        # 2. HIGH: Large repositories needing Git LFS
        large_repos = [r for r in self.repositories if r.get("size_mb", 0) > 500]
        if large_repos:
            actions.append(
                ActionItem(
                    title="Optimize large repositories with Git LFS",
                    description=f"{len(large_repos)} repositories >500MB cause performance issues and slow clones",
                    priority="high",
                    impact="high",
                    effort="medium",
                    affected_repos=[r["name"] for r in large_repos],
                    action_type="storage",
                    commands=[
                        "# Install Git LFS (if not already installed)",
                        "git lfs install",
                        "",
                        "# Track large file types (adjust patterns as needed)",
                        "git lfs track '*.zip'",
                        "git lfs track '*.tar.gz'",
                        "git lfs track '*.bin'",
                        "git lfs track '*.exe'",
                        "git lfs track '*.dll'",
                        "git lfs track '*.so'",
                        "",
                        "# Track files larger than 100MB",
                        "find . -size +100M -type f | head -10 | while read file; do",
                        '    git lfs track "$file"',
                        "done",
                        "",
                        "git add .gitattributes",
                        "git commit -m 'Add Git LFS tracking for large files'",
                        "git push",
                    ],
                    expected_result="Reduce repository sizes by 60-80%, improve clone performance",
                    deadline="1 month",
                )
            )

        # 3. HIGH: Repositories with many open issues
        high_issue_repos = [
            r for r in self.repositories if r.get("open_issues", 0) > 20
        ]
        if high_issue_repos:
            actions.append(
                ActionItem(
                    title="Triage and resolve high issue backlogs",
                    description=f"{len(high_issue_repos)} repositories have >20 open issues, indicating maintenance debt",
                    priority="high",
                    impact="medium",
                    effort="high",
                    affected_repos=[r["name"] for r in high_issue_repos[:5]],
                    action_type="issues",
                    commands=[
                        "# Use GitLab API to bulk-label stale issues",
                        "export GITLAB_TOKEN='your-token-here'",
                        "export PROJECT_ID='project-id'",
                        "",
                        "# Get issues older than 6 months",
                        "curl --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                        "     'https://gitlab.example.com/api/v4/projects/$PROJECT_ID/issues?state=opened&created_before=2024-01-01' \\",
                        "     | jq '.[].iid' > old_issues.txt",
                        "",
                        "# Label old issues as 'needs-triage'",
                        "while read issue_iid; do",
                        "    curl --request PUT --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                        "         --data 'labels=needs-triage,stale' \\",
                        "         'https://gitlab.example.com/api/v4/projects/$PROJECT_ID/issues/$issue_iid'",
                        "done < old_issues.txt",
                    ],
                    expected_result="Organize issue backlog, identify actionable vs stale issues",
                    deadline="6 weeks",
                )
            )

        # 4. MEDIUM: Repositories with low activity
        cutoff_date = datetime.now() - timedelta(days=90)
        inactive_repos = []

        for repo in self.repositories:
            try:
                last_activity = parse_date(repo.get("last_activity", "2020-01-01"))
                if last_activity.tzinfo is not None:
                    last_activity = last_activity.replace(tzinfo=None)
                if last_activity < cutoff_date:
                    inactive_repos.append(repo)
            except Exception:
                continue

        if inactive_repos:
            actions.append(
                ActionItem(
                    title="Archive or revitalize inactive repositories",
                    description=f"{len(inactive_repos)} repositories inactive >90 days, consuming storage without value",
                    priority="medium",
                    impact="medium",
                    effort="low",
                    affected_repos=[r["name"] for r in inactive_repos[:10]],
                    action_type="storage",
                    commands=[
                        "# Option 1: Archive inactive repositories",
                        "export GITLAB_TOKEN='your-token-here'",
                        "export PROJECT_ID='project-id'",
                        "",
                        "# Archive the repository",
                        "curl --request POST --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                        "     'https://gitlab.example.com/api/v4/projects/$PROJECT_ID/archive'",
                        "",
                        "# Option 2: Add archive notice to README",
                        "echo '# ⚠️ ARCHIVED REPOSITORY' > ARCHIVE_NOTICE.md",
                        "echo 'This repository is no longer actively maintained.' >> ARCHIVE_NOTICE.md",
                        "echo 'Last activity: $(date)' >> ARCHIVE_NOTICE.md",
                        "git add ARCHIVE_NOTICE.md",
                        "git commit -m 'Mark repository as archived'",
                        "git push",
                    ],
                    expected_result="Free up storage, clarify repository status",
                    deadline="2 months",
                )
            )

        # 5. CRITICAL: Repositories with excessive artifacts
        artifact_repos = [
            r for r in self.repositories if r.get("artifacts_size_mb", 0) > 1000
        ]  # >1GB
        if artifact_repos:
            actions.append(
                ActionItem(
                    title="Clean up excessive CI/CD artifacts",
                    description=f"{len(artifact_repos)} repositories have >1GB artifacts, causing storage bloat",
                    priority="critical",
                    impact="high",
                    effort="low",
                    affected_repos=[r["name"] for r in artifact_repos],
                    action_type="storage",
                    commands=[
                        "# Set artifact expiration in .gitlab-ci.yml",
                        "# Add this to your job definitions:",
                        "build:",
                        "  script:",
                        "    - make build",
                        "  artifacts:",
                        "    expire_in: 7 days",
                        "    when: always",
                        "    paths:",
                        "      - build/",
                        "",
                        "# Clean up existing artifacts via API",
                        "export GITLAB_TOKEN='your-token-here'",
                        "export PROJECT_ID='project-id'",
                        "",
                        "# WARNING: This deletes ALL artifacts",
                        "curl --request DELETE --header 'PRIVATE-TOKEN: $GITLAB_TOKEN' \\",
                        "     'https://gitlab.example.com/api/v4/projects/$PROJECT_ID/artifacts'",
                    ],
                    expected_result="Reduce storage usage by 50-90%, improve GitLab performance",
                    deadline="1 week",
                )
            )

        return actions

    def generate_html_dashboard(self, actions: List[ActionItem]) -> str:
        """Generate HTML dashboard with actionable items."""
        # Group actions by priority
        critical_actions = [a for a in actions if a.priority == "critical"]
        high_actions = [a for a in actions if a.priority == "high"]
        medium_actions = [a for a in actions if a.priority == "medium"]

        def generate_action_cards(
            actions: List[ActionItem], priority_class: str
        ) -> str:
            cards = ""
            for i, action in enumerate(actions, 1):
                commands_preview = "\n".join(action.commands[:8])
                if len(action.commands) > 8:
                    commands_preview += (
                        f"\n# ... and {len(action.commands) - 8} more commands"
                    )

                cards += f"""
                <div class="action-card {priority_class}">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h5 class="mb-2">
                                <span class="me-2">{i}.</span>
                                🚀 {action.title}
                                <span class="priority-badge priority-{action.priority}">{action.priority}</span>
                            </h5>
                            <p class="text-muted mb-2">{action.description}</p>
                            <div class="d-flex gap-2 mb-2">
                                <span class="badge bg-info">Impact: {action.impact}</span>
                                <span class="badge bg-warning text-dark">Effort: {action.effort}</span>
                                <span class="badge bg-secondary">Type: {action.action_type}</span>
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="deadline-badge mb-2">⏰ {action.deadline}</div>
                            <div>
                                <small class="text-muted">Affects {len(action.affected_repos)} repos</small>
                            </div>
                        </div>
                    </div>

                    <div class="expected-result">
                        <i class="fas fa-bullseye me-2"></i>
                        <strong>Expected Result:</strong> {action.expected_result}
                    </div>

                    <details class="mt-3">
                        <summary class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-terminal me-2"></i>Show Implementation Commands
                        </summary>
                        <div class="code-block mt-2">
                            <pre><code>{commands_preview}</code></pre>
                        </div>
                    </details>

                    <div class="affected-repos mt-2">
                        <small class="text-muted">
                            <strong>Affected repositories:</strong> {", ".join(action.affected_repos[:5])}
                            {"..." if len(action.affected_repos) > 5 else ""}
                        </small>
                    </div>
                </div>
                """
            return cards

        return f"""
        <div class="alert alert-success mb-4" role="alert">
            <h4 class="alert-heading">🎯 Actionable GitLab Optimization Plan</h4>
            <p class="mb-0">
                <strong>{len(actions)} concrete actions</strong> identified with
                <strong>{len(critical_actions)} critical</strong> and <strong>{len(high_actions)} high priority</strong> items
            </p>
        </div>

        <div class="row mb-4">
            <div class="col-lg-4 col-md-6">
                <div class="card border-danger">
                    <div class="card-body text-center">
                        <div class="display-4 text-danger">{len(critical_actions)}</div>
                        <p class="card-text">Critical Actions</p>
                        <small class="text-muted">Fix immediately</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-4 col-md-6">
                <div class="card border-warning">
                    <div class="card-body text-center">
                        <div class="display-4 text-warning">{len(high_actions)}</div>
                        <p class="card-text">High Priority</p>
                        <small class="text-muted">Fix within 1 month</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-4 col-md-6">
                <div class="card border-info">
                    <div class="card-body text-center">
                        <div class="display-4 text-info">{len(medium_actions)}</div>
                        <p class="card-text">Medium Priority</p>
                        <small class="text-muted">Plan for future</small>
                    </div>
                </div>
            </div>
        </div>

        <h3 class="text-danger mb-3">🚨 CRITICAL ACTIONS (Fix Immediately)</h3>
        {generate_action_cards(critical_actions, 'critical')}

        <h3 class="text-warning mb-3">⚠️ HIGH PRIORITY ACTIONS</h3>
        {generate_action_cards(high_actions, 'high')}

        <h3 class="text-info mb-3">💡 MEDIUM PRIORITY ACTIONS</h3>
        {generate_action_cards(medium_actions, 'medium')}
        """
