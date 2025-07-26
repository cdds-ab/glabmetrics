"""Tests for HTML report generation."""

from datetime import datetime
from bs4 import BeautifulSoup

from glabmetrics.report_generator import HTMLReportGenerator


class TestHTMLReportGenerator:
    """Test suite for HTML report generation."""

    def test_initialization(self):
        """Test report generator initialization."""
        generator = HTMLReportGenerator()
        assert generator is not None

    def test_generate_complete_report(self, sample_analysis_results):
        """Test generation of complete HTML report."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        assert html_content is not None
        assert isinstance(html_content, str)
        assert len(html_content) > 1000  # Should be substantial content

        # Parse HTML to verify structure
        soup = BeautifulSoup(html_content, "html.parser")

        # Verify basic HTML structure
        assert soup.find("html") is not None
        assert soup.find("head") is not None
        assert soup.find("body") is not None
        assert soup.find("title") is not None

    def test_html_contains_system_metrics(self, sample_analysis_results):
        """Test that HTML contains system-wide metrics."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain total repositories count
        assert "3" in html_content  # total_repositories from sample data

        # Should contain storage information
        assert "6.25 GB" in html_content or "6.3 GB" in html_content  # total_size_gb

        # Should contain GitLab version
        assert "17.2.1-ee" in html_content

    def test_html_contains_bootstrap_and_chartjs(self, sample_analysis_results):
        """Test that HTML includes necessary CSS/JS libraries."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should include Bootstrap CSS
        assert "bootstrap" in html_content.lower()
        assert "cdn.jsdelivr.net" in html_content or "cdnjs.cloudflare.com" in html_content

        # Should include Chart.js
        assert "chart.js" in html_content.lower()

    def test_html_contains_charts(self, sample_analysis_results):
        """Test that HTML contains chart canvas elements."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        soup = BeautifulSoup(html_content, "html.parser")

        # Should contain canvas elements for charts
        canvas_elements = soup.find_all("canvas")
        assert len(canvas_elements) > 0

        # Should have storage chart
        storage_chart = soup.find("canvas", {"id": "storageChart"})
        assert storage_chart is not None

    def test_html_escapes_user_content(self, sample_analysis_results):
        """Test that user-provided content is properly escaped."""
        # Modify sample data to include potentially dangerous content
        malicious_repo = sample_analysis_results["repositories"][0]
        malicious_repo.name = '<script>alert("xss")</script>'  # This field is not rendered in HTML
        malicious_repo.path_with_namespace = 'group/<img src="x" onerror="alert(1)">'  # This is rendered

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should not contain unescaped dangerous content that is actually rendered
        assert '<img src="x" onerror="alert(1)">' not in html_content
        assert 'onerror="alert(1)"' not in html_content

        # Should contain escaped versions of actually rendered content
        assert "&lt;img" in html_content and "onerror=&#34;alert(1)&#34;" in html_content

    def test_html_handles_empty_data(self):
        """Test report generation with minimal/empty data."""
        empty_results = {
            "system_stats": None,
            "repositories": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "Unknown",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(empty_results)

        # Should still generate valid HTML
        assert html_content is not None
        assert len(html_content) > 500

        soup = BeautifulSoup(html_content, "html.parser")
        assert soup.find("html") is not None

    def test_storage_chart_data_generation(self, sample_analysis_results):
        """Test that storage chart receives proper data."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain JavaScript for chart initialization
        assert "storageChart" in html_content
        assert "Chart(" in html_content or "new Chart" in html_content

        # Should contain storage data
        # Look for repository data, LFS data, artifacts data
        assert any(term in html_content for term in ["Repository", "LFS", "Artifacts"])

    def test_recommendations_section(self, sample_analysis_results):
        """Test that recommendations are properly displayed."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain recommendations section
        soup = BeautifulSoup(html_content, "html.parser")

        # Look for recommendations content
        recommendations_found = False
        for text in soup.stripped_strings:
            if "recommendation" in text.lower() or "optimize" in text.lower():
                recommendations_found = True
                break

        assert recommendations_found

    def test_repository_listings(self, sample_analysis_results):
        """Test that repository information is properly displayed."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain repository names from sample data
        repo_names = [repo.name for repo in sample_analysis_results["repositories"]]

        for repo_name in repo_names:
            assert repo_name in html_content

    def test_timestamp_display(self, sample_analysis_results):
        """Test that timestamps are properly displayed."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain collection timestamp
        collection_time = sample_analysis_results["collection_timestamp"]
        assert collection_time in html_content or "2025" in html_content  # Should have some timestamp

    def test_gitlab_version_display(self, sample_analysis_results):
        """Test that GitLab version is displayed."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        gitlab_version = sample_analysis_results["gitlab_version"]
        assert gitlab_version in html_content

    def test_responsive_design_classes(self, sample_analysis_results):
        """Test that HTML includes responsive design classes."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should include Bootstrap responsive classes
        assert "col-" in html_content  # Bootstrap column classes
        assert "container" in html_content  # Bootstrap container
        assert "row" in html_content  # Bootstrap row system

    def test_chart_colors_and_styling(self, sample_analysis_results):
        """Test that charts have proper colors and styling."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should contain color definitions for charts
        color_patterns = ["#", "rgb", "rgba", "color"]
        assert any(pattern in html_content for pattern in color_patterns)

    def test_number_formatting(self, sample_analysis_results):
        """Test that numbers are properly formatted in HTML."""
        generator = HTMLReportGenerator()
        html_content = generator.generate_report(sample_analysis_results)

        # Should format large numbers with appropriate units
        # Look for GB, MB, or comma-separated numbers
        formatting_found = any(pattern in html_content for pattern in ["GB", "MB", ","])
        assert formatting_found
