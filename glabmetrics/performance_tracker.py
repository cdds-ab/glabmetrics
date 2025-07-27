"""Performance tracking for GitLab data collection."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class APIBlockTiming:
    """Timing information for an API block."""

    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: float = 0.0
    api_calls_count: int = 0
    failed_calls: int = 0
    total_data_points: int = 0
    error_messages: List[str] = field(default_factory=list)


@dataclass
class CollectionPerformanceStats:
    """Complete performance statistics for data collection."""

    total_duration: float = 0.0
    start_timestamp: str = ""
    end_timestamp: str = ""
    total_repositories: int = 0
    total_api_calls: int = 0
    total_failed_calls: int = 0
    api_blocks: List[APIBlockTiming] = field(default_factory=list)
    slowest_blocks: List[APIBlockTiming] = field(default_factory=list)
    error_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    # Enhanced KPI Analysis Performance
    enhanced_kpi_duration: float = 0.0
    enhanced_kpi_enabled: bool = False
    kpi_analysis_times: Dict[str, float] = field(default_factory=dict)
    parallel_speedup_factor: float = 1.0


class PerformanceTracker:
    """Tracks performance metrics during GitLab data collection."""

    def __init__(self):
        self.current_blocks: Dict[str, APIBlockTiming] = {}
        self.completed_blocks: List[APIBlockTiming] = []
        self.total_start_time: Optional[float] = None
        self.total_api_calls = 0
        self.total_failed_calls = 0
        self.repository_count = 0

    def start_collection(self) -> None:
        """Start tracking the overall collection process."""
        self.total_start_time = time.time()

    def start_api_block(self, block_name: str) -> None:
        """Start timing an API block."""
        if block_name in self.current_blocks:
            # Block already running, ignore
            return

        self.current_blocks[block_name] = APIBlockTiming(
            name=block_name, start_time=time.time()
        )

    def end_api_block(self, block_name: str, data_points: int = 0) -> None:
        """End timing an API block."""
        if block_name not in self.current_blocks:
            return

        block = self.current_blocks[block_name]
        block.end_time = time.time()
        block.duration = block.end_time - block.start_time
        block.total_data_points = data_points

        self.completed_blocks.append(block)
        del self.current_blocks[block_name]

    def add_api_call(
        self, block_name: str, success: bool = True, error_message: str = ""
    ) -> None:
        """Record an API call within a block."""
        self.total_api_calls += 1

        if block_name in self.current_blocks:
            block = self.current_blocks[block_name]
            block.api_calls_count += 1

            if not success:
                block.failed_calls += 1
                self.total_failed_calls += 1
                if error_message:
                    block.error_messages.append(error_message)

    def set_repository_count(self, count: int) -> None:
        """Set the total number of repositories processed."""
        self.repository_count = count

    def track_enhanced_kpi_analysis(
        self,
        kpi_times: Dict[str, float],
        total_duration: float,
        parallel_enabled: bool = True,
    ) -> None:
        """Track Enhanced KPI Analysis performance metrics."""
        self.enhanced_kpi_duration = total_duration
        self.enhanced_kpi_enabled = True
        self.kpi_analysis_times = kpi_times.copy()

        # Calculate speedup factor (theoretical vs actual)
        if parallel_enabled and kpi_times:
            sequential_time = sum(kpi_times.values())
            self.parallel_speedup_factor = (
                sequential_time / total_duration if total_duration > 0 else 1.0
            )
        else:
            self.parallel_speedup_factor = 1.0

    def get_performance_stats(self) -> CollectionPerformanceStats:
        """Generate comprehensive performance statistics."""
        if self.total_start_time is None:
            return CollectionPerformanceStats()

        total_duration = time.time() - self.total_start_time

        # Sort blocks by duration (slowest first)
        slowest_blocks = sorted(
            self.completed_blocks, key=lambda x: x.duration, reverse=True
        )[:5]

        # Analyze error patterns
        error_summary = defaultdict(int)
        for block in self.completed_blocks:
            for error in block.error_messages:
                # Extract error type from message
                if "403" in error:
                    error_summary["Permission Denied (403)"] += 1
                elif "404" in error:
                    error_summary["Not Found (404)"] += 1
                elif "500" in error:
                    error_summary["Server Error (500)"] += 1
                elif "timeout" in error.lower():
                    error_summary["Timeout"] += 1
                else:
                    error_summary["Other Errors"] += 1

        # Generate recommendations
        recommendations = self._generate_performance_recommendations(
            slowest_blocks, error_summary
        )

        return CollectionPerformanceStats(
            total_duration=total_duration,
            start_timestamp=datetime.fromtimestamp(self.total_start_time).isoformat(),
            end_timestamp=datetime.now().isoformat(),
            total_repositories=self.repository_count,
            total_api_calls=self.total_api_calls,
            total_failed_calls=self.total_failed_calls,
            api_blocks=self.completed_blocks.copy(),
            slowest_blocks=slowest_blocks,
            error_summary=dict(error_summary),
            recommendations=recommendations,
            # Enhanced KPI Analysis Performance
            enhanced_kpi_duration=getattr(self, "enhanced_kpi_duration", 0.0),
            enhanced_kpi_enabled=getattr(self, "enhanced_kpi_enabled", False),
            kpi_analysis_times=getattr(self, "kpi_analysis_times", {}),
            parallel_speedup_factor=getattr(self, "parallel_speedup_factor", 1.0),
        )

    def _generate_performance_recommendations(
        self, slowest_blocks: List[APIBlockTiming], error_summary: Dict[str, int]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Analyze slowest blocks
        if slowest_blocks:
            slowest = slowest_blocks[0]
            if slowest.duration > 60:  # More than 1 minute
                recommendations.append(
                    f"'{slowest.name}' took {slowest.duration:.1f} seconds. "
                    f"Consider using --skip-binary-scan or optimizing this operation."
                )

        # Analyze error rates
        total_errors = sum(error_summary.values())
        if total_errors > 0:
            error_rate = (total_errors / self.total_api_calls) * 100
            if error_rate > 10:
                recommendations.append(
                    f"High error rate: {error_rate:.1f}% of API calls failed. "
                    f"Check GitLab instance health and token permissions."
                )

        # Analyze specific error types
        if error_summary.get("Permission Denied (403)", 0) > 10:
            recommendations.append(
                "Many permission errors detected. Some GitLab features (packages, registry) "
                "may not be available with current token permissions."
            )

        if error_summary.get("Server Error (500)", 0) > 5:
            recommendations.append(
                "Server errors detected. GitLab instance may be under load. "
                "Consider running collection during off-peak hours."
            )

        # Performance recommendations
        if self.total_api_calls > 1000:
            recommendations.append(
                f"Made {self.total_api_calls} API calls. For faster subsequent runs, "
                f"use cached data without --refresh-data flag."
            )

        # Enhanced KPI Analysis recommendations
        if getattr(self, "enhanced_kpi_enabled", False):
            kpi_duration = getattr(self, "enhanced_kpi_duration", 0.0)
            speedup = getattr(self, "parallel_speedup_factor", 1.0)

            if speedup > 4.0:
                recommendations.append(
                    f"Enhanced KPI Analysis achieved {speedup:.1f}x speedup through parallelization "
                    f"({kpi_duration:.1f}s vs {kpi_duration * speedup:.1f}s sequential)."
                )
            elif kpi_duration > 60:
                recommendations.append(
                    f"Enhanced KPI Analysis took {kpi_duration:.1f}s. "
                    f"Consider using incremental updates or selective analysis."
                )

        return recommendations

    def print_live_stats(self) -> None:
        """Print current performance statistics (for verbose mode)."""
        if not self.completed_blocks:
            return

        print("\n=== Performance Statistics ===")
        print(f"Total API Calls: {self.total_api_calls}")
        print(f"Failed Calls: {self.total_failed_calls}")
        print(f"Repositories Processed: {self.repository_count}")

        print("\nCompleted API Blocks:")
        for block in sorted(
            self.completed_blocks, key=lambda x: x.duration, reverse=True
        ):
            print(
                f"  {block.name}: {block.duration:.1f}s ({block.api_calls_count} calls)"
            )

        if self.current_blocks:
            print("\nCurrently Running:")
            for name, block in self.current_blocks.items():
                elapsed = time.time() - block.start_time
                print(f"  {name}: {elapsed:.1f}s (ongoing)")

        # Enhanced KPI Analysis stats
        if getattr(self, "enhanced_kpi_enabled", False):
            print("\n=== Enhanced KPI Analysis Performance ===")
            kpi_duration = getattr(self, "enhanced_kpi_duration", 0.0)
            speedup = getattr(self, "parallel_speedup_factor", 1.0)
            kpi_times = getattr(self, "kpi_analysis_times", {})

            print(f"Total KPI Analysis Time: {kpi_duration:.1f}s")
            print(f"Parallel Speedup Factor: {speedup:.1f}x")

            if kpi_times:
                print("\nIndividual KPI Analysis Times:")
                for analysis, duration in sorted(
                    kpi_times.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"  {analysis.upper()}: {duration:.1f}s")

                estimated_sequential = sum(kpi_times.values())
                print(f"\nEstimated Sequential Time: {estimated_sequential:.1f}s")
                print(
                    f"Time Saved by Parallelization: {estimated_sequential - kpi_duration:.1f}s"
                )

        print("=" * 50)
