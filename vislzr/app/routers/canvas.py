"""
Canvas management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import CanvasService
from ..models import LayoutType

router = APIRouter()


# ==================== Request/Response Models ====================

class CanvasCreate(BaseModel):
    """Request model for creating a canvas."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner_id: Optional[str] = None
    settings: Optional[dict] = None


class CanvasUpdate(BaseModel):
    """Request model for updating a canvas."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None
    is_public: Optional[bool] = None
    is_archived: Optional[bool] = None


class LayoutCreate(BaseModel):
    """Request model for creating a layout."""
    name: str = Field(..., min_length=1, max_length=255)
    layout_type: LayoutType = LayoutType.FORCE_DIRECTED
    positions: Optional[dict] = None
    parameters: Optional[dict] = None


class NodeIdsRequest(BaseModel):
    """Request model for adding/removing nodes."""
    node_ids: List[str]


# ==================== Endpoints ====================

@router.post("")
async def create_canvas(
    request: CanvasCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new visualization canvas."""
    service = CanvasService(session)
    canvas = await service.create_canvas(
        name=request.name,
        description=request.description,
        owner_id=request.owner_id,
        settings=request.settings,
    )
    return canvas.to_dict()


@router.get("")
async def list_canvases(
    owner_id: Optional[str] = Query(None),
    include_public: bool = Query(True),
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List canvases with optional filters."""
    service = CanvasService(session)
    canvases = await service.list_canvases(
        owner_id=owner_id,
        include_public=include_public,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return {"canvases": [c.to_dict() for c in canvases], "count": len(canvases)}


@router.get("/{canvas_id}")
async def get_canvas(
    canvas_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a canvas by ID."""
    service = CanvasService(session)
    canvas = await service.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas.to_dict()


@router.patch("/{canvas_id}")
async def update_canvas(
    canvas_id: str,
    request: CanvasUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a canvas."""
    service = CanvasService(session)
    
    updates = request.model_dump(exclude_none=True)
    
    # Convert booleans to strings for database
    if "is_public" in updates:
        updates["is_public"] = "true" if updates["is_public"] else "false"
    if "is_archived" in updates:
        updates["is_archived"] = "true" if updates["is_archived"] else "false"
    
    canvas = await service.update_canvas(canvas_id, **updates)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas.to_dict()


@router.delete("/{canvas_id}")
async def delete_canvas(
    canvas_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a canvas."""
    service = CanvasService(session)
    deleted = await service.delete_canvas(canvas_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return {"deleted": True, "canvas_id": canvas_id}


@router.post("/{canvas_id}/nodes")
async def add_nodes_to_canvas(
    canvas_id: str,
    request: NodeIdsRequest,
    session: AsyncSession = Depends(get_session),
):
    """Add nodes to a canvas."""
    service = CanvasService(session)
    canvas = await service.add_nodes_to_canvas(canvas_id, request.node_ids)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas.to_dict()


@router.delete("/{canvas_id}/nodes")
async def remove_nodes_from_canvas(
    canvas_id: str,
    request: NodeIdsRequest,
    session: AsyncSession = Depends(get_session),
):
    """Remove nodes from a canvas."""
    service = CanvasService(session)
    canvas = await service.remove_nodes_from_canvas(canvas_id, request.node_ids)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas.to_dict()


# ==================== Layout Endpoints ====================

@router.post("/{canvas_id}/layouts")
async def create_layout(
    canvas_id: str,
    request: LayoutCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new layout for a canvas."""
    service = CanvasService(session)
    
    # Verify canvas exists
    canvas = await service.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    layout = await service.create_layout(
        canvas_id=canvas_id,
        name=request.name,
        layout_type=request.layout_type,
        positions=request.positions,
        parameters=request.parameters,
    )
    return layout.to_dict()


@router.get("/{canvas_id}/layouts")
async def list_canvas_layouts(
    canvas_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List all layouts for a canvas."""
    service = CanvasService(session)
    layouts = await service.get_canvas_layouts(canvas_id)
    return {"layouts": [l.to_dict() for l in layouts], "count": len(layouts)}


@router.put("/{canvas_id}/layouts/{layout_id}/activate")
async def activate_layout(
    canvas_id: str,
    layout_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Set a layout as the active layout for a canvas."""
    service = CanvasService(session)
    canvas = await service.set_active_layout(canvas_id, layout_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas.to_dict()
