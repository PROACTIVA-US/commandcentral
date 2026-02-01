#!/bin/bash
# Detect Redundant/Conflicting Documentation Hook
# Updated: 2026-02-01
# Prevents proliferation of one-off plans and redundant docs

case "$CLAUDE_TOOL_NAME" in
  Write|CreateFile)
    FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.file_path // .path // empty' 2>/dev/null)
    FILE_CONTENT=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.content // empty' 2>/dev/null)

    if [ -n "$FILE_PATH" ]; then
      BASENAME=$(basename "$FILE_PATH")
      DIRNAME=$(dirname "$FILE_PATH")

      # ============================================
      # BLOCK: One-off plan files
      # ============================================
      # Detect plan-like files outside of docs/plans/master-plan.md
      if echo "$FILE_PATH" | grep -qiE "(plan|roadmap|todo|next[-_]?steps|phase)" && \
         echo "$FILE_PATH" | grep -qE "\.md$" && \
         ! echo "$FILE_PATH" | grep -qE "docs/plans/master-plan\.md$"; then
        echo ""
        echo "❌ BLOCKED: Looks like a plan - update docs/plans/master-plan.md instead"
        echo "   File: $FILE_PATH"
        echo "   Pattern matched: plan/roadmap/todo/next-steps/phase"
        echo ""
        echo "   Why: One master plan prevents fragmentation."
        echo "   How: Add a section to master-plan.md, don't create new files."
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # ============================================
      # BLOCK: Handoff documents
      # ============================================
      if echo "$FILE_PATH" | grep -qiE "handoff|hand[-_]?off" && echo "$FILE_PATH" | grep -qE "\.md$"; then
        echo ""
        echo "❌ BLOCKED: Handoff docs are deprecated"
        echo "   File: $FILE_PATH"
        echo ""
        echo "   Why: Handoffs fragment knowledge and become stale."
        echo "   How: Update master-plan.md with current state instead."
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # ============================================
      # BLOCK: WIP/Draft prefix files
      # ============================================
      if echo "$BASENAME" | grep -qiE "^(wip|draft|temp|tmp)[-_]"; then
        echo ""
        echo "❌ BLOCKED: No WIP/Draft prefix files"
        echo "   File: $FILE_PATH"
        echo ""
        echo "   Why: Use 'status: draft' in frontmatter, not filename prefixes."
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # ============================================
      # BLOCK: Version suffix files
      # ============================================
      if echo "$BASENAME" | grep -qiE "[-_]v[0-9]+\.md$|[-_]v[0-9]+[-_]"; then
        echo ""
        echo "❌ BLOCKED: No version suffixes in filenames"
        echo "   File: $FILE_PATH"
        echo ""
        echo "   Why: Use git history for versions, not separate files."
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # ============================================
      # BLOCK: Date suffix files (except in archive/)
      # ============================================
      if echo "$BASENAME" | grep -qE "[-_][0-9]{4}[-_][0-9]{2}[-_][0-9]{2}" && \
         ! echo "$FILE_PATH" | grep -qE "/archive/"; then
        echo ""
        echo "❌ BLOCKED: No date suffixes in filenames (except in archive/)"
        echo "   File: $FILE_PATH"
        echo ""
        echo "   Why: Put timestamps in frontmatter 'updated:' field."
        echo "   If archiving, move to archive/ directory."
        echo "   Read: skills/documentation-protocol/SKILL.md"
        echo ""
        exit 1
      fi

      # ============================================
      # WARN: Potential duplicates in docs/
      # ============================================
      if echo "$FILE_PATH" | grep -qE "^docs/.*\.md$"; then
        # Check for similar files that might indicate duplication
        SEARCH_TERM=$(echo "$BASENAME" | sed 's/\.md$//' | sed 's/[-_]/ /g')

        # Look for files with similar names
        if [ -d "docs" ]; then
          SIMILAR=$(find docs -name "*.md" -type f 2>/dev/null | while read f; do
            OTHER_BASE=$(basename "$f" | sed 's/\.md$//' | sed 's/[-_]/ /g')
            # Simple similarity check - same words
            if [ "$OTHER_BASE" = "$SEARCH_TERM" ] && [ "$f" != "$FILE_PATH" ]; then
              echo "$f"
            fi
          done)

          if [ -n "$SIMILAR" ]; then
            echo ""
            echo "⚠️  WARNING: Similar file exists - check for redundancy"
            echo "   New file: $FILE_PATH"
            echo "   Existing: $SIMILAR"
            echo ""
            echo "   Consider updating the existing file instead."
            echo ""
          fi
        fi
      fi

    fi
    ;;
esac

exit 0
