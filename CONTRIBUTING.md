# Contributing to glabmetrics

Thank you for your interest in contributing to glabmetrics! This document provides guidelines and instructions for contributing to the project.

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/gitlab-stats-analyzer.git
cd gitlab-stats-analyzer

# Add upstream remote
git remote add upstream https://github.com/original/gitlab-stats-analyzer.git
```

### 2. Development Setup

```bash
# Install PDM if not already installed
curl -sSL https://pdm-project.org/install-pdm.py | python3 -

# Install dependencies
pdm install -d

# Install pre-commit hooks
pdm run pre-commit-install

# Verify setup by running tests
pdm run test
```

### 3. Development Workflow

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests and linting
pdm run test
pdm run lint
pdm run format-check

# Commit using conventional commits
pdm run commit

# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## 📝 Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **flake8**: Linting and style checking
- **isort**: Import sorting
- **mypy**: Type checking (optional but encouraged)

```bash
# Format code
pdm run format

# Check formatting
pdm run format-check

# Run linting
pdm run lint
```

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) for consistent commit messages:

```bash
# Use commitizen for guided commit messages
pdm run commit

# Or manually follow the format:
# <type>(<scope>): <description>
#
# [optional body]
#
# [optional footer(s)]
```

#### Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks, dependencies
- `ci`: CI/CD changes
- `perf`: Performance improvements

#### Examples

```
feat(analyzer): add repository complexity scoring algorithm
fix(storage): resolve serialization error with defaultdict objects
docs(readme): update installation instructions for Docker
test(client): add unit tests for GitLab API pagination
```

### Testing

We maintain comprehensive test coverage. Please include tests for new features:

```bash
# Run all tests
pdm run test

# Run tests with coverage
pdm run test-cov

# Run specific test file
pdm run test tests/test_analyzer.py

# Run tests matching pattern
pdm run test -k "test_scoring"
```

#### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **API Tests**: Test GitLab API interactions (mocked)
- **End-to-End Tests**: Test complete workflows

#### Writing Tests

```python
# Example test structure
def test_feature_functionality():
    """Test that feature works correctly."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = feature_function(input_data)
    
    # Assert
    assert result.expected_property == expected_value
    assert len(result.items) == 3
```

### Architecture Guidelines

#### Core Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Pass dependencies explicitly
3. **Error Handling**: Graceful degradation with informative messages
4. **Performance**: Efficient API usage with caching
5. **Testability**: Design for easy testing with mocks

#### Module Structure

```python
# Standard module structure
"""Module docstring describing purpose."""

import standard_library_imports
import third_party_imports

from .local_imports import LocalClass

# Constants
CONSTANT_VALUE = "value"

# Classes and functions
class ExampleClass:
    """Class docstring."""
    
    def __init__(self, dependency: Dependency):
        self.dependency = dependency
    
    def public_method(self) -> ReturnType:
        """Method docstring."""
        return self._private_method()
    
    def _private_method(self) -> ReturnType:
        """Private method implementation."""
        pass
```

#### Adding New Features

1. **Design First**: Consider the interface and data flow
2. **Write Tests**: Start with test cases for the new feature
3. **Implement**: Write the minimal code to make tests pass
4. **Refactor**: Improve code quality while keeping tests green
5. **Document**: Update docstrings, README, and examples

## 🐛 Bug Reports

When filing bug reports, please include:

### Required Information

1. **Environment Details**:
   - Python version
   - GitLab version
   - Operating system
   - Tool version

2. **Reproduction Steps**:
   - Exact command used
   - Input data (sanitized)
   - Expected behavior
   - Actual behavior

3. **Error Output**:
   - Complete error messages
   - Stack traces
   - Log output (use `--verbose`)

### Example Bug Report

```markdown
## Bug Description
Serialization fails when repository contains defaultdict objects

## Environment
- Python: 3.11.5
- GitLab: 17.2.1-ee
- OS: Ubuntu 22.04
- Tool Version: 1.0.0

## Reproduction Steps
1. Run analysis on GitLab instance with complex pipeline data
2. Command: `pdm run gitlab-stats https://gitlab.example.com token --verbose`
3. Error occurs during data caching step

## Error Output
```
TypeError: first argument must be callable or None
  File "glabmetrics/data_storage.py", line 55, in _serialize_repository_stats
    repo_dict = asdict(repo)
```

## Expected Behavior
Data should serialize successfully and be cached for reuse

## Additional Context
This affects repositories with complex pipeline_details containing defaultdict objects
```

## 💡 Feature Requests

For feature requests, please provide:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other ways to achieve the goal
4. **Implementation Notes**: Any technical considerations

### Feature Request Template

```markdown
## Feature Request: [Brief Description]

### Problem Statement
Describe the problem this feature would solve.

### Proposed Solution
Detailed description of the proposed feature.

### User Stories
- As a [user type], I want [goal] so that [benefit]
- As a [user type], I want [goal] so that [benefit]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Technical Considerations
Any implementation details, dependencies, or constraints.
```

## 🚀 Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite**:
   ```bash
   pdm run test
   pdm run lint
   pdm run format-check
   ```

3. **Update documentation** if needed
4. **Add changelog entry** (optional - will be generated)

### PR Guidelines

1. **Single Purpose**: One feature or fix per PR
2. **Clear Description**: Explain what and why
3. **Link Issues**: Reference related issues
4. **Small Changes**: Easier to review and merge
5. **Update Tests**: Include relevant test updates

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
- Fixes #123
- Related to #456

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] New tests added for new functionality

## Screenshots/Examples
If applicable, add screenshots or example output.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Changelog entry added (if significant)
```

## 🏗️ Development Environment

### IDE Setup

#### VS Code
Recommended extensions:
- Python
- Python Docstring Generator
- GitLens
- Better Comments
- Auto Docstring

#### Settings
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=100"],
    "python.testing.pytestEnabled": true
}
```

### Docker Development

```bash
# Build development image
docker build -t gitlab-stats-dev .

# Run development container
docker run -it --rm \
  -v $(pwd):/home/app/src \
  -w /home/app/src \
  gitlab-stats-dev bash

# Run tests in container
docker run --rm \
  -v $(pwd):/home/app/src \
  -w /home/app/src \
  gitlab-stats-dev pdm run test
```

### Performance Testing

For performance-related changes:

```bash
# Profile specific functions
python -m cProfile -o profile.prof -m glabmetrics.main url token

# Analyze profile
python -c "import pstats; pstats.Stats('profile.prof').sort_stats('cumulative').print_stats(20)"

# Memory profiling
pip install memory-profiler
python -m memory_profiler glabmetrics/main.py
```

## 🚀 Release Process

### Version Management

We use semantic versioning and automated releases:

```bash
# Bump version (automated based on commit messages)
pdm run bump

# Generate changelog
pdm run changelog

# Create release (maintainers only)
git tag v1.2.3
git push origin v1.2.3
```

### Release Checklist

For maintainers preparing releases:

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog generated
- [ ] Version bumped
- [ ] Docker image builds
- [ ] Release notes prepared

## 📚 Resources

### Documentation
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Tools
- [PDM Documentation](https://pdm.fming.dev/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [flake8 Linter](https://flake8.pycqa.org/)
- [pre-commit](https://pre-commit.com/)

## ❓ Questions?

- **General Questions**: Use [GitHub Discussions](https://github.com/yourusername/gitlab-stats-analyzer/discussions)
- **Bug Reports**: Use [GitHub Issues](https://github.com/yourusername/gitlab-stats-analyzer/issues)
- **Feature Requests**: Use [GitHub Issues](https://github.com/yourusername/gitlab-stats-analyzer/issues) with "enhancement" label

Thank you for contributing to glabmetrics! 🎉