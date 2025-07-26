"""Security-focused tests for HTML report generation."""

from datetime import datetime
import pytest

from glabmetrics.report_generator import HTMLReportGenerator
from glabmetrics.analyzer import RepositoryStats, SystemStats


class TestXSSProtection:
    """Test XSS protection and HTML escaping."""

    def test_jinja2_autoescape_enabled(self):
        """Test that Jinja2 autoescape is properly enabled."""
        generator = HTMLReportGenerator()

        # Check that the template environment has autoescape enabled
        assert generator.template.environment.autoescape is True

    def test_comprehensive_xss_protection(self):
        """Test comprehensive XSS protection across different attack vectors."""
        # Create repository with various XSS payloads
        xss_repo = RepositoryStats(
            id=1,
            name='<script>alert("name_xss")</script>',
            path_with_namespace='group/<img src="x" onerror="alert(\'path_xss\')">/malicious',
            size_mb=100.0,
            commit_count=10,
            contributor_count=2,
            last_activity=datetime.now(),
            is_orphaned=False
        )

        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=0.1,
            total_users=1,
            active_users_30d=1,
            total_commits=10,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0,
            optimization_recommendations=[
                'Consider <script>alert("rec_xss")</script> for cleanup'
            ]
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [xss_repo],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(analysis_results)

        # Test that dangerous unescaped content is NOT present
        dangerous_patterns = [
            '<script>alert("name_xss")</script>',
            '<img src="x" onerror="alert(\'path_xss\')"',
            'onerror="alert(\'path_xss\')"',
            '<script>alert("rec_xss")</script>',
            'javascript:',
            'vbscript:',
            'data:text/html',
            'onload="alert(',
            'onerror="alert(',
            'onmouseover="alert(',
            'onclick="alert('
        ]

        for pattern in dangerous_patterns:
            assert pattern not in html_content, f"Found dangerous unescaped pattern: {pattern}"

        # Test that content is properly escaped
        escaped_patterns = [
            '&lt;img',  # <img should be escaped
            'onerror=&#34;',  # quotes should be escaped
            '&gt;',  # > should be escaped
            '&lt;script&gt;'  # <script> should be escaped in recommendations
        ]

        escaped_found = any(pattern in html_content for pattern in escaped_patterns)
        assert escaped_found, "Expected to find at least some properly escaped content"

    def test_json_data_sanitization(self):
        """Test that JSON data marked as 'safe' doesn't contain XSS."""
        # Create data that could potentially end up in JSON
        repo = RepositoryStats(
            id=1,
            name='normal-repo',
            path_with_namespace='group/normal-repo',
            size_mb=100.0,
            commit_count=10,
            contributor_count=2,
            last_activity=datetime.now(),
            is_orphaned=False,
            languages={
                "JavaScript": "50", "Python": "50",
                "HTML</script><script>alert(1)</script>": 0
            }
        )

        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=0.1,
            total_users=1,
            active_users_30d=1,
            total_commits=10,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [repo],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Check that JSON strings don't contain unescaped dangerous content
        json_fields = [
            'storage_breakdown_json',
            'language_distribution_json',
            'fetch_heatmap_json'
        ]

        for field in json_fields:
            json_content = template_data.get(field, '{}')
            assert '<script>' not in json_content, f"Found unescaped script in {field}"
            assert '</script>' not in json_content, f"Found unescaped script in {field}"
            assert 'alert(' not in json_content, f"Found alert function in {field}"

    def test_empty_data_security(self):
        """Test that empty/None data doesn't cause security issues."""
        # Test with completely empty data
        empty_results = {}

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(empty_results)

        # Should generate error report safely
        assert "Analysis Error" in html_content
        # Exclude legitimate scripts
        content_without_legit_scripts = html_content.replace('<script src=', '').replace('</script>', '')
        assert "<script>" not in content_without_legit_scripts

    def test_malicious_recommendations_escaping(self):
        """Test that optimization recommendations with XSS are properly escaped."""
        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=0.1,
            total_users=1,
            active_users_30d=1,
            total_commits=10,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0,
            optimization_recommendations=[
                'Clean up <script>alert("xss")</script> old artifacts',
                'Consider migrating to <img src=x onerror="alert(1)"> Git LFS'
            ]
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(analysis_results)

        # Recommendations should be escaped
        assert '&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;' in html_content
        assert '<script>alert("xss")</script>' not in html_content
        assert 'onerror="alert(1)"' not in html_content


class TestDataValidation:
    """Test data validation and sanitization."""

    def test_template_data_structure_integrity(self):
        """Test that template data structure is always valid."""
        # Test with minimal valid data
        repo = RepositoryStats(
            id=1,
            name='test-repo',
            path_with_namespace='group/test-repo',
            size_mb=100.0,
            commit_count=10,
            contributor_count=2,
            last_activity=datetime.now(),
            is_orphaned=False
        )

        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=0.1,
            total_users=1,
            active_users_30d=1,
            total_commits=10,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [repo],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        template_data = generator._prepare_template_data(analysis_results)

        # Check required fields exist
        required_fields = [
            'system_stats', 'repositories', 'largest_repos', 'most_active_repos',
            'storage_breakdown', 'storage_breakdown_json', 'language_distribution_json',
            'fetch_heatmap_json', 'analysis_timestamp', 'gitlab_version'
        ]

        for field in required_fields:
            assert field in template_data, f"Missing required field: {field}"

        # Check JSON fields are valid JSON strings
        import json
        json_fields = ['storage_breakdown_json', 'language_distribution_json', 'fetch_heatmap_json']
        for field in json_fields:
            try:
                json.loads(template_data[field])
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in field {field}: {template_data[field]}")

    def test_numeric_data_safety(self):
        """Test that numeric data is properly formatted."""
        # Test with extreme numeric values
        repo = RepositoryStats(
            id=1,
            name='extreme-repo',
            path_with_namespace='group/extreme-repo',
            size_mb=999.999,  # Large but reasonable number
            commit_count=0,  # Zero
            contributor_count=1,
            last_activity=datetime.now(),
            is_orphaned=False,
            complexity_score=999.9  # Large but reasonable number
        )

        system_stats = SystemStats(
            total_repositories=1,
            total_size_gb=1.0,  # Reasonable number
            total_users=1,
            active_users_30d=1,
            total_commits=0,
            orphaned_repositories=0,
            repositories_with_lfs=0,
            total_lfs_size_gb=0.0,
            total_artifacts_size_gb=0.0,
            total_packages_size_gb=0.0,
            total_container_registry_size_gb=0.0
        )

        analysis_results = {
            "system_stats": system_stats,
            "repositories": [repo],
            "analysis_timestamp": datetime.now().isoformat(),
            "gitlab_version": "17.2.1-ee",
            "collection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        generator = HTMLReportGenerator()
        html_content = generator.generate_report(analysis_results)

        # Should handle numbers gracefully - look for numeric inf/nan patterns
        import re
        numeric_inf_pattern = r'\b(inf|infinity)\b'
        numeric_nan_pattern = r'\bnan\b'

        assert not re.search(numeric_inf_pattern, html_content, re.IGNORECASE), "Found numeric infinity in HTML"
        assert not re.search(numeric_nan_pattern, html_content, re.IGNORECASE), "Found numeric NaN in HTML"
        assert html_content  # Should generate valid HTML
        assert "999.999" in html_content or "1000.0" in html_content  # Repository size should appear
