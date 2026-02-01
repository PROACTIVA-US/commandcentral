#!/usr/bin/env python3
"""
Index CommandCentral skills into CC4's KnowledgeBeast.

Reads skill files from skills/ directory and indexes them via CC4's API
for semantic search, conflict detection, and composition suggestions.

Usage:
    python scripts/index_skills_to_cc4.py

    # With custom CC4 URL:
    CC4_URL=http://localhost:8001 python scripts/index_skills_to_cc4.py
"""
import os
import sys
import json
import httpx
import asyncio
import logging
from pathlib import Path
from typing import Optional
import yaml
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
CC4_URL = os.environ.get("CC4_URL", "http://localhost:8001")
SKILLS_DIR = Path(__file__).parent.parent / "skills"
MANIFEST_PATH = SKILLS_DIR / "MANIFEST.yaml"


def parse_skill_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from skill file."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return frontmatter or {}, body
            except yaml.YAMLError:
                pass
    return {}, content


def extract_skill_metadata(skill_path: Path, manifest_entry: Optional[dict] = None) -> dict:
    """Extract metadata from skill file and manifest."""
    content = skill_path.read_text()
    frontmatter, body = parse_skill_frontmatter(content)

    # Get skill name from path
    skill_name = skill_path.parent.name
    if skill_name in ["skills", "archive"]:
        skill_name = skill_path.stem

    # Merge manifest data if available
    metadata = {
        "name": frontmatter.get("name", skill_name),
        "status": frontmatter.get("status", "active"),
        "description": frontmatter.get("description", ""),
        "priority": "P1",  # Default
        "keywords": [],
        "file_patterns": [],
    }

    if manifest_entry:
        metadata["priority"] = manifest_entry.get("priority", "P1")
        metadata["keywords"] = manifest_entry.get("keywords", [])
        metadata["file_patterns"] = manifest_entry.get("file_patterns", [])
        metadata["description"] = manifest_entry.get("description", metadata["description"])

    return metadata, body


def load_manifest() -> dict:
    """Load skill manifest for metadata."""
    if not MANIFEST_PATH.exists():
        return {}

    try:
        content = MANIFEST_PATH.read_text()
        manifest = yaml.safe_load(content)
        # Index by name for quick lookup
        return {s["name"]: s for s in manifest.get("skills", [])}
    except Exception as e:
        logger.warning(f"Could not load manifest: {e}")
        return {}


async def index_skill(client: httpx.AsyncClient, skill_path: Path, manifest: dict) -> bool:
    """Index a single skill to CC4's KnowledgeBeast."""
    skill_name = skill_path.parent.name
    if skill_name in ["skills", "archive"]:
        skill_name = skill_path.stem

    manifest_entry = manifest.get(skill_name)
    metadata, body = extract_skill_metadata(skill_path, manifest_entry)

    # Determine if archived
    is_archived = "archive" in str(skill_path)

    # Build full content for indexing
    full_content = f"""# Skill: {metadata['name']}

**Priority:** {metadata['priority']}
**Status:** {metadata['status']}
**Archived:** {is_archived}

## Description
{metadata['description']}

## Keywords
{', '.join(metadata['keywords']) if metadata['keywords'] else 'None'}

## File Patterns
{', '.join(metadata['file_patterns']) if metadata['file_patterns'] else 'None'}

## Content
{body}
"""

    # Prepare knowledge sync payload
    payload = {
        "source": f"skill:{skill_name}",
        "content": full_content,
        "metadata": {
            "type": "skill",
            "skill_name": skill_name,
            "priority": metadata["priority"],
            "status": metadata["status"],
            "archived": is_archived,
            "keywords": metadata["keywords"],
            "file_patterns": metadata["file_patterns"],
            "source_repo": "CommandCentral",
        }
    }

    try:
        # Use the knowledge ingest endpoint
        response = await client.post(
            f"{CC4_URL}/api/v1/knowledge/ingest",
            json={
                "content": full_content,
                "source": f"skill:{skill_name}",
                "metadata": payload["metadata"]
            },
            timeout=30.0
        )

        if response.status_code in [200, 201]:
            return True
        elif response.status_code == 422:
            # Validation error - try memory store
            response = await client.post(
                f"{CC4_URL}/api/v1/memory/store",
                json={
                    "content": full_content,
                    "source": f"skill:{skill_name}",
                    "claim_type": "skill",
                    "confidence": 1.0,
                    "metadata": payload["metadata"]
                },
                timeout=30.0
            )
            return response.status_code in [200, 201]
        else:
            error_detail = response.text[:200] if response.text else "No details"
            logger.error(f"  ✗ {skill_name}: HTTP {response.status_code} - {error_detail}")
            return False

    except Exception as e:
        logger.error(f"  ✗ {skill_name}: {e}")
        return False


async def main():
    """Index all skills to CC4."""
    logger.info(f"Indexing skills from {SKILLS_DIR}")
    logger.info(f"Target: {CC4_URL}")

    # Check CC4 is running
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CC4_URL}/", timeout=5.0)
            info = response.json()
            logger.info(f"Connected to {info.get('name', 'CC4')} v{info.get('version', '?')}")
        except Exception as e:
            logger.error(f"Cannot connect to CC4 at {CC4_URL}: {e}")
            sys.exit(1)

    # Load manifest
    manifest = load_manifest()
    logger.info(f"Loaded manifest with {len(manifest)} skill definitions")

    # Find all skill files
    skill_files = list(SKILLS_DIR.glob("**/SKILL.md")) + list(SKILLS_DIR.glob("**/README.md"))
    # Exclude files that are just READMEs in archive subdirs
    skill_files = [f for f in skill_files if f.name == "SKILL.md" or f.parent.name != "archive"]

    logger.info(f"Found {len(skill_files)} skill files")

    indexed = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        for skill_path in sorted(skill_files):
            skill_name = skill_path.parent.name
            if skill_name in ["skills"]:
                skill_name = skill_path.stem

            success = await index_skill(client, skill_path, manifest)
            if success:
                logger.info(f"  ✓ {skill_name}")
                indexed += 1
            else:
                failed += 1

    print(f"\n{'='*50}")
    print(f"Indexed: {indexed}, Failed: {failed}")
    print(f"Total skills processed: {indexed + failed}")


if __name__ == "__main__":
    asyncio.run(main())
