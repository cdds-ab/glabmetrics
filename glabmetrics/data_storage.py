"""Data storage and serialization utilities."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict
import logging

from .analyzer import RepositoryStats
from .performance_tracker import CollectionPerformanceStats

logger = logging.getLogger(__name__)


class GitLabDataStorage:
    """Handles loading and saving of GitLab analysis data."""

    def __init__(self, data_file: str = "gitlab_data.json"):
        self.data_file = Path(data_file)

    def save_data(
        self,
        repositories: List[RepositoryStats],
        analysis_timestamp: datetime,
        performance_stats: Optional[CollectionPerformanceStats] = None,
    ) -> None:
        """Save repository data to JSON file."""
        try:
            # Convert dataclasses to dictionaries
            repo_dicts = []
            for repo in repositories:
                # Custom serialization to handle complex objects
                repo_dict = self._serialize_repository_stats(repo)
                repo_dicts.append(repo_dict)

            data = {
                "repositories": repo_dicts,
                "analysis_timestamp": analysis_timestamp.isoformat(),
                "version": "1.0",
            }

            # Add performance statistics if available
            if performance_stats:
                data["performance_stats"] = asdict(performance_stats)

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Data saved to {self.data_file}")

        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise

    def _serialize_repository_stats(self, repo: RepositoryStats) -> Dict[str, Any]:
        """Serialize RepositoryStats to JSON-compatible dict."""
        # Always use manual serialization to avoid issues with complex objects
        return {
            "id": repo.id,
            "name": repo.name,
            "path_with_namespace": repo.path_with_namespace,
            "size_mb": repo.size_mb,
            "commit_count": repo.commit_count,
            "contributor_count": repo.contributor_count,
            "last_activity": (repo.last_activity.isoformat() if repo.last_activity > datetime.min else None),
            "is_orphaned": repo.is_orphaned,
            "languages": (dict(repo.languages) if hasattr(repo.languages, "items") else repo.languages),
            "storage_stats": (dict(repo.storage_stats) if hasattr(repo.storage_stats, "items") else repo.storage_stats),
            "pipeline_count": repo.pipeline_count,
            "open_mrs": repo.open_mrs,
            "open_issues": repo.open_issues,
            "lfs_size_mb": repo.lfs_size_mb,
            "artifacts_size_mb": repo.artifacts_size_mb,
            "packages_size_mb": repo.packages_size_mb,
            "container_registry_size_mb": repo.container_registry_size_mb,
            "binary_files": list(repo.binary_files),
            "complexity_score": repo.complexity_score,
            "health_score": repo.health_score,
            "hotness_score": repo.hotness_score,
            "maintenance_score": repo.maintenance_score,
            "language_diversity": repo.language_diversity,
            "commit_frequency": repo.commit_frequency,
            "default_branch": repo.default_branch,
            "pipeline_success_rate": repo.pipeline_success_rate,
            "avg_pipeline_duration": repo.avg_pipeline_duration,
            "expired_artifacts_count": repo.expired_artifacts_count,
            "old_artifacts_size_mb": repo.old_artifacts_size_mb,
            "gitlab_version": repo.gitlab_version,
            "job_artifacts_details": list(repo.job_artifacts_details),
            "lfs_objects_details": list(repo.lfs_objects_details),
            "pipeline_details": self._serialize_complex_dict(repo.pipeline_details),
            "fetch_activity": self._serialize_complex_dict(repo.fetch_activity),
        }

    def _serialize_complex_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert complex objects like defaultdict to regular dict."""
        if obj is None:
            return {}

        if hasattr(obj, "items"):
            # Convert defaultdict or other dict-like objects
            result = {}
            for key, value in obj.items():
                if hasattr(value, "items"):
                    # Nested dict-like object
                    result[key] = dict(value)
                elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
                    # Convert lists, sets, etc.
                    result[key] = list(value)
                else:
                    result[key] = value
            return result
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            # Convert lists, sets, etc.
            return list(obj)
        else:
            return obj if obj is not None else {}

    def load_data(self) -> tuple[List[RepositoryStats], datetime]:
        """Load repository data from JSON file."""
        try:
            if not self.data_file.exists():
                raise FileNotFoundError(f"Data file {self.data_file} not found. Run with --refresh-data first.")

            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert dictionaries back to dataclasses
            repositories = []
            for repo_dict in data["repositories"]:
                try:
                    # Convert ISO string back to datetime
                    if repo_dict.get("last_activity"):
                        repo_dict["last_activity"] = datetime.fromisoformat(repo_dict["last_activity"])
                    else:
                        repo_dict["last_activity"] = datetime.min

                    # Handle missing fields for backward compatibility
                    repo_dict.setdefault("complexity_score", 0.0)
                    repo_dict.setdefault("health_score", 0.0)
                    repo_dict.setdefault("hotness_score", 0.0)
                    repo_dict.setdefault("maintenance_score", 0.0)
                    repo_dict.setdefault("language_diversity", 0)
                    repo_dict.setdefault("commit_frequency", 0.0)
                    repo_dict.setdefault("default_branch", "")
                    repo_dict.setdefault("pipeline_success_rate", 0.0)
                    repo_dict.setdefault("avg_pipeline_duration", 0.0)
                    repo_dict.setdefault("pipeline_details", {})
                    repo_dict.setdefault("job_artifacts_details", [])
                    repo_dict.setdefault("lfs_objects_details", [])
                    repo_dict.setdefault("expired_artifacts_count", 0)
                    repo_dict.setdefault("old_artifacts_size_mb", 0.0)
                    repo_dict.setdefault("gitlab_version", "")
                    repo_dict.setdefault("fetch_activity", {})

                    repo = RepositoryStats(**repo_dict)
                    repositories.append(repo)

                except Exception as e:
                    logger.warning(f"Error deserializing repository {repo_dict.get('name', 'unknown')}: {e}")
                    continue

            analysis_timestamp = datetime.fromisoformat(data["analysis_timestamp"])

            logger.info(f"Data loaded from {self.data_file} (timestamp: {analysis_timestamp})")
            return repositories, analysis_timestamp

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def data_exists(self) -> bool:
        """Check if data file exists."""
        return self.data_file.exists()

    def get_data_age(self) -> str:
        """Get age of data file."""
        if not self.data_file.exists():
            return "No data file found"

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            analysis_time = datetime.fromisoformat(data["analysis_timestamp"])
            age = datetime.now() - analysis_time

            if age.days > 0:
                return f"{age.days} days old"
            elif age.seconds > 3600:
                hours = age.seconds // 3600
                return f"{hours} hours old"
            else:
                minutes = age.seconds // 60
                return f"{minutes} minutes old"

        except Exception:
            return "Unknown age"


def serialize_analysis_results(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize analysis results for JSON storage."""
    if not analysis_results:
        return {}

    # Handle SystemStats
    system_stats = analysis_results.get("system_stats")
    if system_stats:
        system_dict = asdict(system_stats)

        # Convert nested RepositoryStats objects to dicts
        if "repositories_by_size" in system_dict:
            system_dict["repositories_by_size"] = [
                {
                    **asdict(repo),
                    "last_activity": (repo.last_activity.isoformat() if repo.last_activity > datetime.min else None),
                }
                for repo in system_stats.repositories_by_size
            ]

        if "most_active_repositories" in system_dict:
            system_dict["most_active_repositories"] = [
                {
                    **asdict(repo),
                    "last_activity": (repo.last_activity.isoformat() if repo.last_activity > datetime.min else None),
                }
                for repo in system_stats.most_active_repositories
            ]

        analysis_results["system_stats"] = system_dict

    return analysis_results


def deserialize_analysis_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize analysis results from JSON storage."""
    if not data:
        return {}

    # Handle SystemStats reconstruction - we'll do this in the analyzer
    # since SystemStats is generated from repositories data
    return data
