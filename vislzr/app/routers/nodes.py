"""
Node and relationship management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import NodeService
from ..models import NodeType, RelationshipType

router = APIRouter()


# ==================== Request/Response Models ====================

class PositionModel(BaseModel):
    """Position coordinates."""
    x: float = 0.0
    y: float = 0.0


class NodeCreate(BaseModel):
    """Request model for creating a node."""
    label: str = Field(..., min_length=1, max_length=255)
    node_type: NodeType = NodeType.ENTITY
    description: Optional[str] = None
    external_id: Optional[str] = None
    source_service: Optional[str] = None
    position: Optional[PositionModel] = None
    properties: Optional[dict] = None
    extra_data: Optional[dict] = None


class NodeUpdate(BaseModel):
    """Request model for updating a node."""
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    node_type: Optional[NodeType] = None
    position: Optional[PositionModel] = None
    size: Optional[float] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_hidden: Optional[bool] = None
    properties: Optional[dict] = None
    extra_data: Optional[dict] = None


class NodePositionUpdate(BaseModel):
    """Request model for updating node position."""
    x: float
    y: float


class RelationshipCreate(BaseModel):
    """Request model for creating a relationship."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType = RelationshipType.RELATED_TO
    label: Optional[str] = None
    description: Optional[str] = None
    weight: float = Field(1.0, ge=0.0, le=1.0)
    extra_data: Optional[dict] = None


class BulkNodesCreate(BaseModel):
    """Request model for bulk node creation."""
    nodes: List[NodeCreate]


class BulkRelationshipsCreate(BaseModel):
    """Request model for bulk relationship creation."""
    relationships: List[RelationshipCreate]


# ==================== Node Endpoints ====================

@router.post("")
async def create_node(
    request: NodeCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new node."""
    service = NodeService(session)
    node = await service.create_node(
        label=request.label,
        node_type=request.node_type,
        description=request.description,
        external_id=request.external_id,
        source_service=request.source_service,
        position=request.position.model_dump() if request.position else None,
        properties=request.properties,
        extra_data=request.extra_data,
    )
    return node.to_dict()


@router.get("")
async def list_nodes(
    node_types: Optional[str] = Query(None, description="Comma-separated node types"),
    source_service: Optional[str] = Query(None),
    include_hidden: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List nodes with optional filters."""
    service = NodeService(session)
    
    # Parse node types
    types = None
    if node_types:
        types = [NodeType(t.strip()) for t in node_types.split(",")]
    
    nodes = await service.list_nodes(
        node_types=types,
        source_service=source_service,
        include_hidden=include_hidden,
        limit=limit,
        offset=offset,
    )
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@router.get("/{node_id}")
async def get_node(
    node_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a node by ID."""
    service = NodeService(session)
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.get("/external/{external_id}")
async def get_node_by_external_id(
    external_id: str,
    source_service: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get a node by external ID."""
    service = NodeService(session)
    node = await service.get_node_by_external_id(external_id, source_service)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.patch("/{node_id}")
async def update_node(
    node_id: str,
    request: NodeUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a node."""
    service = NodeService(session)
    
    updates = request.model_dump(exclude_none=True)
    
    # Convert booleans to strings for database
    if "is_pinned" in updates:
        updates["is_pinned"] = "true" if updates["is_pinned"] else "false"
    if "is_hidden" in updates:
        updates["is_hidden"] = "true" if updates["is_hidden"] else "false"
    
    # Handle position
    if "position" in updates:
        pos = updates.pop("position")
        updates["position"] = {"x": pos.x, "y": pos.y} if isinstance(pos, PositionModel) else pos
    
    node = await service.update_node(node_id, **updates)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.put("/{node_id}/position")
async def update_node_position(
    node_id: str,
    request: NodePositionUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a node's position."""
    service = NodeService(session)
    node = await service.update_node_position(node_id, request.x, request.y)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a node and its relationships."""
    service = NodeService(session)
    deleted = await service.delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"deleted": True, "node_id": node_id}


@router.post("/bulk")
async def bulk_create_nodes(
    request: BulkNodesCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create multiple nodes at once."""
    service = NodeService(session)
    
    nodes_data = []
    for node_req in request.nodes:
        data = node_req.model_dump()
        if data.get("position"):
            data["x"] = data["position"]["x"]
            data["y"] = data["position"]["y"]
            del data["position"]
        nodes_data.append(data)
    
    nodes = await service.bulk_create_nodes(nodes_data)
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


# ==================== Relationship Endpoints ====================

@router.post("/relationships")
async def create_relationship(
    request: RelationshipCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a relationship between two nodes."""
    service = NodeService(session)
    
    # Verify both nodes exist
    source = await service.get_node(request.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source node not found")
    
    target = await service.get_node(request.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    relationship = await service.create_relationship(
        source_id=request.source_id,
        target_id=request.target_id,
        relationship_type=request.relationship_type,
        label=request.label,
        description=request.description,
        weight=request.weight,
        extra_data=request.extra_data,
    )
    return relationship.to_dict()


@router.get("/{node_id}/relationships")
async def get_node_relationships(
    node_id: str,
    direction: str = Query("both", regex="^(incoming|outgoing|both)$"),
    relationship_types: Optional[str] = Query(None, description="Comma-separated relationship types"),
    session: AsyncSession = Depends(get_session),
):
    """Get relationships for a node."""
    service = NodeService(session)
    
    # Parse relationship types
    types = None
    if relationship_types:
        types = [RelationshipType(t.strip()) for t in relationship_types.split(",")]
    
    relationships = await service.get_relationships_for_node(
        node_id=node_id,
        direction=direction,
        relationship_types=types,
    )
    return {"relationships": [r.to_dict() for r in relationships], "count": len(relationships)}


@router.get("/{node_id}/connected")
async def get_connected_nodes(
    node_id: str,
    direction: str = Query("both", regex="^(incoming|outgoing|both)$"),
    session: AsyncSession = Depends(get_session),
):
    """Get nodes connected to a given node."""
    service = NodeService(session)
    nodes = await service.get_connected_nodes(node_id, direction)
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a relationship."""
    service = NodeService(session)
    deleted = await service.delete_relationship(relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"deleted": True, "relationship_id": relationship_id}


@router.post("/relationships/bulk")
async def bulk_create_relationships(
    request: BulkRelationshipsCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create multiple relationships at once."""
    service = NodeService(session)
    
    relationships_data = [r.model_dump() for r in request.relationships]
    relationships = await service.bulk_create_relationships(relationships_data)
    return {"relationships": [r.to_dict() for r in relationships], "count": len(relationships)}
