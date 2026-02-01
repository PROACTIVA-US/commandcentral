---
status: active
name: repository-hygiene
description: Enforces clean repository structure by preventing root-level clutter,
  organizing scripts/docs properly, and cleaning up temporary artifacts. Use during
  any session when creating files, and before commits.
contract:
  version: '1.0'
  inputs:
    required:
    - name: task_description
      type: string
      description: Description of the task to perform
    optional: []
  outputs:
  - name: result
    type: object
    properties:
      success:
        type: boolean
      summary:
        type: string
  errors:
  - code: SKILL_EXECUTION_FAILED
    description: Skill execution encountered an error
    recoverable: true
  side_effects:
  - type: file_write
    description: May modify files
  - type: git_commit
    description: May create git commits
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes:
  - scope: file:write
    required: true
  - scope: git:commit
    required: false
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# Repository Hygiene

Keep repositories professional and organized. Every file has a proper home.

## Core Rules

### Root Directory - Keep Minimal

**Allowed in root:**
- README.md, LICENSE, CONTRIBUTING.md, SECURITY.md, CLAUDE.md
- Package files (package.json, pyproject.toml, Cargo.toml, etc.)
- Config files (.gitignore, .env.example, tsconfig.json, etc.)
- CI/CD directories (.github/, .claude/)

**Examples of allowed root files:**
```
✅ README.md               # Project documentation
✅ package.json            # Node.js dependencies
✅ .gitignore              # Git configuration
✅ tsconfig.json           # TypeScript config
✅ .env.example            # Example environment variables
```

**NOT allowed in root:**
- Test scripts (`test-*.sh`, `test-*.py`)
- Utility scripts (`fix-*.sh`, `apply-*.ts`, `session-*`)
- SQL files, one-off scripts
- Documentation (except allowed list above)

**Examples of violations:**
```
❌ test-api.sh             # Should be in scripts/tests/
❌ fix-database.py         # Should be in scripts/
❌ session-notes.md        # Should be in docs/ or deleted
❌ migration-001.sql       # Should be in migrations/
❌ API_GUIDE.md            # Should be in docs/
❌ apply-patches.ts        # Should be in scripts/
```

### Proper Locations

| File Type | Location | Example |
|-----------|----------|---------|
| Test scripts | `scripts/tests/` or `tests/` | `scripts/tests/test-api.sh` |
| Utility scripts | `scripts/` | `scripts/fix-database.py` |
| Documentation | `docs/` | `docs/API_GUIDE.md` |
| SQL migrations | `migrations/` or `db/migrations/` | `migrations/001-add-users.sql` |
| Temporary files | `/tmp/` or delete after use | `/tmp/debug-output.log` |
| Archive files | `archives/` or `releases/` | `archives/prototype-v1.zip` |
| Debug output | `docs/temp/` or delete | `docs/temp/debug-output.txt` |
| Stale documentation | `docs/archived/` with timestamp | `docs/archived/NOTES-2025-12-27.md` |
| Session notes | `docs/sessions/` | `docs/sessions/2025-12-15-summary.md` |

**Real-world examples:**

**Before (❌ Messy):**
```
CommandCenter/
├── README.md
├── test-auth.sh           ❌ Wrong location
├── fix-permissions.py     ❌ Wrong location
├── ARCHITECTURE.md        ❌ Wrong location
├── session-notes.md       ❌ Wrong location
└── src/
```

**After (✅ Clean):**
```
CommandCenter/
├── README.md
├── scripts/
│   ├── tests/
│   │   └── test-auth.sh   ✅ Proper location
│   └── fix-permissions.py ✅ Proper location
├── docs/
│   └── ARCHITECTURE.md    ✅ Proper location
└── src/
```

## Workflow

### Before Creating Files

Ask yourself:
1. **Temporary?** → Create in `/tmp/` or delete immediately after
2. **Test script?** → `scripts/tests/` or `tests/`
3. **Utility?** → `scripts/`
4. **Documentation?** → `docs/`

**Decision tree examples:**

```
"I need to test the authentication flow"
→ Temporary test? YES
→ Location: /tmp/test-auth.sh or scripts/tests/test-auth.sh
→ Delete after use? If in /tmp, YES

"I'm writing a database migration"
→ Temporary? NO
→ Location: migrations/003-add-oauth.sql

"I need a script to fix file permissions"
→ Temporary? Maybe reusable
→ Location: scripts/fix-permissions.py

"I want to document the API"
→ Documentation? YES
→ Location: docs/API.md
```

### Before Committing

Run these checks:
```bash
# Find violations in root
ls -1 *.md 2>/dev/null | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$'
ls -1 *.{sh,py,js,ts} 2>/dev/null
ls -1 test-* session-* 2>/dev/null
```

Move or delete any violations before committing.

**Example cleanup process:**
```bash
# Found violations:
# - test-api.sh
# - fix-db.py
# - SETUP_GUIDE.md

# Move to proper locations:
mkdir -p scripts/tests docs
mv test-api.sh scripts/tests/
mv fix-db.py scripts/
mv SETUP_GUIDE.md docs/

# Verify root is clean:
git status
```

## Red Flags

- Creating `test-*.sh` in root
  - **Example**: `touch test-login.sh` in root → Should be in `scripts/tests/`
- "I'll clean it up later" (do it now)
  - **Example**: Leaving `debug-output.txt` → Delete or move to `/tmp/`
- "It's just a quick test" (use `/tmp/` or delete after)
  - **Example**: `quick-test.py` → Use `/tmp/quick-test.py` and delete after
- Leaving utility scripts in root
  - **Example**: `apply-patches.sh` sitting in root → Move to `scripts/`

## Quick Reference Checklist

Use this checklist before every commit:

### File Organization
- [ ] No test scripts in root (e.g., `test-*.sh`, `test-*.py`)
- [ ] No utility scripts in root (e.g., `fix-*.sh`, `apply-*.ts`)
- [ ] No stray .md files in root (except README, LICENSE, CONTRIBUTING, SECURITY, CLAUDE)
- [ ] No SQL files in root (should be in `migrations/`)
- [ ] No session/temporary files in root (e.g., `session-*.md`, `temp-*.txt`)

### Directory Structure
- [ ] Test scripts in `scripts/tests/` or `tests/`
- [ ] Utility scripts in `scripts/`
- [ ] Documentation in `docs/`
- [ ] Migrations in `migrations/` or `db/migrations/`
- [ ] Temporary files deleted or in `/tmp/`

### Git Status
- [ ] `git status` shows only intentional changes
- [ ] No untracked files that should be ignored
- [ ] No accidentally committed temporary files

### Common Violations to Check
- [ ] No files matching pattern: `test-*` in root
- [ ] No files matching pattern: `fix-*` in root
- [ ] No files matching pattern: `session-*` in root
- [ ] No files matching pattern: `*.sql` in root
- [ ] No files matching pattern: `apply-*` in root

**Quick verification command:**
```bash
# Run this to catch most violations:
ls -1 | grep -E '^(test-|fix-|session-|apply-)'
ls -1 *.sql 2>/dev/null
ls -1 *.md | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$'
```

If any of these commands return results, you have violations to fix!

## Handling Duplicate Files

When moving files to proper locations, you may find duplicates:

**Check for conflicts first:**
```bash
# Before moving, check if destination exists
ls -la docs/MYFILE.md 2>/dev/null
diff MYFILE.md docs/MYFILE.md 2>/dev/null
```

**Resolution strategies:**
- **Identical files**: Delete the root copy
- **Different content**:
  - If root is newer → replace docs version
  - If docs is canonical → delete root version
  - If both valuable → merge or archive one with timestamp

**Example:**
```bash
# Found AGENTS.md in both root and docs/
diff AGENTS.md docs/AGENTS.md

# If docs version is canonical:
rm AGENTS.md

# If root is newer but docs is canonical location:
mv docs/AGENTS.md docs/archived/AGENTS-old.md
mv AGENTS.md docs/AGENTS.md
```

## Cleaning Already-Committed Files

If temporary files are already in git history:

1. **Move, don't delete** (preserves history for debugging)
2. **Use descriptive paths** with timestamps if historical value exists
3. **Add .gitignore patterns** to prevent recurrence

```bash
# Move committed temporary file
git mv debug-output.txt docs/temp/debug-output-2025-12-15.txt

# Move committed archive
git mv prototype.zip archives/prototype-v1.zip

# Archive stale documentation with timestamp
git mv NOTES.md docs/archived/NOTES-2025-12-27.md
```

## Prevention: .gitignore Patterns

After cleanup, update `.gitignore` to prevent violations:

```gitignore
# Root-level temporary files
/*.txt          # Debug/output files should be in docs/temp/
/*.zip          # Archives should be in archives/
/*.tar.gz       # Archives should be in archives/
session-*.md    # Session notes should be in docs/sessions/
NOTES.md        # Personal notes should be in docs/
STATUS_LOG.md   # Status logs should be in docs/
```

**Test your patterns:**
```bash
# Create a test file and verify it's ignored
touch test-debug.txt
git status  # Should not show test-debug.txt
rm test-debug.txt
```

## Verification Commands (Graceful)

Updated commands that handle no-match cases gracefully:

```bash
# Check for test/utility scripts in root (no error on empty)
ls -1 | grep -E '^(test-|fix-|session-|apply-)' || echo "✓ No script violations"

# Check for SQL files in root
ls -1 *.sql 2>/dev/null || echo "✓ No SQL files in root"

# Check for extra markdown files
ls -1 *.md 2>/dev/null | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$' || echo "✓ No extra markdown files"

# Check for archive files in root
ls -1 *.zip *.tar.gz 2>/dev/null || echo "✓ No archive files in root"

# Check for debug/temp text files
ls -1 *.txt 2>/dev/null || echo "✓ No text files in root"
```
