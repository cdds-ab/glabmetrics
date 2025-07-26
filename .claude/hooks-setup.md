# Git Hooks Setup

## Automatic Quality Checks

This project uses Git hooks to ensure code quality and prevent broken commits.

### Current Hooks

#### Pre-commit Hook
- ✅ Runs `pdm run lint` (flake8)
- ✅ Runs `pdm run test` (all 77 tests)
- ✅ Checks for debug statements
- ✅ Reports TODO/FIXME count
- ❌ **Blocks commit** if linting or tests fail

#### Pre-push Hook  
- ✅ Extra validation for master/main branch
- ✅ Runs coverage tests
- ✅ Verifies all 77 tests pass
- ✅ Reminds about Claude context updates
- ❌ **Blocks push** if quality checks fail

#### Post-commit Hook
- 📝 Reminds to update `.claude/context.md`
- 🚨 Alerts on large commits (>5 files)

### Setup for New Team Members

```bash
# Hooks are already configured in .git/hooks/
# They activate automatically after cloning

# To test hooks manually:
.git/hooks/pre-commit   # Test commit checks
.git/hooks/pre-push     # Test push checks
```

### Bypassing Hooks (Emergency Only!)

```bash
# Skip pre-commit (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"

# Skip pre-push (NOT RECOMMENDED)  
git push --no-verify
```

### Hook Benefits

1. **Never commit broken code** - Tests must pass
2. **Consistent code style** - Linting enforced
3. **No debugging artifacts** - Warns about print/breakpoint
4. **Quality assurance** - Coverage on main branch
5. **Documentation reminders** - Keep Claude context updated

### Troubleshooting

**Hook not running?**
```bash
# Check if executable
ls -la .git/hooks/pre-commit
# Should show: -rwxr-xr-x

# Make executable if needed
chmod +x .git/hooks/pre-commit
```

**PDM not found?**
```bash
# Install PDM first
pip install pdm
# Or follow: https://pdm.fming.dev/latest/#installation
```