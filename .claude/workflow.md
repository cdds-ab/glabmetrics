# Claude Workflow Integration

## Automated Context Updates

### When to Update .claude/ Files

**Always update** when:
- ✅ Major features added/removed
- ✅ Architecture changes
- ✅ Test suite changes (new tests, failures fixed)
- ✅ Build process modifications
- ✅ Dependencies added/removed

**Consider updating** when:
- 🤔 Bug fixes with broader implications
- 🤔 Refactoring that changes patterns
- 🤔 Configuration changes

### Quick Update Commands

```bash
# Quick context update after significant changes
echo "## $(date '+%Y-%m-%d') Session
- Fixed: [describe what was fixed]
- Added: [describe what was added]
- Changed: [describe what changed]
" >> .claude/context.md

# Commit the updates
git add .claude/ && git commit -m "docs: update Claude context"
```

### Claude's Proactive Reminders

Claude should **automatically suggest** updating .claude/ files when:
1. Session involves major changes (>5 files modified)
2. New tests are added (changes test count)
3. Architecture discussions occur
4. Build/deployment processes change

### Template for Context Updates

```markdown
## [DATE] - [BRIEF_DESCRIPTION]
**Status**: [Current project state]
**Changes**: 
- [Major change 1]
- [Major change 2]
**Tests**: [Current test count and status]
**Issues**: [Any known issues or TODOs]
```