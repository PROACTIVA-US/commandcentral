"""
Canvas service for managing visualization canvases.
"""

from typing import List, Optional
from datetime import datetime
import structlog

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Canvas, Layout, LayoutType

logger = structlog.get_logger("vislzr.services.canvas")


class CanvasService:
    """Service for managing visualization canvases."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_canvas(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Canvas:
        """Create a new canvas."""
        canvas = Canvas(
            name=name,
            description=description,
            owner_id=owner_id,
            settings=settings or {},
        )
        self.session.add(canvas)
        await self.session.flush()
        
        await logger.ainfo(
            "canvas_created",
            canvas_id=canvas.id,
            name=name,
            owner_id=owner_id,
        )
        
        return canvas

    async def get_canvas(self, canvas_id: str) -> Optional[Canvas]:
        """Get a canvas by ID."""
        result = await self.session.execute(
            select(Canvas).where(Canvas.id == canvas_id)
        )
        canvas = result.scalar_one_or_none()
        
        if canvas:
            # Update last accessed time
            canvas.last_accessed_at = datetime.utcnow()
            
        return canvas

    async def list_canvases(
        self,
        owner_id: Optional[str] = None,
        include_public: bool = True,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Canvas]:
        """List canvases with optional filters."""
        query = select(Canvas)
        
        conditions = []
        if owner_id:
            if include_public:
                conditions.append(
                    (Canvas.owner_id == owner_id) | (Canvas.is_public == "true")
                )
            else:
                conditions.append(Canvas.owner_id == owner_id)
        
        if not include_archived:
            conditions.append(Canvas.is_archived == "false")
        
        for condition in conditions:
            query = query.where(condition)
        
        query = query.order_by(Canvas.updated_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_canvas(
        self,
        canvas_id: str,
        **updates,
    ) -> Optional[Canvas]:
        """Update a canvas."""
        canvas = await self.get_canvas(canvas_id)
        if not canvas:
            return None
        
        for key, value in updates.items():
            if hasattr(canvas, key) and value is not None:
                setattr(canvas, key, value)
        
        canvas.updated_at = datetime.utcnow()
        
        await logger.ainfo(
            "canvas_updated",
            canvas_id=canvas_id,
            updates=list(updates.keys()),
        )
        
        return canvas

    async def delete_canvas(self, canvas_id: str) -> bool:
        """Delete a canvas."""
        result = await self.session.execute(
            delete(Canvas).where(Canvas.id == canvas_id)
        )
        
        deleted = result.rowcount > 0
        if deleted:
            await logger.ainfo("canvas_deleted", canvas_id=canvas_id)
        
        return deleted

    async def add_nodes_to_canvas(
        self,
        canvas_id: str,
        node_ids: List[str],
    ) -> Optional[Canvas]:
        """Add nodes to a canvas."""
        canvas = await self.get_canvas(canvas_id)
        if not canvas:
            return None
        
        current_nodes = set(canvas.node_ids or [])
        current_nodes.update(node_ids)
        canvas.node_ids = list(current_nodes)
        canvas.node_count = len(canvas.node_ids)
        canvas.updated_at = datetime.utcnow()
        
        await logger.ainfo(
            "nodes_added_to_canvas",
            canvas_id=canvas_id,
            node_count=len(node_ids),
        )
        
        return canvas

    async def remove_nodes_from_canvas(
        self,
        canvas_id: str,
        node_ids: List[str],
    ) -> Optional[Canvas]:
        """Remove nodes from a canvas."""
        canvas = await self.get_canvas(canvas_id)
        if not canvas:
            return None
        
        current_nodes = set(canvas.node_ids or [])
        current_nodes -= set(node_ids)
        canvas.node_ids = list(current_nodes)
        canvas.node_count = len(canvas.node_ids)
        canvas.updated_at = datetime.utcnow()
        
        await logger.ainfo(
            "nodes_removed_from_canvas",
            canvas_id=canvas_id,
            node_count=len(node_ids),
        )
        
        return canvas

    async def create_layout(
        self,
        canvas_id: str,
        name: str,
        layout_type: LayoutType = LayoutType.FORCE_DIRECTED,
        positions: Optional[dict] = None,
        parameters: Optional[dict] = None,
    ) -> Layout:
        """Create a new layout for a canvas."""
        layout = Layout(
            name=name,
            canvas_id=canvas_id,
            layout_type=layout_type,
            positions=positions or {},
            parameters=parameters or {},
        )
        self.session.add(layout)
        await self.session.flush()
        
        await logger.ainfo(
            "layout_created",
            layout_id=layout.id,
            canvas_id=canvas_id,
            layout_type=layout_type.value,
        )
        
        return layout

    async def get_canvas_layouts(self, canvas_id: str) -> List[Layout]:
        """Get all layouts for a canvas."""
        result = await self.session.execute(
            select(Layout)
            .where(Layout.canvas_id == canvas_id)
            .order_by(Layout.created_at.desc())
        )
        return list(result.scalars().all())

    async def set_active_layout(
        self,
        canvas_id: str,
        layout_id: str,
    ) -> Optional[Canvas]:
        """Set the active layout for a canvas."""
        canvas = await self.get_canvas(canvas_id)
        if not canvas:
            return None
        
        canvas.active_layout_id = layout_id
        canvas.updated_at = datetime.utcnow()
        
        return canvas
