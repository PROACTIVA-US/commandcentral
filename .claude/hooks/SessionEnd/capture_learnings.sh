#!/bin/bash
# PostSession Hook - Capture learnings from Claude Code session
# Created: 2026-01-27
#
# This hook runs after each Claude Code session ends.
# It triggers knowledge capture from the session transcript.

# CC4 backend URL
CC4_URL="${CC4_URL:-http://localhost:8001}"

# Check if backend is running
if ! curl -s --max-time 2 "${CC4_URL}/api/v1/health" > /dev/null 2>&1; then
    # Backend not running, skip silently
    exit 0
fi

# Get session info from environment (if available)
SESSION_ID="${CLAUDE_SESSION_ID:-}"
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"

# Trigger knowledge sync via API
# This calls the CLI session importer to process any new sessions
curl -s --max-time 10 \
    -X POST "${CC4_URL}/api/v1/knowledge/sync-cli-sessions" \
    -H "Content-Type: application/json" \
    -d "{\"project_path\": \"${PROJECT_PATH}\"}" \
    > /dev/null 2>&1 || true

# Log completion (optional, for debugging)
# echo "CC4: Knowledge capture triggered for session"

exit 0
