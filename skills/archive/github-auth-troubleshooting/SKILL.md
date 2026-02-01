---
name: github-auth-troubleshooting
description: Diagnose and fix GitHub authentication failures for git push/pull. Use BEFORE suggesting the repo doesn't exist or asking the user to check permissions.
---

# GitHub Auth Troubleshooting

**CRITICAL:** When `git push` fails with "repository not found" or permission denied, DO NOT assume the repo doesn't exist. Run diagnostics first.

## Root Cause

This user has multiple GitHub accounts configured. The most common failure is:
- **Active account mismatch**: Git operations use the wrong GitHub account's credentials
- **GITHUB_TOKEN override**: An environment variable overrides the intended account

## Diagnostic Steps (Run These First)

```bash
# 1. Check which accounts are configured and which is ACTIVE
gh auth status

# 2. Check which account git operations will use
gh api user --jq '.login'

# 3. Check the remote URL to identify which account SHOULD be used
git remote -v
```

## Interpreting Results

Look at `gh auth status` output:
- Find `Active account: true` - this is what git will use
- Compare to the org/user in `git remote -v`
- If they don't match, that's the problem

Example problem state:
```
github.com
  ✓ Logged in to github.com account PerformanceSuite (GITHUB_TOKEN)
  - Active account: true          # <-- WRONG ACCOUNT IS ACTIVE

  ✓ Logged in to github.com account PROACTIVA-US (keyring)
  - Active account: false         # <-- THIS IS THE CORRECT ONE
```

## Fix

### If GITHUB_TOKEN is overriding:
```bash
unset GITHUB_TOKEN && gh auth switch --user CORRECT_ACCOUNT && git push origin main
```

### If just wrong account active:
```bash
gh auth switch --user CORRECT_ACCOUNT
git push origin main
```

## Prevention

Before any `git push` to a repo, quickly verify:
```bash
# Extract org from remote and compare to active account
REMOTE_ORG=$(git remote get-url origin | sed -E 's/.*[:/]([^/]+)\/[^/]+\.git/\1/')
ACTIVE_ACCOUNT=$(gh api user --jq '.login' 2>/dev/null)
if [ "$REMOTE_ORG" != "$ACTIVE_ACCOUNT" ]; then
  echo "WARNING: Remote org ($REMOTE_ORG) != active account ($ACTIVE_ACCOUNT)"
fi
```

## Key Lesson

"Repository not found" almost never means the repo doesn't exist when the user says it does. It means **authentication is using the wrong account**.
