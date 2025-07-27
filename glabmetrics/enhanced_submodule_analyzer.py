"""Enhanced Submodule Network Graph Analyzer - ChatGPT Prompt 5 Implementation"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Set

from rich.console import Console
from rich.table import Table

from .gitlab_client import GitLabClient

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class SubmoduleMetrics:
    """Submodule relationship metrics for a single repository."""

    id: int
    path_with_namespace: str
    has_submodules: bool
    submodules: List[Dict]  # [{name, url, path, commit}]
    is_submodule_of: List[str]  # Projects that use this as submodule
    submodule_depth: int  # How deep in submodule chain
    circular_dependencies: List[str]  # Circular refs detected
    outdated_submodules: List[Dict]  # Submodules with old commits
    gitlab_url: str


@dataclass
class SubmoduleSystemAnalysis:
    """System-wide submodule network analysis results."""

    total_projects: int
    projects_with_submodules: int
    total_submodule_relationships: int
    network_depth: int  # Maximum depth found
    circular_dependencies: List[Dict]
    most_used_submodules: List[Dict]  # [{repo, usage_count}]
    complex_projects: List[Dict]  # Projects with many submodules
    orphaned_submodules: List[str]  # Submodules not used anywhere
    network_graph: Dict[str, List[str]]  # Adjacency list representation
    health_status: str


class EnhancedSubmoduleAnalyzer:
    """Analyzes Git submodule relationships according to ChatGPT Prompt 5."""

    def __init__(self, gitlab_client: GitLabClient):
        self.client = gitlab_client

    def collect_submodule_kpis(self, projects: List[Dict]) -> List[SubmoduleMetrics]:
        """
        ChatGPT Prompt 5 - collect_section:
        For each project gather:
        - id, path_with_namespace
        - .gitmodules content and submodule configurations
        - submodule URLs, paths, and commit references
        """
        console.print("[cyan]🔗 Collecting Submodule Network KPIs...[/cyan]")

        metrics = []
        all_project_paths = {p["path_with_namespace"] for p in projects}

        for i, project in enumerate(projects, 1):
            console.print(
                f"[blue]Processing {project['path_with_namespace']} ({i}/{len(projects)})[/blue]"
            )

            try:
                project_id = project["id"]
                project_path = project["path_with_namespace"]

                # Try to get .gitmodules file
                gitmodules_content = None
                has_submodules = False
                submodules = []

                try:
                    gitmodules_file = self.client.get_repository_file(
                        project_id, ".gitmodules"
                    )
                    if gitmodules_file:
                        gitmodules_content = gitmodules_file.get("content", "")
                        if gitmodules_content:
                            # Decode base64 if needed
                            import base64

                            try:
                                gitmodules_content = base64.b64decode(
                                    gitmodules_content
                                ).decode("utf-8")
                                has_submodules = True
                                submodules = self._parse_gitmodules(gitmodules_content)
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug(f"No .gitmodules found in {project_path}: {e}")

                metrics.append(
                    SubmoduleMetrics(
                        id=project_id,
                        path_with_namespace=project_path,
                        has_submodules=has_submodules,
                        submodules=submodules,
                        is_submodule_of=[],  # Will be filled in second pass
                        submodule_depth=0,  # Will be calculated later
                        circular_dependencies=[],  # Will be detected later
                        outdated_submodules=[],  # Will be analyzed later
                        gitlab_url=self.client.gitlab_url,
                    )
                )

            except Exception as e:
                logger.error(
                    f"Error analyzing submodules for {project['path_with_namespace']}: {e}"
                )
                continue

        # Second pass: Build reverse relationships and detect patterns
        self._build_reverse_relationships(metrics, all_project_paths)
        self._calculate_depths_and_cycles(metrics)

        console.print(
            f"[green]✅ Collected Submodule KPIs for {len(metrics)} projects[/green]"
        )
        return metrics

    def _parse_gitmodules(self, content: str) -> List[Dict]:
        """Parse .gitmodules file content to extract submodule configurations."""
        submodules = []
        current_submodule = {}

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Start of new submodule section
            if line.startswith("[submodule "):
                if current_submodule:
                    submodules.append(current_submodule)

                # Extract submodule name
                match = re.match(r'\[submodule "([^"]+)"\]', line)
                if match:
                    current_submodule = {"name": match.group(1)}
                else:
                    current_submodule = {"name": "unknown"}

            # Parse submodule properties
            elif "=" in line and current_submodule:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "path":
                    current_submodule["path"] = value
                elif key == "url":
                    current_submodule["url"] = value
                elif key == "branch":
                    current_submodule["branch"] = value

        # Add the last submodule
        if current_submodule:
            submodules.append(current_submodule)

        return submodules

    def _build_reverse_relationships(
        self, metrics: List[SubmoduleMetrics], all_project_paths: Set[str]
    ):
        """Build reverse submodule relationships (which projects use this as submodule)."""
        path_to_metric = {m.path_with_namespace: m for m in metrics}

        for metric in metrics:
            for submodule in metric.submodules:
                submodule_url = submodule.get("url", "")

                # Try to match submodule URL to internal projects
                for project_path in all_project_paths:
                    if project_path in submodule_url or submodule_url.endswith(
                        f"/{project_path}.git"
                    ):
                        if project_path in path_to_metric:
                            target_metric = path_to_metric[project_path]
                            if (
                                metric.path_with_namespace
                                not in target_metric.is_submodule_of
                            ):
                                target_metric.is_submodule_of.append(
                                    metric.path_with_namespace
                                )

    def _calculate_depths_and_cycles(self, metrics: List[SubmoduleMetrics]):
        """Calculate submodule depths and detect circular dependencies."""
        path_to_metric = {m.path_with_namespace: m for m in metrics}

        # Calculate depths using DFS
        visited = set()
        visiting = set()  # For cycle detection

        def calculate_depth(project_path: str, path: List[str] = None) -> int:
            if path is None:
                path = []

            if project_path in visiting:
                # Circular dependency detected
                cycle_start = path.index(project_path)
                cycle = path[cycle_start:] + [project_path]

                # Record cycle for all involved projects
                for p in cycle[:-1]:  # Exclude duplicate at end
                    if p in path_to_metric:
                        cycle_str = " → ".join(cycle)
                        if cycle_str not in path_to_metric[p].circular_dependencies:
                            path_to_metric[p].circular_dependencies.append(cycle_str)

                return float("inf")  # Infinite depth due to cycle

            if project_path in visited:
                return path_to_metric.get(
                    project_path,
                    SubmoduleMetrics(0, project_path, False, [], [], 0, [], [], ""),
                ).submodule_depth

            visiting.add(project_path)
            path.append(project_path)

            max_submodule_depth = 0
            if project_path in path_to_metric:
                metric = path_to_metric[project_path]
                for submodule in metric.submodules:
                    submodule_url = submodule.get("url", "")

                    # Find matching internal project
                    for other_path in path_to_metric:
                        if other_path in submodule_url or submodule_url.endswith(
                            f"/{other_path}.git"
                        ):
                            sub_depth = calculate_depth(other_path, path[:])
                            if sub_depth != float("inf"):
                                max_submodule_depth = max(
                                    max_submodule_depth, sub_depth + 1
                                )
                            break

            visiting.remove(project_path)
            path.pop()
            visited.add(project_path)

            if project_path in path_to_metric:
                path_to_metric[project_path].submodule_depth = max_submodule_depth

            return max_submodule_depth

        # Calculate depths for all projects
        for metric in metrics:
            if metric.path_with_namespace not in visited:
                calculate_depth(metric.path_with_namespace)

    def generate_submodule_analysis(
        self, submodule_metrics: List[SubmoduleMetrics]
    ) -> SubmoduleSystemAnalysis:
        """
        ChatGPT Prompt 5 - analyse_section:
        Build network graph and analyze submodule relationships, dependencies, and complexity.
        """
        console.print("[cyan]🔍 Analyzing Submodule Network...[/cyan]")

        if not submodule_metrics:
            return SubmoduleSystemAnalysis(
                total_projects=0,
                projects_with_submodules=0,
                total_submodule_relationships=0,
                network_depth=0,
                circular_dependencies=[],
                most_used_submodules=[],
                complex_projects=[],
                orphaned_submodules=[],
                network_graph={},
                health_status="No data",
            )

        projects_with_submodules = [m for m in submodule_metrics if m.has_submodules]
        total_relationships = sum(len(m.submodules) for m in projects_with_submodules)

        # Calculate maximum network depth
        max_depth = max(
            (
                m.submodule_depth
                for m in submodule_metrics
                if m.submodule_depth != float("inf")
            ),
            default=0,
        )

        # Collect all circular dependencies
        all_circular_deps = []
        for metric in submodule_metrics:
            for cycle in metric.circular_dependencies:
                if cycle not in [cd["cycle"] for cd in all_circular_deps]:
                    all_circular_deps.append(
                        {
                            "cycle": cycle,
                            "projects_involved": cycle.split(" → ")[:-1],
                        }  # Remove duplicate at end
                    )

        # Find most used submodules
        submodule_usage = {}
        for metric in submodule_metrics:
            for used_by in metric.is_submodule_of:
                if metric.path_with_namespace not in submodule_usage:
                    submodule_usage[metric.path_with_namespace] = []
                submodule_usage[metric.path_with_namespace].append(used_by)

        most_used = sorted(
            [
                {"repo": repo, "usage_count": len(users), "used_by": users}
                for repo, users in submodule_usage.items()
            ],
            key=lambda x: x["usage_count"],
            reverse=True,
        )[:5]

        # Find complex projects (many submodules)
        complex_projects = sorted(
            [
                {
                    "repo": m.path_with_namespace,
                    "submodule_count": len(m.submodules),
                    "depth": (
                        m.submodule_depth
                        if m.submodule_depth != float("inf")
                        else "Circular"
                    ),
                    "has_cycles": len(m.circular_dependencies) > 0,
                }
                for m in projects_with_submodules
                if len(m.submodules) > 2
            ],
            key=lambda x: x["submodule_count"],
            reverse=True,
        )

        # Find orphaned submodules (have .gitmodules but not used by anyone)
        orphaned = [
            m.path_with_namespace
            for m in projects_with_submodules
            if not m.is_submodule_of
        ]

        # Build network graph (adjacency list)
        network_graph = {}
        for metric in submodule_metrics:
            network_graph[metric.path_with_namespace] = []
            for submodule in metric.submodules:
                submodule_url = submodule.get("url", "")
                # Try to match to internal projects
                for other_metric in submodule_metrics:
                    if (
                        other_metric.path_with_namespace in submodule_url
                        or submodule_url.endswith(
                            f"/{other_metric.path_with_namespace}.git"
                        )
                    ):
                        network_graph[metric.path_with_namespace].append(
                            other_metric.path_with_namespace
                        )
                        break

        # Health status
        cycle_percentage = (
            (len(all_circular_deps) / len(submodule_metrics) * 100)
            if submodule_metrics
            else 0
        )
        complexity_percentage = (
            (len(complex_projects) / len(submodule_metrics) * 100)
            if submodule_metrics
            else 0
        )

        if cycle_percentage == 0 and complexity_percentage < 20:
            health_status = "🟢 Excellent"
        elif cycle_percentage < 5 and complexity_percentage < 40:
            health_status = "🟡 Good"
        elif cycle_percentage < 15 or complexity_percentage < 60:
            health_status = "🟠 Needs Attention"
        else:
            health_status = "🔴 Critical"

        return SubmoduleSystemAnalysis(
            total_projects=len(submodule_metrics),
            projects_with_submodules=len(projects_with_submodules),
            total_submodule_relationships=total_relationships,
            network_depth=max_depth,
            circular_dependencies=all_circular_deps,
            most_used_submodules=most_used,
            complex_projects=complex_projects,
            orphaned_submodules=orphaned,
            network_graph=network_graph,
            health_status=health_status,
        )

    def generate_markdown_report(
        self,
        analysis: SubmoduleSystemAnalysis,
        submodule_metrics: List[SubmoduleMetrics],
    ) -> str:
        """Generate comprehensive markdown report for Submodule Network KPIs."""
        report = []

        # Header
        report.append("## 🔗 Submodule Network Graph Analysis")
        report.append("")

        # System Overview
        submodule_adoption = (
            (analysis.projects_with_submodules / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )
        report.append("### System Overview")
        report.append(f"- **Total Projects:** {analysis.total_projects}")
        report.append(
            f"- **Projects with Submodules:** {analysis.projects_with_submodules} ({submodule_adoption:.1f}%)"
        )
        report.append(
            f"- **Total Submodule Relationships:** {analysis.total_submodule_relationships}"
        )
        report.append(f"- **Maximum Network Depth:** {analysis.network_depth}")
        report.append(
            f"- **Circular Dependencies:** {len(analysis.circular_dependencies)} detected"
        )
        report.append(f"- **System Health:** {analysis.health_status}")
        report.append("")

        # Circular Dependencies
        if analysis.circular_dependencies:
            report.append("### 🔄 Circular Dependencies")
            report.append(
                "**⚠️ Warning: Circular dependencies can cause build and update issues**"
            )
            report.append("")
            for i, cycle_info in enumerate(analysis.circular_dependencies, 1):
                report.append(f"{i}. **{cycle_info['cycle']}**")
                report.append(
                    f"   - Projects involved: {', '.join(cycle_info['projects_involved'])}"
                )
            report.append("")

        # Most Used Submodules
        if analysis.most_used_submodules:
            report.append("### 🏆 Most Used Submodules")
            report.append("| Repository | Usage Count | Used By |")
            report.append("|------------|-------------|---------|")
            for submodule in analysis.most_used_submodules:
                used_by = ", ".join(submodule["used_by"][:3])
                if len(submodule["used_by"]) > 3:
                    used_by += f" (+{len(submodule['used_by'])-3} more)"
                report.append(
                    f"| [{submodule['repo']}]({submodule_metrics[0].gitlab_url}/{submodule['repo']}) | {submodule['usage_count']} | {used_by} |"
                )
            report.append("")

        # Complex Projects
        if analysis.complex_projects:
            report.append("### 🧩 Complex Projects (Multiple Submodules)")
            report.append("| Repository | Submodules | Depth | Has Cycles |")
            report.append("|------------|------------|-------|------------|")
            for project in analysis.complex_projects:
                cycles = "🔄 Yes" if project["has_cycles"] else "✅ No"
                report.append(
                    f"| [{project['repo']}]({submodule_metrics[0].gitlab_url}/{project['repo']}) | {project['submodule_count']} | {project['depth']} | {cycles} |"
                )
            report.append("")

        # Orphaned Submodules
        if analysis.orphaned_submodules:
            report.append("### 🏝️ Orphaned Submodules")
            report.append(
                "*Projects that have submodules but are not used as submodules by others*"
            )
            report.append("")
            for orphan in analysis.orphaned_submodules:
                report.append(
                    f"- [{orphan}]({submodule_metrics[0].gitlab_url}/{orphan})"
                )
            report.append("")

        # Network Graph Visualization
        if analysis.network_graph:
            report.append("### 🕸️ Network Graph")
            report.append("```mermaid")
            report.append("graph TD")

            # Generate mermaid graph syntax
            node_ids = {}
            counter = 1

            # Create node IDs
            for repo in analysis.network_graph:
                if repo not in node_ids:
                    node_ids[repo] = f"N{counter}"
                    counter += 1

            # Add nodes with labels
            for repo, node_id in node_ids.items():
                clean_name = repo.split("/")[-1]  # Just the repo name
                report.append(f'    {node_id}["{clean_name}"]')

            # Add edges
            for repo, dependencies in analysis.network_graph.items():
                if dependencies:
                    repo_id = node_ids[repo]
                    for dep in dependencies:
                        if dep in node_ids:
                            dep_id = node_ids[dep]
                            report.append(f"    {repo_id} --> {dep_id}")

            report.append("```")
            report.append("")

        # Repository Details
        report.append("### Repository Submodule Details")
        report.append("")
        report.append(
            "| Repo | Has Submodules | Submodule Count | Used As Submodule | Depth | Cycles |"
        )
        report.append(
            "|------|----------------|-----------------|-------------------|-------|--------|"
        )

        # Sort by submodule count (descending)
        sorted_metrics = sorted(
            submodule_metrics, key=lambda x: len(x.submodules), reverse=True
        )

        for metric in sorted_metrics:
            has_submodules = "✅" if metric.has_submodules else "❌"
            submodule_count = len(metric.submodules)
            used_count = len(metric.is_submodule_of)
            used_as = f"✅ ({used_count})" if used_count > 0 else "❌"
            depth = (
                str(metric.submodule_depth)
                if metric.submodule_depth != float("inf")
                else "∞"
            )
            cycles = "🔄" if metric.circular_dependencies else "✅"

            report.append(
                f"| [{metric.path_with_namespace}]({metric.gitlab_url}/{metric.path_with_namespace}) | {has_submodules} | {submodule_count} | {used_as} | {depth} | {cycles} |"
            )

        return "\n".join(report)

    def display_results_table(self, analysis: SubmoduleSystemAnalysis):
        """Display results in a Rich table format."""
        # System Overview Table
        overview_table = Table(
            title="🔗 Submodule Network System Overview", show_header=True
        )
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        submodule_adoption = (
            (analysis.projects_with_submodules / analysis.total_projects * 100)
            if analysis.total_projects > 0
            else 0
        )

        overview_table.add_row("Total Projects", str(analysis.total_projects))
        overview_table.add_row(
            "Projects with Submodules",
            f"{analysis.projects_with_submodules} ({submodule_adoption:.1f}%)",
        )
        overview_table.add_row(
            "Total Relationships", str(analysis.total_submodule_relationships)
        )
        overview_table.add_row("Maximum Depth", str(analysis.network_depth))
        overview_table.add_row(
            "Circular Dependencies", str(len(analysis.circular_dependencies))
        )
        overview_table.add_row("System Health", analysis.health_status)

        console.print(overview_table)
        console.print()

        # Most Used Submodules
        if analysis.most_used_submodules:
            usage_table = Table(title="🏆 Most Used Submodules", show_header=True)
            usage_table.add_column("Repository", style="cyan")
            usage_table.add_column("Usage Count", style="green")
            usage_table.add_column("Used By", style="yellow")

            for submodule in analysis.most_used_submodules[:5]:
                used_by = ", ".join(submodule["used_by"][:2])
                if len(submodule["used_by"]) > 2:
                    used_by += f" (+{len(submodule['used_by'])-2})"

                usage_table.add_row(
                    submodule["repo"], str(submodule["usage_count"]), used_by
                )

            console.print(usage_table)
