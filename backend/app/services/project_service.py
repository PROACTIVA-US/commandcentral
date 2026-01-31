"""
Project Service

Manages projects - the primary isolation boundary across all services.
"""

from datetime import datetime
from typing import Optional, List
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_

from ..models.project import Project, ProjectState
from ..models.audit import AuditEventType
from .audit_service import AuditService


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


class ProjectService:
    """Service for project operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit = AuditService(session)

    async def create(
        self,
        name: str,
        owner_id: str,
        description: str = None,
        slug: str = None,
        repo_path: str = None,
        repo_url: str = None,
        settings: dict = None,
        metadata: dict = None,
    ) -> Project:
        """Create a new project in proposed state."""
        # Generate slug if not provided
        if not slug:
            slug = slugify(name)

        # Ensure slug is unique
        existing = await self.get_by_slug(slug)
        if existing:
            # Append a number to make it unique
            base_slug = slug
            counter = 1
            while existing:
                slug = f"{base_slug}-{counter}"
                existing = await self.get_by_slug(slug)
                counter += 1

        project = Project(
            name=name,
            slug=slug,
            description=description,
            owner_id=owner_id,
            repo_path=repo_path,
            repo_url=repo_url,
            settings=settings or {},
            metadata=metadata or {},
            state=ProjectState.PROPOSED,
        )
        self.session.add(project)
        await self.session.flush()

        # Audit log
        await self.audit.log(
            event_type=AuditEventType.ENTITY_CREATED,
            event_name="project.created",
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            actor_id=owner_id,
        )

        return project

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Project]:
        """Get a project by slug."""
        result = await self.session.execute(
            select(Project).where(Project.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        state: ProjectState = None,
        owner_id: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Project]:
        """List all projects with optional filters."""
        query = select(Project)

        conditions = []
        if state:
            conditions.append(Project.state == state)
        if owner_id:
            conditions.append(
                or_(
                    Project.owner_id == owner_id,
                    Project.team_ids.contains([owner_id])  # User is in team
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Project.updated_at)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_for_user(self, user_id: str, limit: int = 50) -> List[Project]:
        """List projects a user has access to."""
        result = await self.session.execute(
            select(Project)
            .where(
                or_(
                    Project.owner_id == user_id,
                    Project.team_ids.contains([user_id])
                )
            )
            .order_by(desc(Project.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        project_id: str,
        actor_id: str,
        name: str = None,
        description: str = None,
        repo_path: str = None,
        repo_url: str = None,
        settings: dict = None,
        metadata: dict = None,
    ) -> Optional[Project]:
        """Update a project."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        # Update fields
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if repo_path is not None:
            project.repo_path = repo_path
        if repo_url is not None:
            project.repo_url = repo_url
        if settings is not None:
            project.settings = settings
        if metadata is not None:
            project.metadata = metadata

        project.updated_at = datetime.utcnow()

        await self.audit.log(
            event_type=AuditEventType.ENTITY_UPDATED,
            event_name="project.updated",
            entity_type="project",
            entity_id=project_id,
            project_id=project_id,
            actor_id=actor_id,
        )

        return project

    async def transition(
        self,
        project_id: str,
        to_state: ProjectState,
        actor_id: str,
        rationale: str = None,
    ) -> tuple[bool, str, Optional[Project]]:
        """
        Attempt to transition a project to a new state.

        Returns (success, message, project)
        """
        project = await self.get_by_id(project_id)
        if not project:
            return False, "Project not found", None

        from_state = project.state

        # Check if transition is allowed
        if not project.can_transition_to(to_state):
            await self.audit.log_transition(
                entity_type="project",
                entity_id=project_id,
                from_state=from_state.value,
                to_state=to_state.value,
                actor_id=actor_id,
                project_id=project_id,
                success=False,
                failure_reason=f"Transition from {from_state.value} to {to_state.value} not allowed",
            )
            return False, f"Cannot transition from {from_state.value} to {to_state.value}", project

        # Perform transition
        project.state = to_state
        project.state_changed_at = datetime.utcnow()
        project.state_changed_by = actor_id

        await self.audit.log_transition(
            entity_type="project",
            entity_id=project_id,
            from_state=from_state.value,
            to_state=to_state.value,
            actor_id=actor_id,
            project_id=project_id,
            success=True,
            rationale=rationale,
        )

        return True, f"Transitioned to {to_state.value}", project

    async def activate(self, project_id: str, actor_id: str) -> tuple[bool, str, Optional[Project]]:
        """Activate a proposed project."""
        return await self.transition(project_id, ProjectState.ACTIVE, actor_id)

    async def pause(self, project_id: str, actor_id: str, rationale: str = None) -> tuple[bool, str, Optional[Project]]:
        """Pause an active project."""
        return await self.transition(project_id, ProjectState.PAUSED, actor_id, rationale)

    async def resume(self, project_id: str, actor_id: str) -> tuple[bool, str, Optional[Project]]:
        """Resume a paused project."""
        return await self.transition(project_id, ProjectState.ACTIVE, actor_id)

    async def complete(self, project_id: str, actor_id: str, rationale: str = None) -> tuple[bool, str, Optional[Project]]:
        """Mark a project as completed."""
        return await self.transition(project_id, ProjectState.COMPLETED, actor_id, rationale)

    async def kill(self, project_id: str, actor_id: str, rationale: str = None) -> tuple[bool, str, Optional[Project]]:
        """Kill a project."""
        return await self.transition(project_id, ProjectState.KILLED, actor_id, rationale)

    async def add_team_member(self, project_id: str, user_id: str, actor_id: str) -> Optional[Project]:
        """Add a user to the project team."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        team_ids = project.team_ids or []
        if user_id not in team_ids:
            team_ids.append(user_id)
            project.team_ids = team_ids

            await self.audit.log(
                event_type=AuditEventType.ENTITY_UPDATED,
                event_name="project.team.member_added",
                entity_type="project",
                entity_id=project_id,
                project_id=project_id,
                actor_id=actor_id,
                metadata={"user_id": user_id},
            )

        return project

    async def remove_team_member(self, project_id: str, user_id: str, actor_id: str) -> Optional[Project]:
        """Remove a user from the project team."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        team_ids = project.team_ids or []
        if user_id in team_ids:
            team_ids.remove(user_id)
            project.team_ids = team_ids

            await self.audit.log(
                event_type=AuditEventType.ENTITY_UPDATED,
                event_name="project.team.member_removed",
                entity_type="project",
                entity_id=project_id,
                project_id=project_id,
                actor_id=actor_id,
                metadata={"user_id": user_id},
            )

        return project

    async def get_audit_trail(self, project_id: str, limit: int = 50) -> List:
        """Get audit trail for a project."""
        return await self.audit.get_by_project(project_id, limit=limit)

    async def delete(self, project_id: str, actor_id: str) -> bool:
        """Delete a project (only allowed in proposed state)."""
        project = await self.get_by_id(project_id)
        if not project:
            return False

        if project.state != ProjectState.PROPOSED:
            await self.audit.log(
                event_type=AuditEventType.ENTITY_DELETED,
                event_name="project.delete.denied",
                entity_type="project",
                entity_id=project_id,
                project_id=project_id,
                actor_id=actor_id,
                success=False,
                failure_reason="Can only delete projects in proposed state",
            )
            return False

        await self.session.delete(project)

        await self.audit.log(
            event_type=AuditEventType.ENTITY_DELETED,
            event_name="project.deleted",
            entity_type="project",
            entity_id=project_id,
            project_id=project_id,
            actor_id=actor_id,
        )

        return True
