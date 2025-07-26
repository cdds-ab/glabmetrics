"""HTML report generator for GitLab statistics."""

from typing import Dict, Any
from datetime import datetime
from jinja2 import Template, Environment
import json


class HTMLReportGenerator:
    """Generates HTML reports from GitLab analysis data."""

    def __init__(self):
        self.template = self._get_html_template()

    def generate_report(self, analysis_data: Dict[str, Any]) -> str:
        """Generate complete HTML report."""
        if not analysis_data:
            return self._generate_error_report("No analysis data available")

        # Prepare data for template
        template_data = self._prepare_template_data(analysis_data)

        # Render template
        return self.template.render(**template_data)

    def _prepare_template_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for HTML template."""
        system_stats = analysis_data.get("system_stats")
        repositories = analysis_data.get("repositories", [])

        # Handle missing system_stats
        if not system_stats:
            return self._get_empty_template_data(analysis_data)

        # Convert dataclass to dict for template
        system_dict = {
            "total_repositories": system_stats.total_repositories,
            "total_size_gb": round(system_stats.total_size_gb, 2),
            "total_commits": system_stats.total_commits,
            "orphaned_repositories": system_stats.orphaned_repositories,
            "repositories_with_lfs": system_stats.repositories_with_lfs,
            "total_lfs_size_gb": round(system_stats.total_lfs_size_gb, 2),
            "total_artifacts_size_gb": round(system_stats.total_artifacts_size_gb, 2),
            "total_packages_size_gb": round(system_stats.total_packages_size_gb, 2),
            "total_container_registry_size_gb": round(system_stats.total_container_registry_size_gb, 2),
            "optimization_recommendations": system_stats.optimization_recommendations,
            "avg_complexity_score": round(system_stats.avg_complexity_score, 1),
            "avg_health_score": round(system_stats.avg_health_score, 1),
            "pipeline_success_rate": round(system_stats.pipeline_success_rate, 1),
            "language_distribution": system_stats.language_distribution,
            "default_branch_stats": system_stats.default_branch_stats,
            "fetch_heatmap_data": system_stats.fetch_heatmap_data,
        }

        # Prepare repository data
        repo_data = []
        for repo in repositories:
            repo_dict = {
                "name": repo.name,
                "path_with_namespace": repo.path_with_namespace,
                "size_mb": round(repo.size_mb, 2),
                "commit_count": repo.commit_count,
                "contributor_count": repo.contributor_count,
                "last_activity": (
                    repo.last_activity.strftime("%Y-%m-%d") if repo.last_activity > datetime.min else "Never"
                ),
                "is_orphaned": repo.is_orphaned,
                "pipeline_count": repo.pipeline_count,
                "open_mrs": repo.open_mrs,
                "open_issues": repo.open_issues,
                "lfs_size_mb": round(repo.lfs_size_mb, 2),
                "artifacts_size_mb": round(repo.artifacts_size_mb, 2),
                "packages_size_mb": round(repo.packages_size_mb, 2),
                "container_registry_size_mb": round(repo.container_registry_size_mb, 2),
                "binary_files_count": len(repo.binary_files),
                "languages": repo.languages,
                "complexity_score": round(repo.complexity_score, 1),
                "health_score": round(repo.health_score, 1),
                "hotness_score": round(repo.hotness_score, 1),
                "maintenance_score": round(repo.maintenance_score, 1),
                "language_diversity": repo.language_diversity,
                "commit_frequency": round(repo.commit_frequency, 3),
                "default_branch": repo.default_branch,
                "pipeline_success_rate": round(repo.pipeline_success_rate, 1),
                "avg_pipeline_duration": (round(repo.avg_pipeline_duration, 1) if repo.avg_pipeline_duration else 0),
            }
            repo_data.append(repo_dict)

        # Sort repositories for different views
        largest_repos = sorted(repo_data, key=lambda x: x["size_mb"], reverse=True)[:10]
        most_active_repos = sorted(repo_data, key=lambda x: x["commit_count"], reverse=True)[:10]
        orphaned_repos = [r for r in repo_data if r["is_orphaned"]]
        lfs_repos = [r for r in repo_data if r["lfs_size_mb"] > 0]
        binary_heavy_repos = [r for r in repo_data if r["binary_files_count"] > 0 and r["lfs_size_mb"] == 0]

        # New enhanced views
        most_complex_repos = sorted(repo_data, key=lambda x: x["complexity_score"], reverse=True)[:10]
        healthiest_repos = sorted(repo_data, key=lambda x: x["health_score"], reverse=True)[:10]
        hottest_repos = sorted(repo_data, key=lambda x: x["hotness_score"], reverse=True)[:10]
        lowest_health_repos = sorted(repo_data, key=lambda x: x["health_score"])[:10]

        # Calculate percentages for pie charts
        # Only include categories with meaningful data
        storage_breakdown = {}

        if system_dict["total_size_gb"] > 0:
            storage_breakdown["Repository Code"] = system_dict["total_size_gb"]
        if system_dict["total_lfs_size_gb"] > 0:
            storage_breakdown["LFS Objects"] = system_dict["total_lfs_size_gb"]
        if system_dict["total_artifacts_size_gb"] > 0:
            storage_breakdown["CI/CD Artifacts"] = system_dict["total_artifacts_size_gb"]
        if system_dict["total_packages_size_gb"] > 0:
            storage_breakdown["Packages"] = system_dict["total_packages_size_gb"]
        if system_dict["total_container_registry_size_gb"] > 0:
            storage_breakdown["Container Images"] = system_dict["total_container_registry_size_gb"]

        # If we have no detailed breakdown, create repository-based categories
        if len(storage_breakdown) <= 1:
            # Alternative breakdown by repository size categories
            large_repos = [r for r in repo_data if r["size_mb"] > 100]
            medium_repos = [r for r in repo_data if 10 <= r["size_mb"] <= 100]
            small_repos = [r for r in repo_data if r["size_mb"] < 10]

            large_size = sum(r["size_mb"] for r in large_repos) / 1024
            medium_size = sum(r["size_mb"] for r in medium_repos) / 1024
            small_size = sum(r["size_mb"] for r in small_repos) / 1024

            storage_breakdown = {
                f"Large Repositories ({len(large_repos)})": large_size,
                f"Medium Repositories ({len(medium_repos)})": medium_size,
                f"Small Repositories ({len(small_repos)})": small_size,
            }

            # Remove zero categories
            storage_breakdown = {k: v for k, v in storage_breakdown.items() if v > 0}

        return {
            "system_stats": system_dict,
            "repositories": repo_data,
            "largest_repos": largest_repos,
            "most_active_repos": most_active_repos,
            "orphaned_repos": orphaned_repos,
            "lfs_repos": lfs_repos,
            "binary_heavy_repos": binary_heavy_repos,
            "most_complex_repos": most_complex_repos,
            "healthiest_repos": healthiest_repos,
            "hottest_repos": hottest_repos,
            "lowest_health_repos": lowest_health_repos,
            "storage_breakdown": storage_breakdown,
            "storage_breakdown_json": json.dumps(storage_breakdown),
            "language_distribution_json": json.dumps(system_dict["language_distribution"]),
            "fetch_heatmap_json": json.dumps(system_dict["fetch_heatmap_data"]),
            "analysis_timestamp": analysis_data.get("analysis_timestamp", datetime.now().isoformat()),
            "gitlab_version": analysis_data.get("gitlab_version", "Unknown"),
            "collection_timestamp": analysis_data.get("collection_timestamp", ""),
            "total_storage_gb": sum(storage_breakdown.values()),
        }

    def _generate_error_report(self, error_message: str) -> str:
        """Generate error report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitLab Analysis - Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h4>Analysis Error</h4>
                    <p>{error_message}</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_empty_template_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template data for empty/missing system stats."""
        return {
            "system_stats": {
                "total_repositories": 0,
                "total_size_gb": 0.0,
                "total_commits": 0,
                "orphaned_repositories": 0,
                "repositories_with_lfs": 0,
                "total_lfs_size_gb": 0.0,
                "total_artifacts_size_gb": 0.0,
                "total_packages_size_gb": 0.0,
                "total_container_registry_size_gb": 0.0,
                "optimization_recommendations": [],
                "avg_complexity_score": 0.0,
                "avg_health_score": 0.0,
                "pipeline_success_rate": 0.0,
                "language_distribution": {},
                "default_branch_stats": {},
                "fetch_heatmap_data": {},
            },
            "repositories": [],
            "largest_repos": [],
            "most_active_repos": [],
            "orphaned_repos": [],
            "lfs_repos": [],
            "binary_heavy_repos": [],
            "most_complex_repos": [],
            "healthiest_repos": [],
            "hottest_repos": [],
            "lowest_health_repos": [],
            "storage_breakdown": {},
            "storage_breakdown_json": "{}",
            "language_distribution_json": "{}",
            "fetch_heatmap_json": "{}",
            "analysis_timestamp": analysis_data.get("analysis_timestamp", ""),
            "gitlab_version": analysis_data.get("gitlab_version", "Unknown"),
            "collection_timestamp": analysis_data.get("collection_timestamp", ""),
            "total_storage_gb": 0.0,
        }

    def _get_html_template(self) -> Template:
        """Get the HTML template."""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitLab Instance Analysis Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card { transition: transform 0.2s; }
        .metric-card:hover { transform: translateY(-2px); }
        .orphaned { background-color: #fff3cd; border-left: 4px solid #ffc107; }
        .critical { background-color: #f8d7da; border-left: 4px solid #dc3545; }
        .warning { background-color: #d1ecf1; border-left: 4px solid #0dcaf0; }
        .chart-container { position: relative; height: 400px; margin: 20px 0; }
        .recommendation {
            background-color: #d4edda; border: 1px solid #c3e6cb;
            border-radius: 0.375rem; padding: 1rem; margin: 0.5rem 0;
        }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <div class="row bg-primary text-white py-4 mb-4">
            <div class="col">
                <h1 class="display-4">GitLab Instance Analysis</h1>
                <p class="lead">Comprehensive analysis and optimization recommendations</p>
                <small>Generated on: {{ analysis_timestamp }}</small>
            </div>
        </div>

        <!-- Key Metrics Overview -->
        <div class="row mb-4">
            <div class="col">
                <h2>System Overview</h2>
                <div class="stats-grid">
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <h3 class="text-primary">{{ system_stats.total_repositories }}</h3>
                            <p class="card-text">Total Repositories</p>
                        </div>
                    </div>
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <h3 class="text-info">{{ system_stats.total_size_gb }} GB</h3>
                            <p class="card-text">Total Storage</p>
                        </div>
                    </div>
                    <div class="card metric-card">
                        <div class="card-body text-center">
                            <h3 class="text-success">{{ "{:,}".format(system_stats.total_commits) }}</h3>
                            <p class="card-text">Total Commits</p>
                        </div>
                    </div>
                    <div class="card metric-card {% if system_stats.orphaned_repositories > 0 %}warning{% endif %}">
                        <div class="card-body text-center">
                            <h3 class="text-warning">{{ system_stats.orphaned_repositories }}</h3>
                            <p class="card-text">Orphaned Repositories</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Storage Breakdown -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3>Storage Distribution</h3>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="storageChart"></canvas>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">
                                <strong>Total Storage:</strong> {{ total_storage_gb | round(2) }} GB
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3>Storage Details</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Repository Data</span>
                                <strong>{{ system_stats.total_size_gb }} GB</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Git LFS Objects</span>
                                <strong>{{ system_stats.total_lfs_size_gb }} GB</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>CI/CD Artifacts</span>
                                <strong>{{ system_stats.total_artifacts_size_gb }} GB</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Packages</span>
                                <strong>{{ system_stats.total_packages_size_gb }} GB</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Container Registry</span>
                                <strong>{{ system_stats.total_container_registry_size_gb }} GB</strong>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Optimization Recommendations -->
        {% if system_stats.optimization_recommendations %}
        <div class="row mb-4">
            <div class="col">
                <div class="card border-success">
                    <div class="card-header bg-success text-white">
                        <h3><i class="bi bi-lightbulb"></i> Optimization Recommendations</h3>
                    </div>
                    <div class="card-body">
                        {% for recommendation in system_stats.optimization_recommendations %}
                        <div class="recommendation">
                            <i class="bi bi-check-circle text-success"></i>
                            {{ recommendation }}
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Critical Issues -->
        {% if orphaned_repos or binary_heavy_repos %}
        <div class="row mb-4">
            <div class="col">
                <h2 class="text-danger">Critical Issues Requiring Attention</h2>
            </div>
        </div>

        {% if orphaned_repos %}
        <div class="row mb-4">
            <div class="col">
                <div class="card border-warning">
                    <div class="card-header bg-warning">
                        <h4>⚠️ Orphaned Repositories ({{ orphaned_repos | length }})</h4>
                        <small>No activity in the last 6 months</small>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size (MB)</th>
                                        <th>Last Activity</th>
                                        <th>Total Commits</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in orphaned_repos[:20] %}
                                    <tr class="orphaned">
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.size_mb }}</td>
                                        <td>{{ repo.last_activity }}</td>
                                        <td>{{ repo.commit_count }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% if orphaned_repos | length > 20 %}
                        <p class="text-muted">... and {{ orphaned_repos | length - 20 }} more repositories</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        {% if binary_heavy_repos %}
        <div class="row mb-4">
            <div class="col">
                <div class="card border-info">
                    <div class="card-header bg-info text-white">
                        <h4>📦 Repositories with Binary Files (Not Using LFS)</h4>
                        <small>{{ binary_heavy_repos | length }} repositories could benefit from Git LFS</small>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size (MB)</th>
                                        <th>Binary Files</th>
                                        <th>Recommendation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in binary_heavy_repos[:15] %}
                                    <tr class="warning">
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.size_mb }}</td>
                                        <td>{{ repo.binary_files_count }}</td>
                                        <td><span class="badge bg-info">Migrate to LFS</span></td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        {% endif %}

        <!-- Repository Analysis -->
        <div class="row mb-4">
            <div class="col">
                <h2>Repository Analysis</h2>
            </div>
        </div>

        <!-- Largest Repositories -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4>🏆 Largest Repositories</h4>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size (MB)</th>
                                        <th>Commits</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in largest_repos %}
                                    <tr>
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.size_mb }}</td>
                                        <td>{{ repo.commit_count }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Most Active Repositories -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4>🚀 Most Active Repositories</h4>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Commits</th>
                                        <th>Contributors</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in most_active_repos %}
                                    <tr>
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.commit_count }}</td>
                                        <td>{{ repo.contributor_count }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- LFS Usage -->
        {% if lfs_repos %}
        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        <h4>📁 Git LFS Usage</h4>
                        <small>{{ lfs_repos | length }} repositories using Git LFS</small>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>LFS Size (MB)</th>
                                        <th>Repository Size (MB)</th>
                                        <th>LFS Ratio</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in lfs_repos[:15] %}
                                    <tr>
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.lfs_size_mb }}</td>
                                        <td>{{ repo.size_mb }}</td>
                                        <td>
                                            {% set ratio = (repo.lfs_size_mb / (repo.size_mb + repo.lfs_size_mb) * 100) | round(1) %}
                                            <span class="badge bg-success">{{ ratio }}%</span>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- All Repositories Table -->
        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        <h4>📊 All Repositories Overview</h4>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover" id="repositoriesTable">
                                <thead>
                                    <tr>
                                        <th>Repository</th>
                                        <th>Size (MB)</th>
                                        <th>Commits</th>
                                        <th>Contributors</th>
                                        <th>Last Activity</th>
                                        <th>Pipelines</th>
                                        <th>Open MRs</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for repo in repositories %}
                                    <tr {% if repo.is_orphaned %}class="orphaned"{% endif %}>
                                        <td>{{ repo.path_with_namespace }}</td>
                                        <td>{{ repo.size_mb }}</td>
                                        <td>{{ repo.commit_count }}</td>
                                        <td>{{ repo.contributor_count }}</td>
                                        <td>{{ repo.last_activity }}</td>
                                        <td>{{ repo.pipeline_count }}</td>
                                        <td>{{ repo.open_mrs }}</td>
                                        <td>
                                            {% if repo.is_orphaned %}
                                                <span class="badge bg-warning">Orphaned</span>
                                            {% elif repo.binary_files_count > 0 and repo.lfs_size_mb == 0 %}
                                                <span class="badge bg-info">Needs LFS</span>
                                            {% else %}
                                                <span class="badge bg-success">Active</span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="row">
            <div class="col text-center py-4 text-muted">
                <p>GitLab Statistics Analyzer - Generated on {{ analysis_timestamp }}</p>
                <p><small>GitLab Version: {{ gitlab_version }} | This report provides read-only analysis of your GitLab instance for optimization purposes.</small></p>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Storage breakdown pie chart
        const storageData = {{ storage_breakdown_json | safe }};
        const ctx = document.getElementById('storageChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(storageData),
                datasets: [{
                    data: Object.values(storageData),
                    backgroundColor: [
                        '#0d6efd',
                        '#6f42c1',
                        '#fd7e14',
                        '#20c997',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return context.label + ': ' + value.toFixed(2) + ' GB (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });

        // Add search functionality to repositories table
        function filterTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('repositoriesTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    tr[i].style.display = txtValue.toUpperCase().indexOf(filter) > -1 ? '' : 'none';
                }
            }
        }
    </script>
</body>
</html>
        """
        env = Environment(autoescape=True)
        return env.from_string(template_content)
