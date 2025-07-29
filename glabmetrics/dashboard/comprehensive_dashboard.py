#!/usr/bin/env python3
"""Comprehensive dashboard combining all analysis components."""

from typing import Any, Dict, List

from .actionable_dashboard import ActionableDashboard
from .performance_dashboard import PerformanceDashboard


class ComprehensiveDashboard:
    """Combines actionable and performance dashboards into a unified view."""

    def __init__(self, repositories: List[Dict], enhanced_analysis: Dict = None):
        self.repositories = repositories
        self.enhanced_analysis = enhanced_analysis or {}

        # Initialize component dashboards
        self.actionable_dashboard = ActionableDashboard(repositories, enhanced_analysis)
        self.performance_dashboard = PerformanceDashboard(repositories)

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report combining all analyses."""
        # Get actionable items
        action_items = self.actionable_dashboard.analyze_and_generate_actions()

        # Get performance analysis
        performance_report = self.performance_dashboard.generate_performance_report()

        # Combine and prioritize
        return {
            "action_items": action_items,
            "performance_report": performance_report,
            "summary": {
                "total_action_items": len(action_items),
                "critical_actions": len(
                    [a for a in action_items if a.priority == "critical"]
                ),
                "high_actions": len([a for a in action_items if a.priority == "high"]),
                "performance_issues": performance_report["summary"]["total_issues"],
                "critical_performance_issues": performance_report["summary"][
                    "critical_issues"
                ],
                "total_storage_waste_gb": performance_report["summary"][
                    "total_waste_gb"
                ],
                "optimization_potential_percent": performance_report["summary"][
                    "optimization_potential_percent"
                ],
            },
        }

    def generate_html_dashboard(self) -> str:
        """Generate comprehensive HTML dashboard."""
        comprehensive_report = self.generate_comprehensive_report()
        action_items = comprehensive_report["action_items"]
        performance_report = comprehensive_report["performance_report"]
        summary = comprehensive_report["summary"]

        # Generate actionable content
        actionable_content = self.actionable_dashboard.generate_html_dashboard(
            action_items
        )

        # Generate performance content
        performance_content = self.performance_dashboard.generate_html_dashboard(
            performance_report
        )

        return f"""
        <div class="alert alert-primary mb-4" role="alert">
            <h4 class="alert-heading">📊 Comprehensive GitLab Optimization Dashboard</h4>
            <p class="mb-0">
                Complete analysis with <strong>{summary['total_action_items']} actionable items</strong> and 
                <strong>{summary['performance_issues']} performance issues</strong> detected.
                Potential storage savings: <strong>{summary['total_storage_waste_gb']:.1f} GB</strong>
            </p>
        </div>
        
        <div class="row mb-4">
            <div class="col-lg-2 col-md-4 col-sm-6">
                <div class="card border-danger">
                    <div class="card-body text-center p-3">
                        <div class="display-6 text-danger">{summary['critical_actions']}</div>
                        <small class="text-muted">Critical Actions</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6">
                <div class="card border-warning">
                    <div class="card-body text-center p-3">
                        <div class="display-6 text-warning">{summary['high_actions']}</div>
                        <small class="text-muted">High Priority</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6">
                <div class="card border-danger">
                    <div class="card-body text-center p-3">
                        <div class="display-6 text-danger">{summary['critical_performance_issues']}</div>
                        <small class="text-muted">Perf Issues</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="card border-success">
                    <div class="card-body text-center p-3">
                        <div class="display-6 text-success">{summary['total_storage_waste_gb']:.0f} GB</div>
                        <small class="text-muted">Storage Waste</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="card border-info">
                    <div class="card-body text-center p-3">
                        <div class="display-6 text-info">{summary['optimization_potential_percent']:.0f}%</div>
                        <small class="text-muted">Optimization</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Nav tabs -->
        <ul class="nav nav-tabs mb-4" id="comprehensiveTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="actionable-tab" data-bs-toggle="tab" 
                        data-bs-target="#actionable" type="button" role="tab">
                    🎯 Actionable Items
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="performance-tab" data-bs-toggle="tab" 
                        data-bs-target="#performance" type="button" role="tab">
                    ⚡ Performance Issues
                </button>
            </li>
        </ul>
        
        <!-- Tab content -->
        <div class="tab-content" id="comprehensiveTabContent">
            <div class="tab-pane fade show active" id="actionable" role="tabpanel">
                {actionable_content}
            </div>
            <div class="tab-pane fade" id="performance" role="tabpanel">
                <div class="alert alert-warning mb-4" role="alert">
                    <h4 class="alert-heading">🚨 Performance Crisis Detected!</h4>
                    <p class="mb-0">
                        <strong>{performance_report['summary']['total_issues']} performance issues</strong> identified with 
                        <strong>{performance_report['summary']['total_waste_gb']:.1f} GB storage waste</strong> and 
                        <strong>{performance_report['summary']['optimization_potential_percent']:.0f}% optimization potential</strong>
                    </p>
                </div>
                {performance_content}
            </div>
        </div>
        """
