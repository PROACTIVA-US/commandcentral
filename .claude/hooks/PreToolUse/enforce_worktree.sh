#!/bin/bash
# Worktree Enforcement Hook for CC4 Self-Modification
# Updated: 2026-01-29
#
# Blocks direct modifications to CC4's codebase (backend/, frontend/)
# unless working in a worktree per docs/plans/cc4-self-modification.md
#
# Rationale: CC4 indexes its own code in KnowledgeBeast. Modifying
# code directly while the backend is running can cause issues.
# The worktree workflow ensures:
# 1. Backend runs from stable main branch
# 2. Changes happen in isolated worktree
# 3. Validation runs before merge

# Only check file modification tools
case "$CLAUDE_TOOL_NAME" in
  Write|Edit|MultiEdit|CreateFile|str_replace_editor)
    ;;
  *)
    exit 0
    ;;
esac

# Get the file path being modified
FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.file_path // .path // empty' 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only protect backend/ and frontend/ code paths
# Allow docs/, scripts/, .claude/, alembic/, etc.
if ! echo "$FILE_PATH" | grep -qE "^(backend/app|frontend/src)/"; then
  exit 0
fi

# Detect if we're in the main repo or a worktree
# Method: Check the current working directory path
CWD=$(pwd)

# If we're in a worktree directory, allow modifications
if echo "$CWD" | grep -qiE "(worktree|wt-|CC4-worktrees)"; then
  exit 0
fi

# Alternative detection: Check if .git is a file (worktree) vs directory (main repo)
# In worktrees, .git is a file containing "gitdir: /path/to/main/.git/worktrees/name"
if [ -f "$CWD/.git" ]; then
  # We're in a worktree, allow
  exit 0
fi

# We're in the main repo - block code modifications
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║  🛑 BLOCKED: Direct CC4 Code Modification                                ║"
echo "╠══════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                          ║"
echo "║  You're modifying CC4's code directly in the main repo.                  ║"
echo "║  This violates the self-modification workflow.                           ║"
echo "║                                                                          ║"
echo "║  REQUIRED: Use worktree isolation per CLAUDE.md                          ║"
echo "║                                                                          ║"
echo "║  Setup:                                                                  ║"
echo "║    cd ~/Projects/CC4                                                     ║"
echo "║    bash scripts/setup-self-modification.sh                               ║"
echo "║                                                                          ║"
echo "║  Then open Claude Code in the WORKTREE:                                  ║"
echo "║    ~/Projects/CC4-worktrees/wt-self-fix/                                 ║"
echo "║                                                                          ║"
echo "║  Read: docs/plans/cc4-self-modification.md                               ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "File: $FILE_PATH"
echo ""
exit 1
