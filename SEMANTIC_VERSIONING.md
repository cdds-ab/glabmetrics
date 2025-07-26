# glabmetrics - Semantic Versioning Guide

## 🚀 Wie das Semantic Versioning funktioniert

### **Commit-Message Formate:**

#### **🔧 PATCH (1.0.0 → 1.0.1)**
```bash
git commit -m "fix: behebe serialization error in test_data_storage"
git commit -m "fix(api): korrigiere timeout handling in gitlab_client"
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

### **Release-Prozess:**

#### **Automatisches Release (empfohlen):**
1. **Entwicklung mit konventionellen Commits:**
   ```bash
   git add .
   pdm run commit  # Verwendet commitizen für guided commit
   git push origin main
   ```

2. **Semantic Release Workflow wird automatisch ausgelöst:**
   - Analysiert Commit-Messages seit letztem Tag
   - Bestimmt Version-Bump automatisch
   - Aktualisiert Version in `pyproject.toml` und `__init__.py`
   - Generiert `CHANGELOG.md`
   - Erstellt Git-Tag und GitHub Release
   - Triggert PyPI Upload

#### **Manuelles Release:**
```bash
# Force specific version bump
gh workflow run release.yml -f version_bump=minor
```

### **Version-Beispiele:**

| Commits seit v1.0.0 | Neue Version | Trigger |
|---------------------|--------------|---------|
| `fix: bug1`, `fix: bug2` | v1.0.1 | PATCH |
| `feat: new feature` | v1.1.0 | MINOR |
| `feat!: breaking change` | v2.0.0 | MAJOR |
| `docs: update readme` | - | No release |

### **Workflow-Dateien:**

- **`.github/workflows/release.yml`** - Semantic Release
- **`.github/workflows/ci.yml`** - CI/CD mit PyPI Upload bei Tags
- **`.github/workflows/test-release.yml`** - TestPyPI für Experimente

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

1. **GitHub Releases**: Automatisch bei Git-Tags mit Artifacts
2. **Docker Images**: Automatisch bei Releases zu GitHub Container Registry
3. **Source Distribution**: Wheel/Tarball in GitHub Release Assets
4. **PyPI**: Kann später aktiviert werden (derzeit deaktiviert)

## 🎯 Next Steps:

1. Repository nach GitHub pushen
2. `PYPI_API_TOKEN` in Repository Settings hinzufügen  
3. Ersten Release mit konventionellem Commit erstellen
4. Semantic Release Workflow beobachten
