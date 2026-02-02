"""
Git Service - Worktree and PR Operations

Provides git operations for pipelines:
- Worktree management for isolated changes
- Branch creation and management
- PR creation via GitHub CLI
- Merge operations

Uses git CLI and gh CLI for reliability.
"""

import os
import subprocess
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# Worktree base directory
WORKTREE_BASE = Path("/tmp/pipelzr-worktrees")


@dataclass
class WorktreeInfo:
    """Git worktree information."""
    path: str
    branch: str
    commit_sha: str
    created_at: str


@dataclass
class PRInfo:
    """Pull request information."""
    url: str
    number: int
    branch: str
    title: str


class GitService:
    """
    Git operations service for pipeline automation.

    Manages worktrees for isolated changes without affecting main repo.
    Creates PRs via GitHub CLI (gh).
    """

    def __init__(self):
        WORKTREE_BASE.mkdir(parents=True, exist_ok=True)

    def _run_git(
        self,
        args: List[str],
        cwd: str = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run git command."""
        cmd = ["git"] + args
        logger.debug(f"Running: {' '.join(cmd)}", cwd=cwd)

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        if check and result.returncode != 0:
            logger.error(f"Git command failed: {result.stderr}")
            raise RuntimeError(f"Git error: {result.stderr}")

        return result

    def _run_gh(
        self,
        args: List[str],
        cwd: str = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run GitHub CLI command."""
        cmd = ["gh"] + args
        logger.debug(f"Running: {' '.join(cmd)}", cwd=cwd)

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env={**os.environ, "GH_PROMPT_DISABLED": "1"}
        )

        if check and result.returncode != 0:
            logger.error(f"gh command failed: {result.stderr}")
            raise RuntimeError(f"gh error: {result.stderr}")

        return result

    def create_worktree(
        self,
        project_path: str,
        branch_name: str,
        base_branch: str = "main"
    ) -> WorktreeInfo:
        """Create git worktree for isolated changes."""
        project_path = Path(project_path)
        worktree_path = WORKTREE_BASE / branch_name.replace("/", "_")

        # Ensure base_branch has a value
        if not base_branch or base_branch.strip() == "":
            base_branch = "main"

        # Clean up existing worktree
        if worktree_path.exists():
            self._run_git(
                ["worktree", "remove", str(worktree_path), "--force"],
                cwd=str(project_path),
                check=False
            )
            if worktree_path.exists():
                shutil.rmtree(worktree_path)

        # Ensure base branch is up to date
        self._run_git(["fetch", "origin", base_branch], cwd=str(project_path), check=False)

        # Delete remote branch if exists
        self._run_git(
            ["push", "origin", "--delete", branch_name],
            cwd=str(project_path),
            check=False
        )

        # Delete local branch if exists
        self._run_git(
            ["branch", "-D", branch_name],
            cwd=str(project_path),
            check=False
        )

        # Create worktree with new branch
        self._run_git(
            ["worktree", "add", "-b", branch_name, str(worktree_path), f"origin/{base_branch}"],
            cwd=str(project_path)
        )

        # Get commit SHA
        result = self._run_git(["rev-parse", "HEAD"], cwd=str(worktree_path))
        commit_sha = result.stdout.strip()

        logger.info(
            "Created worktree",
            path=str(worktree_path),
            branch=branch_name,
            commit=commit_sha[:8]
        )

        return WorktreeInfo(
            path=str(worktree_path),
            branch=branch_name,
            commit_sha=commit_sha,
            created_at=datetime.now().isoformat()
        )

    def apply_fixes(
        self,
        worktree_path: str,
        fixes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply code fixes to worktree."""
        applied = []
        failed = []

        for fix in fixes:
            file_path = fix.get("file_path", "")
            diff = fix.get("diff", "")

            if not file_path:
                continue

            full_path = Path(worktree_path) / file_path

            try:
                if diff:
                    # Apply diff using patch
                    patch_file = Path(worktree_path) / ".patch"
                    patch_file.write_text(diff)

                    result = subprocess.run(
                        ["patch", "-p1", "-i", str(patch_file)],
                        cwd=worktree_path,
                        capture_output=True,
                        text=True
                    )

                    patch_file.unlink()

                    if result.returncode == 0:
                        applied.append(file_path)
                    else:
                        failed.append({"file": file_path, "error": result.stderr})
                else:
                    # No diff provided, just touch file
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.touch()
                    applied.append(file_path)

            except Exception as e:
                failed.append({"file": file_path, "error": str(e)})

        return {
            "applied": applied,
            "failed": failed,
            "total": len(fixes)
        }

    def commit_changes(
        self,
        worktree_path: str,
        message: str
    ) -> str:
        """Commit all changes in worktree."""
        # Stage all changes
        self._run_git(["add", "-A"], cwd=worktree_path)

        # Check if there are changes to commit
        result = self._run_git(
            ["status", "--porcelain"],
            cwd=worktree_path
        )

        if not result.stdout.strip():
            logger.info("No changes to commit")
            return ""

        # Commit
        self._run_git(
            ["commit", "-m", message],
            cwd=worktree_path
        )

        # Get commit SHA
        result = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
        return result.stdout.strip()

    def push_branch(
        self,
        worktree_path: str,
        branch_name: str
    ) -> bool:
        """Push branch to origin."""
        self._run_git(
            ["push", "-u", "origin", branch_name, "--force"],
            cwd=worktree_path
        )
        return True

    def create_pr(
        self,
        project_path: str,
        branch_name: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
        labels: List[str] = None
    ) -> PRInfo:
        """Create pull request via GitHub CLI."""
        args = [
            "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base_branch,
            "--head", branch_name
        ]

        if draft:
            args.append("--draft")

        if labels:
            for label in labels:
                args.extend(["--label", label])

        result = self._run_gh(args, cwd=str(project_path))

        # Parse PR URL from output
        pr_url = result.stdout.strip()
        pr_number = int(pr_url.split("/")[-1]) if pr_url else 0

        logger.info("Created PR", url=pr_url, number=pr_number)

        return PRInfo(
            url=pr_url,
            number=pr_number,
            branch=branch_name,
            title=title
        )

    def merge_pr(
        self,
        project_path: str,
        pr_number: int,
        merge_method: str = "squash",
        delete_branch: bool = True
    ) -> Dict[str, Any]:
        """Merge pull request via GitHub CLI."""
        args = [
            "pr", "merge", str(pr_number),
            f"--{merge_method}",
            "--auto"
        ]

        if delete_branch:
            args.append("--delete-branch")

        result = self._run_gh(args, cwd=str(project_path))

        return {
            "merged": True,
            "pr_number": pr_number,
            "method": merge_method
        }

    def cleanup_worktree(
        self,
        project_path: str,
        worktree_path: str
    ) -> bool:
        """Remove worktree."""
        self._run_git(
            ["worktree", "remove", worktree_path, "--force"],
            cwd=str(project_path),
            check=False
        )

        if Path(worktree_path).exists():
            shutil.rmtree(worktree_path)

        return True


# Singleton instance
git_service = GitService()


# Action handlers for pipeline executor
async def action_git_apply_fixes(
    input_data: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """Apply fixes in git worktree."""
    project_path = input_data.get("project_path", "")
    fixes = input_data.get("fixes", [])
    branch_name = input_data.get("branch_name") or f"fix/pipeline-{datetime.now().strftime('%Y%m%d-%H%M')}"
    base_branch = input_data.get("base_branch") or "main"

    # Ensure base_branch is never empty
    if not base_branch or base_branch.strip() == "":
        base_branch = "main"

    # Create worktree
    worktree = git_service.create_worktree(
        project_path=project_path,
        branch_name=branch_name,
        base_branch=base_branch
    )

    # Apply fixes
    if fixes:
        result = git_service.apply_fixes(worktree.path, fixes)

        # Commit if any changes
        if result.get("applied"):
            commit_sha = git_service.commit_changes(
                worktree.path,
                f"fix(ux): Apply visual review fixes\n\nApplied {len(result['applied'])} fixes"
            )

            # Push
            git_service.push_branch(worktree.path, branch_name)

            worktree.commit_sha = commit_sha

    return {
        "worktree_path": worktree.path,
        "branch_name": branch_name,
        "commit_sha": worktree.commit_sha,
        "base_branch": base_branch
    }


async def action_git_create_pr(
    input_data: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """Create pull request."""
    project_path = input_data.get("project_path", "")
    branch_name = input_data.get("branch_name", "")
    base_branch = input_data.get("base_branch", "main")
    title = input_data.get("title", "Pipeline fixes")
    body = input_data.get("body", "Automated fixes from pipeline")
    draft = input_data.get("draft", False)
    labels = input_data.get("labels", [])

    try:
        pr = git_service.create_pr(
            project_path=project_path,
            branch_name=branch_name,
            base_branch=base_branch,
            title=title,
            body=body,
            draft=draft,
            labels=labels
        )

        return {
            "url": pr.url,
            "number": pr.number,
            "branch": pr.branch,
            "title": pr.title
        }
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        return {
            "url": "",
            "number": 0,
            "error": str(e)
        }


async def action_git_merge_pr(
    input_data: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """Merge pull request."""
    project_path = input_data.get("project_path", "")
    pr_number = input_data.get("pr_number", 0)
    merge_method = input_data.get("merge_method", "squash")
    delete_branch = input_data.get("delete_branch", True)

    if not pr_number:
        return {"merged": False, "error": "No PR number provided"}

    try:
        result = git_service.merge_pr(
            project_path=project_path,
            pr_number=pr_number,
            merge_method=merge_method,
            delete_branch=delete_branch
        )

        return result
    except Exception as e:
        logger.error(f"Failed to merge PR: {e}")
        return {"merged": False, "error": str(e)}
