"""
Goals service - business logic for goal management.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.goal import Goal, GoalState, GOAL_TRANSITIONS

logger = structlog.get_logger("idealzr.services.goals")


class GoalsService:
    """Service for managing goals and their hierarchy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_goal(self, data: dict) -> Goal:
        """Create a new goal."""
        goal = Goal(**data)
        self.db.add(goal)
        await self.db.flush()
        
        await logger.ainfo(
            "goal_created",
            goal_id=goal.id,
            title=goal.title,
            parent_id=goal.parent_id,
        )
        
        return goal

    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        result = await self.db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def update_goal(self, goal_id: str, updates: dict) -> Optional[Goal]:
        """Update a goal."""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        for field, value in updates.items():
            if hasattr(goal, field):
                setattr(goal, field, value)

        await self.db.flush()
        
        await logger.ainfo(
            "goal_updated",
            goal_id=goal_id,
            updates=list(updates.keys()),
        )
        
        return goal

    async def transition_goal(
        self, goal_id: str, new_state: GoalState, user_id: Optional[str] = None
    ) -> Optional[Goal]:
        """Transition a goal to a new state."""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        if not goal.can_transition_to(new_state):
            raise ValueError(
                f"Cannot transition from {goal.state.value} to {new_state.value}. "
                f"Allowed: {[s.value for s in goal.allowed_transitions()]}"
            )

        old_state = goal.state
        goal.state = new_state
        goal.state_changed_at = datetime.utcnow()
        goal.state_changed_by = user_id

        # Handle terminal states
        if new_state == GoalState.ACHIEVED:
            goal.progress = 1.0
            goal.achieved_date = datetime.utcnow()

        await self.db.flush()
        
        await logger.ainfo(
            "goal_transitioned",
            goal_id=goal_id,
            from_state=old_state.value,
            to_state=new_state.value,
            user_id=user_id,
        )
        
        return goal

    async def get_goal_hierarchy(self, goal_id: str) -> dict:
        """Get the full hierarchy for a goal."""
        goal = await self.get_goal(goal_id)
        if not goal:
            return {}

        # Get ancestors
        ancestors = []
        current = goal
        while current.parent_id:
            parent = await self.get_goal(current.parent_id)
            if parent:
                ancestors.insert(0, {
                    "id": parent.id,
                    "title": parent.title,
                    "state": parent.state.value,
                    "progress": parent.progress,
                })
                current = parent
            else:
                break

        # Get descendants
        async def get_children(parent_id: str) -> list:
            result = await self.db.execute(
                select(Goal).where(Goal.parent_id == parent_id)
            )
            children = result.scalars().all()
            child_list = []
            for child in children:
                child_data = {
                    "id": child.id,
                    "title": child.title,
                    "state": child.state.value,
                    "progress": child.progress,
                    "children": await get_children(child.id),
                }
                child_list.append(child_data)
            return child_list

        descendants = await get_children(goal_id)

        return {
            "goal": {
                "id": goal.id,
                "title": goal.title,
                "state": goal.state.value,
                "progress": goal.progress,
            },
            "ancestors": ancestors,
            "descendants": descendants,
        }

    async def update_progress(self, goal_id: str, progress: float, notes: Optional[str] = None) -> Optional[Goal]:
        """Update goal progress."""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        goal.progress = max(0.0, min(1.0, progress))  # Clamp to 0-1
        if notes:
            goal.progress_notes = notes

        # Auto-transition if progress reaches 100%
        if goal.progress >= 1.0 and goal.state == GoalState.ACTIVE:
            goal.state = GoalState.ACHIEVED
            goal.achieved_date = datetime.utcnow()

        await self.db.flush()
        return goal

    async def calculate_parent_progress(self, goal_id: str) -> float:
        """Calculate progress for a parent goal based on children."""
        result = await self.db.execute(
            select(Goal).where(Goal.parent_id == goal_id)
        )
        children = result.scalars().all()
        
        if not children:
            return 0.0

        total_progress = sum(child.progress for child in children)
        return total_progress / len(children)
