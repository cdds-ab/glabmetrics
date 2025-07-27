"""Smart sampling for representative project selection across departments/groups."""

import re
from collections import defaultdict
from typing import Dict, List, Set

from rich.console import Console
from rich.table import Table

console = Console()


class SmartProjectSampler:
    """Intelligent project sampling to ensure representative coverage across departments."""

    def __init__(self):
        self.department_patterns = {
            # IT/Development departments
            "frontend": [r"frontend", r"ui", r"web", r"react", r"vue", r"angular"],
            "backend": [r"backend", r"api", r"service", r"server"],
            "devops": [
                r"deployment",
                r"infra",
                r"docker",
                r"k8s",
                r"kubernetes",
                r"ansible",
            ],
            "mobile": [r"mobile", r"android", r"ios", r"app"],
            "data": [r"data", r"analytics", r"etl", r"warehouse", r"bi"],
            "security": [r"security", r"auth", r"sec", r"vault"],
            "testing": [r"test", r"qa", r"automation"],
            # Business departments (from GitLab naming patterns)
            "hardware": [
                r"^hw_",
                r"hardware",
                r"embedded",
                r"mcu",
                r"esp32",
                r"firmware",
            ],
            "tools": [r"tool", r"util", r"helper", r"migra", r"script"],
            "legacy": [r"delete", r"old", r"archive", r"deprecated", r"legacy"],
            "research": [r"research", r"poc", r"prototype", r"experiment"],
            "operations": [r"ops", r"monitoring", r"log", r"metric"],
            "documentation": [r"doc", r"wiki", r"guide", r"manual"],
            # Project types by activity
            "active": [],  # Will be determined by last_activity
            "maintenance": [],  # Will be determined by commit patterns
            "archived": [],  # Will be determined by activity age
        }

        self.size_categories = ["small", "medium", "large", "huge"]
        self.activity_categories = ["hot", "warm", "cold", "frozen"]

    def categorize_projects(self, projects: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize projects by department, size, and activity patterns."""
        categorized = defaultdict(list)

        console.print(
            "[cyan]🔍 Analyzing project patterns for smart sampling...[/cyan]"
        )

        for project in projects:
            project_name = project.get("name", "").lower()
            project_path = project.get("path_with_namespace", "").lower()
            project_size = (
                project.get("statistics", {}).get("repository_size", 0) or 0
            ) / (
                1024 * 1024
            )  # MB

            # Determine department/category
            departments = self._classify_by_department(project_name, project_path)
            size_category = self._classify_by_size(project_size)
            activity_category = self._classify_by_activity(project)

            # Add metadata to project
            project["_analysis"] = {
                "departments": departments,
                "size_category": size_category,
                "activity_category": activity_category,
                "size_mb": project_size,
            }

            # Add to appropriate categories
            for dept in departments:
                categorized[dept].append(project)
            categorized[size_category].append(project)
            categorized[activity_category].append(project)

        return dict(categorized)

    def _classify_by_department(self, name: str, path: str) -> List[str]:
        """Classify project by department based on name patterns."""
        departments = []
        combined_text = f"{name} {path}"

        for dept, patterns in self.department_patterns.items():
            if dept in ["active", "maintenance", "archived"]:
                continue  # These are handled by activity classification

            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    departments.append(dept)
                    break

        # Default classification if no specific department found
        if not departments:
            if any(
                word in combined_text for word in ["lib", "shared", "common", "core"]
            ):
                departments.append("libraries")
            elif any(word in combined_text for word in ["client", "customer", "user"]):
                departments.append("client-facing")
            else:
                departments.append("general")

        return departments

    def _classify_by_size(self, size_mb: float) -> str:
        """Classify project by repository size."""
        if size_mb < 1:
            return "small"
        elif size_mb < 50:
            return "medium"
        elif size_mb < 500:
            return "large"
        else:
            return "huge"

    def _classify_by_activity(self, project: Dict) -> str:
        """Classify project by activity level."""
        from datetime import datetime

        from dateutil.parser import parse as parse_date

        try:
            if project.get("last_activity_at"):
                last_activity = parse_date(project["last_activity_at"])
                if last_activity.tzinfo is not None:
                    last_activity = last_activity.replace(tzinfo=None)

                days_ago = (datetime.now() - last_activity).days

                if days_ago <= 7:
                    return "hot"
                elif days_ago <= 30:
                    return "warm"
                elif days_ago <= 180:
                    return "cold"
                else:
                    return "frozen"
            else:
                return "frozen"
        except Exception:
            return "unknown"

    def sample_projects(
        self, projects: List[Dict], target_count: int = 50, min_per_category: int = 2
    ) -> List[Dict]:
        """Sample projects to ensure representative coverage across departments."""
        categorized = self.categorize_projects(projects)

        # Print categorization summary
        self._print_categorization_summary(categorized, len(projects))

        # Sample strategy: ensure representation across key dimensions
        sampled = []
        used_project_ids = set()

        # Priority 1: Ensure each department has minimum representation
        department_samples = self._sample_by_departments(
            categorized, min_per_category, used_project_ids
        )
        sampled.extend(department_samples)

        # Priority 2: Ensure size diversity
        size_samples = self._sample_by_sizes(
            categorized, min_per_category, used_project_ids
        )
        sampled.extend(size_samples)

        # Priority 3: Ensure activity diversity
        activity_samples = self._sample_by_activity(
            categorized, min_per_category, used_project_ids
        )
        sampled.extend(activity_samples)

        # Priority 4: Fill remaining slots with random selection from underrepresented categories
        remaining_slots = target_count - len(sampled)
        if remaining_slots > 0:
            additional_samples = self._fill_remaining_slots(
                projects, remaining_slots, used_project_ids
            )
            sampled.extend(additional_samples)

        # Remove duplicates and limit to target count
        unique_sampled = []
        seen_ids = set()
        for project in sampled:
            if project["id"] not in seen_ids:
                unique_sampled.append(project)
                seen_ids.add(project["id"])
                if len(unique_sampled) >= target_count:
                    break

        self._print_sampling_results(unique_sampled, target_count)
        return unique_sampled

    def _sample_by_departments(
        self, categorized: Dict, min_per_category: int, used_ids: Set
    ) -> List[Dict]:
        """Sample projects ensuring departmental representation."""
        samples = []
        dept_priorities = [
            "frontend",
            "backend",
            "hardware",
            "devops",
            "tools",
            "mobile",
            "data",
        ]

        for dept in dept_priorities:
            if dept in categorized:
                dept_projects = [
                    p for p in categorized[dept] if p["id"] not in used_ids
                ]
                # Sort by activity (most recent first) and size (larger first) for better representation
                dept_projects.sort(
                    key=lambda x: (
                        x["_analysis"]["activity_category"] == "hot",
                        x["_analysis"]["activity_category"] == "warm",
                        x["_analysis"]["size_mb"],
                    ),
                    reverse=True,
                )

                selected = dept_projects[:min_per_category]
                samples.extend(selected)
                for p in selected:
                    used_ids.add(p["id"])

        return samples

    def _sample_by_sizes(
        self, categorized: Dict, min_per_category: int, used_ids: Set
    ) -> List[Dict]:
        """Sample projects ensuring size diversity."""
        samples = []
        for size_cat in self.size_categories:
            if size_cat in categorized:
                size_projects = [
                    p for p in categorized[size_cat] if p["id"] not in used_ids
                ]
                # Prefer more active projects
                size_projects.sort(
                    key=lambda x: x["_analysis"]["activity_category"]
                    in ["hot", "warm"],
                    reverse=True,
                )

                selected = size_projects[:min_per_category]
                samples.extend(selected)
                for p in selected:
                    used_ids.add(p["id"])

        return samples

    def _sample_by_activity(
        self, categorized: Dict, min_per_category: int, used_ids: Set
    ) -> List[Dict]:
        """Sample projects ensuring activity diversity."""
        samples = []
        for activity_cat in self.activity_categories:
            if activity_cat in categorized:
                activity_projects = [
                    p for p in categorized[activity_cat] if p["id"] not in used_ids
                ]
                # Prefer larger projects for better analysis
                activity_projects.sort(
                    key=lambda x: x["_analysis"]["size_mb"], reverse=True
                )

                selected = activity_projects[:min_per_category]
                samples.extend(selected)
                for p in selected:
                    used_ids.add(p["id"])

        return samples

    def _fill_remaining_slots(
        self, projects: List[Dict], remaining_slots: int, used_ids: Set
    ) -> List[Dict]:
        """Fill remaining slots with diverse selection."""
        available = [p for p in projects if p["id"] not in used_ids]
        # Sort by a combination of activity and size for good representation
        available.sort(
            key=lambda x: (
                x.get("_analysis", {}).get("activity_category", "unknown")
                in ["hot", "warm"],
                x.get("_analysis", {}).get("size_mb", 0),
            ),
            reverse=True,
        )

        return available[:remaining_slots]

    def _print_categorization_summary(self, categorized: Dict, total_projects: int):
        """Print summary of project categorization."""
        console.print(
            f"\n[bold cyan]📊 Project Categorization Summary ({total_projects} total projects)[/bold cyan]"
        )

        # Department distribution
        dept_table = Table(
            title="Department Distribution",
            show_header=True,
            header_style="bold magenta",
        )
        dept_table.add_column("Department", style="cyan", width=15)
        dept_table.add_column("Count", style="green", width=8)
        dept_table.add_column("Examples", style="dim", width=40)

        departments = {
            k: v
            for k, v in categorized.items()
            if k not in self.size_categories + self.activity_categories
        }

        for dept, projects in sorted(
            departments.items(), key=lambda x: len(x[1]), reverse=True
        ):
            examples = ", ".join([p["name"][:20] for p in projects[:3]])
            dept_table.add_row(dept, str(len(projects)), examples)

        console.print(dept_table)

    def _print_sampling_results(self, sampled: List[Dict], target_count: int):
        """Print results of sampling process."""
        console.print(
            f"\n[bold green]✅ Smart Sampling Complete: {len(sampled)}/{target_count} projects selected[/bold green]"
        )

        # Show distribution of sampled projects
        dept_counts = defaultdict(int)
        size_counts = defaultdict(int)
        activity_counts = defaultdict(int)

        for project in sampled:
            analysis = project.get("_analysis", {})
            for dept in analysis.get("departments", []):
                dept_counts[dept] += 1
            size_counts[analysis.get("size_category", "unknown")] += 1
            activity_counts[analysis.get("activity_category", "unknown")] += 1

        console.print("[dim]Department coverage:[/dim]")
        for dept, count in sorted(
            dept_counts.items(), key=lambda x: x[1], reverse=True
        ):
            console.print(f"  • {dept}: {count} projects")

        console.print(f"[dim]Size distribution: {dict(size_counts)}[/dim]")
        console.print(f"[dim]Activity distribution: {dict(activity_counts)}[/dim]")
