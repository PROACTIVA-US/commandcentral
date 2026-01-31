"""
Graph exploration and discovery endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import ExplorationService
from ..models import NodeType, RelationshipType
from ..config import get_settings

router = APIRouter()
settings = get_settings()


# ==================== Request/Response Models ====================

class ExploreRequest(BaseModel):
    """Request model for graph exploration."""
    start_node_id: str
    depth: int = Field(2, ge=1, le=10)
    direction: str = Field("both", pattern="^(incoming|outgoing|both)$")
    relationship_types: Optional[List[RelationshipType]] = None
    node_types: Optional[List[NodeType]] = None
    max_nodes: int = Field(100, ge=1, le=500)


class PathFindRequest(BaseModel):
    """Request model for path finding."""
    start_node_id: str
    end_node_id: str
    max_depth: int = Field(5, ge=1, le=10)
    relationship_types: Optional[List[RelationshipType]] = None


class WanderRequest(BaseModel):
    """Request model for random walk exploration."""
    start_node_id: str
    steps: int = Field(10, ge=1, le=50)
    allow_backtrack: bool = False


class ClusterRequest(BaseModel):
    """Request model for finding clusters."""
    node_ids: List[str]
    min_connections: int = Field(2, ge=1)


class SearchRequest(BaseModel):
    """Request model for node search."""
    query: str = Field(..., min_length=1)
    node_types: Optional[List[NodeType]] = None
    limit: int = Field(20, ge=1, le=100)


# ==================== Endpoints ====================

@router.post("/explore")
async def explore_graph(
    request: ExploreRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Explore the graph starting from a node.
    
    Performs breadth-first traversal up to the specified depth,
    returning all discovered nodes and relationships.
    """
    service = ExplorationService(session)
    
    result = await service.explore_from_node(
        start_node_id=request.start_node_id,
        depth=request.depth,
        direction=request.direction,
        relationship_types=request.relationship_types,
        node_types=request.node_types,
        max_nodes=request.max_nodes,
    )
    
    return result.to_dict()


@router.post("/path")
async def find_path(
    request: PathFindRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Find the shortest path between two nodes.
    
    Uses BFS to find the shortest path, returning the
    sequence of node IDs from start to end.
    """
    service = ExplorationService(session)
    
    path = await service.find_path(
        start_node_id=request.start_node_id,
        end_node_id=request.end_node_id,
        max_depth=request.max_depth,
        relationship_types=request.relationship_types,
    )
    
    if path is None:
        return {
            "found": False,
            "path": [],
            "message": f"No path found within depth {request.max_depth}",
        }
    
    return {
        "found": True,
        "path": path,
        "length": len(path) - 1,  # Number of edges
    }


@router.post("/wander")
async def wander(
    request: WanderRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Perform a random walk through the graph.
    
    This is the "Wander" mode - exploring by following
    random connections to discover new areas of the graph.
    """
    service = ExplorationService(session)
    
    result = await service.wander(
        start_node_id=request.start_node_id,
        steps=request.steps,
        allow_backtrack=request.allow_backtrack,
    )
    
    return result.to_dict()


@router.post("/clusters")
async def find_clusters(
    request: ClusterRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Find clusters of densely connected nodes.
    
    Identifies groups of nodes that are tightly connected
    to each other within the provided set of nodes.
    """
    service = ExplorationService(session)
    
    clusters = await service.find_clusters(
        node_ids=request.node_ids,
        min_connections=request.min_connections,
    )
    
    return {
        "clusters": clusters,
        "cluster_count": len(clusters),
        "total_clustered_nodes": sum(len(c) for c in clusters),
    }


@router.post("/search")
async def search_nodes(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Search for nodes by label or description.
    
    Simple text search across node labels and descriptions.
    For full-text search, use a dedicated search service.
    """
    service = ExplorationService(session)
    
    nodes = await service.search_nodes(
        query=request.query,
        node_types=request.node_types,
        limit=request.limit,
    )
    
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@router.get("/search")
async def search_nodes_get(
    q: str = Query(..., min_length=1, description="Search query"),
    node_types: Optional[str] = Query(None, description="Comma-separated node types"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Search for nodes (GET method).
    
    Convenience endpoint for simple searches via query params.
    """
    service = ExplorationService(session)
    
    # Parse node types
    types = None
    if node_types:
        types = [NodeType(t.strip()) for t in node_types.split(",")]
    
    nodes = await service.search_nodes(
        query=q,
        node_types=types,
        limit=limit,
    )
    
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@router.get("/stats/{node_id}")
async def get_node_statistics(
    node_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get statistics about a node's connections.
    
    Returns information about the node's connectivity,
    including counts by relationship type and direction.
    """
    service = ExplorationService(session)
    stats = await service.get_node_statistics(node_id)
    return stats


@router.get("/neighbors/{node_id}")
async def get_neighbors(
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get immediate neighbors of a node.
    
    Convenience endpoint for quick neighbor lookups.
    """
    service = ExplorationService(session)
    
    result = await service.explore_from_node(
        start_node_id=node_id,
        depth=depth,
        direction=direction,
        max_nodes=50,
    )
    
    # Filter out the start node
    neighbors = [n for n in result.nodes if n.id != node_id]
    
    return {
        "node_id": node_id,
        "neighbors": [n.to_dict() for n in neighbors],
        "count": len(neighbors),
        "relationships": [r.to_dict() for r in result.relationships],
    }
