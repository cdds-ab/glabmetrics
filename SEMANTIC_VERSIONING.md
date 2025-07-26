# glabmetrics - Semantic Versioning Guide

## 🚀 How Semantic Versioning Works

### **Commit Message Formats:**

#### **🔧 PATCH (1.0.0 → 1.0.1)**
```bash
git commit -m "fix: resolve serialization error in test_data_storage"
git commit -m "fix(api): correct timeout handling in gitlab_client"
```

#### **✨ MINOR (1.0.0 → 1.1.0)**  
```bash
git commit -m "feat: add semantic versioning workflow"
git commit -m "feat(ci): implement automated release pipeline"
```

#### **💥 MAJOR (1.0.0 → 2.0.0)**
```bash
git commit -m "feat!: restructure API with breaking changes"
git commit -m "fix!: remove deprecated GitLab v3 support

BREAKING CHANGE: GitLab API v3 is no longer supported. 
Users must upgrade to GitLab v4 API."
```

### **Release Process:**

#### **Automatic Release (recommended):**
1. **Development with conventional commits:**
   ```bash
   git add .
   pdm run commit  # Uses commitizen for guided commit
   git push origin master
   ```

2. **Semantic Release Workflow is automatically triggered:**
   - Analyzes commit messages since last tag
   - Determines version bump automatically
   - Updates version in `pyproject.toml` and `__init__.py`
   - Generates `CHANGELOG.md`
   - Creates Git tag and GitHub Release
   - Triggers Docker image build

#### **Manual Release:**
```bash
# Force specific version bump
gh workflow run release.yml -f version_bump=minor
```

### **Version Examples:**

| Commits since v1.0.0 | New Version | Trigger |
|----------------------|-------------|---------|
| `fix: bug1`, `fix: bug2` | v1.0.1 | PATCH |
| `feat: new feature` | v1.1.0 | MINOR |
| `feat!: breaking change` | v2.0.0 | MAJOR |
| `docs: update readme` | - | No release |

### **Workflow Files:**

- **`.github/workflows/release.yml`** - Semantic Release
- **`.github/workflows/ci.yml`** - CI/CD with Docker publishing on tags
- **`.github/workflows/test-release.yml`** - TestPyPI for experiments

### **Commands:**

```bash
# Check current version
pdm run cz version --project

# Create conventional commit (guided)
pdm run commit

# Manual version bump
pdm run cz bump --increment patch
pdm run cz bump --increment minor  
pdm run cz bump --increment major

# Generate changelog
pdm run changelog
```

### **Distribution:**

1. **GitHub Releases**: Automatic on Git tags with artifacts
2. **Docker Images**: Automatic on releases to GitHub Container Registry
3. **Source Distribution**: Wheel/Tarball in GitHub Release assets
4. **PyPI**: Can be enabled later (currently disabled)

## 🎯 Next Steps:

1. Push repository to GitHub
2. Add `CODECOV_TOKEN` in repository settings  
3. Create first release with conventional commit
4. Monitor semantic release workflow