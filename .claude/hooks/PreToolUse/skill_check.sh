#!/bin/bash
# Skill Check Hook for CommandCenter V3
# Updated: 2026-01-12
# Enforces documentation protocol and repository hygiene

case "$CLAUDE_TOOL_NAME" in
  Write|Edit|MultiEdit|CreateFile|str_replace_editor)
    FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.file_path // .path // empty' 2>/dev/null)
    FILE_CONTENT=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.content // empty' 2>/dev/null)

    if [ -n "$FILE_PATH" ]; then
      # Block new plan files (except MASTER_PLAN.md)
      if echo "$FILE_PATH" | grep -qE "docs/plans/.+\.md$" && ! echo "$FILE_PATH" | grep -q "MASTER_PLAN.md"; then
        echo ""
        echo "❌ BLOCKED: Only ONE plan allowed - update docs/plans/MASTER_PLAN.md instead"
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # Block files in project root (except allowed list)
      BASENAME=$(basename "$FILE_PATH")
      if echo "$FILE_PATH" | grep -qE "^[^/]+\.md$" && ! echo "$BASENAME" | grep -qE "^(README|AGENTS|CLAUDE|NEXT_STEPS|CONTRIBUTING|LICENSE|SECURITY)\.md$"; then
        echo ""
        echo "❌ BLOCKED: No .md files in project root"
        echo "   Allowed: README.md, AGENTS.md, CLAUDE.md, NEXT_STEPS.md, CONTRIBUTING.md"
        echo "   Put docs in docs/, skills in skills/"
        echo "   Read: skills/repository-hygiene/SKILL.md"
        echo ""
        exit 1
      fi

      # Block test scripts in root
      if echo "$FILE_PATH" | grep -qE "^test[_-].*\.(py|sh|js|ts)$"; then
        echo ""
        echo "❌ BLOCKED: Test files must be in backend/app/tests/ or scripts/tests/"
        echo "   Read: skills/repository-hygiene/SKILL.md"
        echo ""
        exit 1
      fi

      # Block utility scripts in root
      if echo "$FILE_PATH" | grep -qE "^(fix|apply|session|util|setup)[_-].*\.(py|sh|js|ts)$"; then
        echo ""
        echo "❌ BLOCKED: Utility scripts must be in scripts/"
        echo "   Read: skills/repository-hygiene/SKILL.md"
        echo ""
        exit 1
      fi

      # Validate frontmatter for docs/ files (Write tool only, not Edit)
      if [ "$CLAUDE_TOOL_NAME" = "Write" ] && echo "$FILE_PATH" | grep -qE "^docs/.*\.md$"; then
        # Skip index.md and MANIFEST files
        if ! echo "$FILE_PATH" | grep -qE "(index\.md|MANIFEST)"; then
          if [ -n "$FILE_CONTENT" ]; then
            # Check for frontmatter
            if ! echo "$FILE_CONTENT" | grep -qE "^---"; then
              echo ""
              echo "❌ BLOCKED: Documentation files must have YAML frontmatter"
              echo "   File: $FILE_PATH"
              echo "   Required fields: title/name, updated (YYYY-MM-DD HH:MM)"
              echo "   Read: skills/documentation-protocol/SKILL.md"
              echo ""
              exit 1
            fi

            # Extract frontmatter and check for required fields
            FRONTMATTER=$(echo "$FILE_CONTENT" | awk '/^---$/{flag=!flag;next}flag' || echo "")

            if ! echo "$FRONTMATTER" | grep -qE "^(title|name):"; then
              echo ""
              echo "❌ BLOCKED: Missing 'title' or 'name' field in frontmatter"
              echo "   File: $FILE_PATH"
              echo "   Read: skills/documentation-protocol/SKILL.md"
              echo ""
              exit 1
            fi

            if ! echo "$FRONTMATTER" | grep -qE "^updated:"; then
              echo ""
              echo "❌ BLOCKED: Missing 'updated' field in frontmatter"
              echo "   File: $FILE_PATH"
              echo "   Required format: updated: YYYY-MM-DD HH:MM"
              echo "   Read: skills/documentation-protocol/SKILL.md"
              echo ""
              exit 1
            fi

            # Check timestamp format (YYYY-MM-DD HH:MM)
            UPDATED_LINE=$(echo "$FRONTMATTER" | grep "^updated:" || echo "")
            if [ -n "$UPDATED_LINE" ]; then
              TIMESTAMP=$(echo "$UPDATED_LINE" | sed 's/^updated: *//' | tr -d '"' | tr -d "'")
              if ! echo "$TIMESTAMP" | grep -qE "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"; then
                echo ""
                echo "❌ BLOCKED: Invalid timestamp format in frontmatter"
                echo "   File: $FILE_PATH"
                echo "   Found: $TIMESTAMP"
                echo "   Required: YYYY-MM-DD HH:MM (e.g., 2026-01-12 15:45)"
                echo "   Read: skills/documentation-protocol/SKILL.md"
                echo ""
                exit 1
              fi
            fi
          fi
        fi
      fi

      # Warn on pipeline/agent work
      if echo "$FILE_PATH" | grep -qE "(agent_service|task_executor|batch_orchestrator|autonomous)"; then
        echo ""
        echo "⚠️  Pipeline code: Read skills/operations/SKILL.md first"
        echo ""
      fi

      # Warn on frontend work
      if echo "$FILE_PATH" | grep -qE "frontend/src/components"; then
        echo "📐 Frontend: See skills/patterns/SKILL.md for component patterns"
      fi
    fi
    ;;
esac

exit 0
