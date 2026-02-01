#!/bin/bash
# PreToolUse hook for CC4 UI validation
# Runs BEFORE Claude Code makes any file changes to frontend/

# Only run for frontend file changes
if [[ "$TOOL_NAME" != "write_file" && "$TOOL_NAME" != "edit_file" ]]; then
    exit 0
fi

# Check if this is a frontend file
if [[ "$FILE_PATH" != *"frontend/src/"* ]]; then
    exit 0
fi

echo "🔍 CC4 UI Validation Hook"
echo "========================="

# Check if we have the unified spec
SPEC_FILE="$PROJECT_ROOT/docs/specs/everything-is-a-pipeline.md"
if [[ ! -f "$SPEC_FILE" ]]; then
    echo "⚠️ Warning: Spec file not found: $SPEC_FILE"
fi

# Read key principles from spec and check against proposed change
# This is a simplified version - full version would use LLM

echo "Checking proposed change against spec..."

# Key checks (these would be more sophisticated):
# 1. Does this create a separate page that should be a pipeline?
# 2. Does this add pipeline management to settings?
# 3. Does this create separate history/archive views?
# 4. Does this violate "everything is a pipeline" principle?

# For now, just warn about known anti-patterns
PROPOSED_CONTENT="$TOOL_INPUT"

if echo "$PROPOSED_CONTENT" | grep -qi "SettingsPage.*pipeline"; then
    echo "❌ VIOLATION: Pipeline management should be IN the pipeline viewer, not Settings"
    echo "See: docs/specs/everything-is-a-pipeline.md"
    exit 1
fi

if echo "$PROPOSED_CONTENT" | grep -qi "HistoryPage\|ArchivePage"; then
    echo "❌ VIOLATION: History/Archives should use Memory search, not separate views"
    echo "See: docs/specs/everything-is-a-pipeline.md"
    exit 1
fi

if echo "$PROPOSED_CONTENT" | grep -qi "KanbanPage" && ! echo "$PROPOSED_CONTENT" | grep -qi "PipelineCard"; then
    echo "❌ VIOLATION: Kanban should be a pipeline type, not separate page"
    echo "See: docs/specs/everything-is-a-pipeline.md"
    exit 1
fi

echo "✅ Basic spec checks passed"
exit 0
