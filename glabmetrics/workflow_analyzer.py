"""Advanced workflow analysis for issues and merge requests."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from dateutil.parser import parse as parse_date

from .gitlab_client import GitLabClient


@dataclass
class IssueMetrics:
    """Detailed metrics for issue management."""

    total_issues: int = 0
    open_issues: int = 0
    closed_issues: int = 0

    # Aging analysis
    avg_resolution_days: float = 0.0
    median_resolution_days: float = 0.0
    issues_over_30_days: int = 0
    issues_over_90_days: int = 0
    oldest_open_issue_days: int = 0

    # Priority/Label analysis
    priority_distribution: Dict[str, int] = field(default_factory=dict)
    label_distribution: Dict[str, int] = field(default_factory=dict)

    # Activity patterns
    issues_created_last_30d: int = 0
    issues_closed_last_30d: int = 0
    avg_comments_per_issue: float = 0.0

    # Quality indicators
    issues_without_labels: int = 0
    issues_without_assignee: int = 0
    stale_issues: int = 0  # No activity in 60+ days


@dataclass
class MergeRequestMetrics:
    """Detailed metrics for merge request workflow."""

    total_mrs: int = 0
    open_mrs: int = 0
    merged_mrs: int = 0
    closed_mrs: int = 0

    # Review efficiency
    avg_review_time_hours: float = 0.0
    median_review_time_hours: float = 0.0
    avg_time_to_merge_days: float = 0.0

    # Review quality
    avg_discussions_per_mr: float = 0.0
    avg_commits_per_mr: float = 0.0
    mrs_with_approvals: int = 0

    # Workflow patterns
    mrs_created_last_30d: int = 0
    mrs_merged_last_30d: int = 0
    draft_mrs: int = 0

    # Bottlenecks
    mrs_waiting_review: int = 0
    mrs_with_conflicts: int = 0
    long_running_mrs: int = 0  # Open > 14 days


@dataclass
class WorkflowHealthScore:
    """Overall workflow health assessment."""

    issue_management_score: float = 0.0  # 0-100
    mr_efficiency_score: float = 0.0  # 0-100
    collaboration_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # 0-100

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    # Key insights
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


class AdvancedWorkflowAnalyzer:
    """Advanced analysis of GitLab workflow patterns and efficiency."""

    def __init__(self, client: GitLabClient):
        self.client = client

    def analyze_project_workflow(
        self, project_id: int, project_name: str
    ) -> Tuple[IssueMetrics, MergeRequestMetrics, WorkflowHealthScore]:
        """Perform comprehensive workflow analysis for a project."""

        # Get comprehensive data
        issues = self._get_detailed_issues(project_id)
        merge_requests = self._get_detailed_merge_requests(project_id)

        # Analyze each component
        issue_metrics = self._analyze_issues(issues)
        mr_metrics = self._analyze_merge_requests(merge_requests)
        health_score = self._calculate_workflow_health(
            issue_metrics, mr_metrics, project_name
        )

        return issue_metrics, mr_metrics, health_score

    def _get_detailed_issues(self, project_id: int) -> List[Dict]:
        """Get comprehensive issue data with discussions and notes."""
        try:
            # Get issues with detailed information
            issues = self.client.get_project_issues(
                project_id, state="all", per_page=100
            )

            # Enrich with additional data for sample of issues
            enriched_issues = []
            for i, issue in enumerate(issues):
                if i < 20:  # Detailed analysis for first 20 issues to avoid API limits
                    try:
                        # Get issue notes/comments
                        notes = self.client.get_issue_notes(project_id, issue["iid"])
                        issue["_notes"] = notes
                        issue["_comment_count"] = len(notes)
                    except Exception:
                        issue["_notes"] = []
                        issue["_comment_count"] = 0
                else:
                    issue["_notes"] = []
                    issue["_comment_count"] = 0

                enriched_issues.append(issue)

            return enriched_issues
        except Exception as e:
            print(f"Error fetching detailed issues: {e}")
            return []

    def _get_detailed_merge_requests(self, project_id: int) -> List[Dict]:
        """Get comprehensive MR data with discussions and approvals."""
        try:
            # Get MRs with detailed information
            mrs = self.client.get_project_merge_requests(
                project_id, state="all", per_page=100
            )

            # Enrich with additional data for sample of MRs
            enriched_mrs = []
            for i, mr in enumerate(mrs):
                if i < 20:  # Detailed analysis for first 20 MRs to avoid API limits
                    try:
                        # Get MR discussions/notes
                        discussions = self.client.get_mr_discussions(
                            project_id, mr["iid"]
                        )
                        mr["_discussions"] = discussions
                        mr["_discussion_count"] = len(discussions)

                        # Get MR approvals
                        approvals = self.client.get_mr_approvals(project_id, mr["iid"])
                        mr["_approvals"] = approvals
                        mr["_approval_count"] = len(approvals.get("approved_by", []))
                    except Exception:
                        mr["_discussions"] = []
                        mr["_discussion_count"] = 0
                        mr["_approvals"] = {}
                        mr["_approval_count"] = 0
                else:
                    mr["_discussions"] = []
                    mr["_discussion_count"] = 0
                    mr["_approvals"] = {}
                    mr["_approval_count"] = 0

                enriched_mrs.append(mr)

            return enriched_mrs
        except Exception as e:
            print(f"Error fetching detailed MRs: {e}")
            return []

    def _analyze_issues(self, issues: List[Dict]) -> IssueMetrics:
        """Analyze issue management patterns."""
        if not issues:
            return IssueMetrics()

        metrics = IssueMetrics()
        metrics.total_issues = len(issues)

        # Basic counts
        open_issues = [i for i in issues if i["state"] == "opened"]
        closed_issues = [i for i in issues if i["state"] == "closed"]

        metrics.open_issues = len(open_issues)
        metrics.closed_issues = len(closed_issues)

        current_time = datetime.now()
        thirty_days_ago = current_time - timedelta(days=30)

        resolution_times = []
        open_ages = []
        recent_created = 0
        recent_closed = 0
        total_comments = 0

        for issue in issues:
            try:
                created_at = parse_date(issue["created_at"])
                if created_at.tzinfo is not None:
                    created_at = created_at.replace(tzinfo=None)

                # Count recent activity
                if created_at > thirty_days_ago:
                    recent_created += 1

                # Analyze closed issues
                if issue["state"] == "closed" and issue.get("closed_at"):
                    closed_at = parse_date(issue["closed_at"])
                    if closed_at.tzinfo is not None:
                        closed_at = closed_at.replace(tzinfo=None)

                    resolution_days = (closed_at - created_at).days
                    resolution_times.append(resolution_days)

                    if closed_at > thirty_days_ago:
                        recent_closed += 1

                # Analyze open issues
                elif issue["state"] == "opened":
                    age_days = (current_time - created_at).days
                    open_ages.append(age_days)

                    if age_days > 30:
                        metrics.issues_over_30_days += 1
                    if age_days > 90:
                        metrics.issues_over_90_days += 1

                # Quality indicators
                if not issue.get("labels"):
                    metrics.issues_without_labels += 1
                if not issue.get("assignee"):
                    metrics.issues_without_assignee += 1

                # Check for stale issues (no recent activity)
                updated_at = parse_date(issue["updated_at"])
                if updated_at.tzinfo is not None:
                    updated_at = updated_at.replace(tzinfo=None)
                if (current_time - updated_at).days > 60:
                    metrics.stale_issues += 1

                # Comment analysis
                total_comments += issue.get("_comment_count", 0)

                # Label analysis
                for label in issue.get("labels", []):
                    if isinstance(label, str):
                        metrics.label_distribution[label] = (
                            metrics.label_distribution.get(label, 0) + 1
                        )
                    elif isinstance(label, dict) and "name" in label:
                        metrics.label_distribution[label["name"]] = (
                            metrics.label_distribution.get(label["name"], 0) + 1
                        )

            except Exception:
                continue  # Skip problematic issues

        # Calculate averages
        if resolution_times:
            metrics.avg_resolution_days = statistics.mean(resolution_times)
            metrics.median_resolution_days = statistics.median(resolution_times)

        if open_ages:
            metrics.oldest_open_issue_days = max(open_ages)

        metrics.issues_created_last_30d = recent_created
        metrics.issues_closed_last_30d = recent_closed

        if metrics.total_issues > 0:
            metrics.avg_comments_per_issue = total_comments / metrics.total_issues

        return metrics

    def _analyze_merge_requests(self, mrs: List[Dict]) -> MergeRequestMetrics:
        """Analyze merge request workflow patterns."""
        if not mrs:
            return MergeRequestMetrics()

        metrics = MergeRequestMetrics()
        metrics.total_mrs = len(mrs)

        # Basic counts
        open_mrs = [mr for mr in mrs if mr["state"] == "opened"]
        merged_mrs = [mr for mr in mrs if mr["state"] == "merged"]
        closed_mrs = [mr for mr in mrs if mr["state"] == "closed"]

        metrics.open_mrs = len(open_mrs)
        metrics.merged_mrs = len(merged_mrs)
        metrics.closed_mrs = len(closed_mrs)

        current_time = datetime.now()
        thirty_days_ago = current_time - timedelta(days=30)

        review_times = []
        merge_times = []
        recent_created = 0
        recent_merged = 0
        total_discussions = 0
        total_commits = 0
        total_approvals = 0

        for mr in mrs:
            try:
                created_at = parse_date(mr["created_at"])
                if created_at.tzinfo is not None:
                    created_at = created_at.replace(tzinfo=None)

                # Count recent activity
                if created_at > thirty_days_ago:
                    recent_created += 1

                # Analyze merged MRs
                if mr["state"] == "merged" and mr.get("merged_at"):
                    merged_at = parse_date(mr["merged_at"])
                    if merged_at.tzinfo is not None:
                        merged_at = merged_at.replace(tzinfo=None)

                    merge_days = (merged_at - created_at).days
                    merge_times.append(merge_days)

                    if merged_at > thirty_days_ago:
                        recent_merged += 1

                    # Estimate review time (simplified)
                    if mr.get("updated_at"):
                        updated_at = parse_date(mr["updated_at"])
                        if updated_at.tzinfo is not None:
                            updated_at = updated_at.replace(tzinfo=None)
                        review_hours = (updated_at - created_at).total_seconds() / 3600
                        if review_hours > 0:
                            review_times.append(review_hours)

                # Analyze open MRs
                elif mr["state"] == "opened":
                    age_days = (current_time - created_at).days
                    if age_days > 14:
                        metrics.long_running_mrs += 1

                    # Check if waiting for review
                    if not mr.get("assignee_id") and mr.get("author_id"):
                        metrics.mrs_waiting_review += 1

                # Quality metrics
                if mr.get("draft", False) or mr.get("work_in_progress", False):
                    metrics.draft_mrs += 1

                if mr.get("has_conflicts", False):
                    metrics.mrs_with_conflicts += 1

                # Discussion and approval analysis
                total_discussions += mr.get("_discussion_count", 0)
                total_approvals += mr.get("_approval_count", 0)

                # Estimate commits (from user_notes_count as proxy)
                commits_estimate = mr.get("user_notes_count", 1)
                total_commits += commits_estimate

            except Exception:
                continue  # Skip problematic MRs

        # Calculate averages
        if review_times:
            metrics.avg_review_time_hours = statistics.mean(review_times)
            metrics.median_review_time_hours = statistics.median(review_times)

        if merge_times:
            metrics.avg_time_to_merge_days = statistics.mean(merge_times)

        metrics.mrs_created_last_30d = recent_created
        metrics.mrs_merged_last_30d = recent_merged
        metrics.mrs_with_approvals = total_approvals

        if metrics.total_mrs > 0:
            metrics.avg_discussions_per_mr = total_discussions / metrics.total_mrs
            metrics.avg_commits_per_mr = total_commits / metrics.total_mrs

        return metrics

    def _calculate_workflow_health(
        self,
        issue_metrics: IssueMetrics,
        mr_metrics: MergeRequestMetrics,
        project_name: str,
    ) -> WorkflowHealthScore:
        """Calculate overall workflow health score and generate recommendations."""
        health = WorkflowHealthScore()

        # Issue Management Score (0-100)
        issue_score = 100.0
        if issue_metrics.total_issues > 0:
            # Penalize old open issues
            if issue_metrics.issues_over_90_days > 0:
                issue_score -= min(issue_metrics.issues_over_90_days * 10, 40)

            # Penalize stale issues
            stale_ratio = issue_metrics.stale_issues / issue_metrics.total_issues
            issue_score -= stale_ratio * 30

            # Penalize poor issue quality
            unlabeled_ratio = (
                issue_metrics.issues_without_labels / issue_metrics.total_issues
            )
            issue_score -= unlabeled_ratio * 20

            # Bonus for recent activity
            if (
                issue_metrics.issues_closed_last_30d
                > issue_metrics.issues_created_last_30d
            ):
                issue_score += 10

        health.issue_management_score = max(0, min(issue_score, 100))

        # MR Efficiency Score (0-100)
        mr_score = 100.0
        if mr_metrics.total_mrs > 0:
            # Penalize long review times
            if mr_metrics.avg_time_to_merge_days > 7:
                mr_score -= min((mr_metrics.avg_time_to_merge_days - 7) * 5, 30)

            # Penalize long-running MRs
            if mr_metrics.long_running_mrs > 0:
                mr_score -= min(mr_metrics.long_running_mrs * 8, 25)

            # Penalize MRs waiting for review
            waiting_ratio = (
                mr_metrics.mrs_waiting_review / mr_metrics.open_mrs
                if mr_metrics.open_mrs > 0
                else 0
            )
            mr_score -= waiting_ratio * 20

            # Bonus for good discussion/review activity
            if mr_metrics.avg_discussions_per_mr > 2:
                mr_score += 10

        health.mr_efficiency_score = max(0, min(mr_score, 100))

        # Collaboration Score (0-100)
        collab_score = 50.0  # Base score

        # Positive indicators
        if issue_metrics.avg_comments_per_issue > 1:
            collab_score += 20
        if mr_metrics.avg_discussions_per_mr > 1:
            collab_score += 20
        if mr_metrics.mrs_with_approvals > mr_metrics.merged_mrs * 0.5:
            collab_score += 10

        health.collaboration_score = max(0, min(collab_score, 100))

        # Overall Score
        health.overall_score = (
            health.issue_management_score
            + health.mr_efficiency_score
            + health.collaboration_score
        ) / 3

        # Generate recommendations
        health.recommendations = self._generate_recommendations(
            issue_metrics, mr_metrics, health
        )
        health.strengths = self._identify_strengths(issue_metrics, mr_metrics, health)
        health.concerns = self._identify_concerns(issue_metrics, mr_metrics, health)

        return health

    def _generate_recommendations(
        self,
        issue_metrics: IssueMetrics,
        mr_metrics: MergeRequestMetrics,
        health: WorkflowHealthScore,
    ) -> List[str]:
        """Generate actionable recommendations for workflow improvement."""
        recommendations = []

        # Issue management recommendations
        if issue_metrics.issues_over_90_days > 5:
            recommendations.append(
                f"🔍 Review {issue_metrics.issues_over_90_days} issues older than 90 days - consider closing or prioritizing"
            )

        if issue_metrics.stale_issues > issue_metrics.total_issues * 0.3:
            recommendations.append(
                "📝 Implement regular issue triage to reduce stale issues"
            )

        if issue_metrics.issues_without_labels > issue_metrics.total_issues * 0.5:
            recommendations.append(
                "🏷️ Establish issue labeling guidelines to improve categorization"
            )

        # MR workflow recommendations
        if mr_metrics.avg_time_to_merge_days > 14:
            recommendations.append(
                "⚡ Review MR approval process - average merge time is too long"
            )

        if mr_metrics.long_running_mrs > 3:
            recommendations.append("🚨 Address long-running MRs to prevent code drift")

        if mr_metrics.mrs_waiting_review > mr_metrics.open_mrs * 0.5:
            recommendations.append(
                "👥 Assign reviewers more promptly to reduce review bottlenecks"
            )

        # Collaboration recommendations
        if mr_metrics.avg_discussions_per_mr < 1:
            recommendations.append(
                "💬 Encourage more code review discussions for knowledge sharing"
            )

        if health.collaboration_score < 60:
            recommendations.append(
                "🤝 Foster team collaboration through pair programming or code review sessions"
            )

        return recommendations

    def _identify_strengths(
        self,
        issue_metrics: IssueMetrics,
        mr_metrics: MergeRequestMetrics,
        health: WorkflowHealthScore,
    ) -> List[str]:
        """Identify workflow strengths."""
        strengths = []

        if issue_metrics.avg_resolution_days < 7:
            strengths.append("⚡ Fast issue resolution time")

        if mr_metrics.avg_time_to_merge_days < 5:
            strengths.append("🚀 Efficient merge process")

        if mr_metrics.avg_discussions_per_mr > 2:
            strengths.append("💬 Active code review culture")

        if issue_metrics.issues_closed_last_30d > issue_metrics.issues_created_last_30d:
            strengths.append("📈 Positive issue resolution trend")

        if health.overall_score > 80:
            strengths.append("🏆 Excellent overall workflow health")

        return strengths

    def _identify_concerns(
        self,
        issue_metrics: IssueMetrics,
        mr_metrics: MergeRequestMetrics,
        health: WorkflowHealthScore,
    ) -> List[str]:
        """Identify workflow concerns."""
        concerns = []

        if issue_metrics.oldest_open_issue_days > 365:
            concerns.append("⚠️ Very old open issues may indicate process gaps")

        if mr_metrics.mrs_with_conflicts > mr_metrics.open_mrs * 0.3:
            concerns.append("🔀 High number of MRs with conflicts")

        if issue_metrics.stale_issues > issue_metrics.total_issues * 0.4:
            concerns.append("💤 High percentage of stale issues")

        if mr_metrics.draft_mrs > mr_metrics.open_mrs * 0.5:
            concerns.append("📝 Many draft MRs may indicate planning issues")

        if health.overall_score < 50:
            concerns.append("🚨 Workflow health needs attention")

        return concerns
