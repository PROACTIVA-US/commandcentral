"""
Exploration service for graph traversal and discovery.
"""

from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import structlog

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Node, NodeType, Relationship, RelationshipType
from ..config import get_settings

logger = structlog.get_logger("vislzr.services.exploration")
settings = get_settings()


@dataclass
class ExplorationResult:
    """Result of a graph exploration query."""
    nodes: List[Node] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)  # List of node ID paths
    depth_reached: int = 0
    total_nodes_explored: int = 0

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "paths": self.paths,
            "depth_reached": self.depth_reached,
            "total_nodes_explored": self.total_nodes_explored,
        }


@dataclass
class WanderResult:
    """Result of a wander exploration (random walk)."""
    path: List[Node] = field(default_factory=list)
    relationships_traversed: List[Relationship] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)  # Interesting findings

    def to_dict(self) -> dict:
        return {
            "path": [n.to_dict() for n in self.path],
            "relationships_traversed": [r.to_dict() for r in self.relationships_traversed],
            "discoveries": self.discoveries,
        }


class ExplorationService:
    """Service for graph exploration and discovery."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def explore_from_node(
        self,
        start_node_id: str,
        depth: int = 2,
        direction: str = "both",
        relationship_types: Optional[List[RelationshipType]] = None,
        node_types: Optional[List[NodeType]] = None,
        max_nodes: int = 100,
    ) -> ExplorationResult:
        """
        Explore the graph starting from a node.
        
        Performs breadth-first traversal up to specified depth.
        """
        depth = min(depth, settings.max_depth)
        
        result = ExplorationResult()
        visited_nodes: Set[str] = set()
        visited_relationships: Set[str] = set()
        current_frontier: Set[str] = {start_node_id}
        
        for current_depth in range(depth + 1):
            if not current_frontier or len(visited_nodes) >= max_nodes:
                break
            
            result.depth_reached = current_depth
            
            # Fetch nodes in current frontier
            nodes_result = await self.session.execute(
                select(Node).where(Node.id.in_(current_frontier))
            )
            frontier_nodes = list(nodes_result.scalars().all())
            
            # Filter by node types if specified
            if node_types:
                frontier_nodes = [n for n in frontier_nodes if n.node_type in node_types]
            
            for node in frontier_nodes:
                if node.id not in visited_nodes:
                    visited_nodes.add(node.id)
                    result.nodes.append(node)
            
            if current_depth == depth:
                break
            
            # Get relationships for frontier nodes
            next_frontier: Set[str] = set()
            
            for node_id in current_frontier:
                relationships = await self._get_relationships(
                    node_id, direction, relationship_types
                )
                
                for rel in relationships:
                    if rel.id not in visited_relationships:
                        visited_relationships.add(rel.id)
                        result.relationships.append(rel)
                        
                        # Add connected nodes to next frontier
                        if rel.source_id != node_id:
                            next_frontier.add(rel.source_id)
                        if rel.target_id != node_id:
                            next_frontier.add(rel.target_id)
            
            # Remove already visited nodes from frontier
            next_frontier -= visited_nodes
            current_frontier = next_frontier
        
        result.total_nodes_explored = len(visited_nodes)
        
        await logger.ainfo(
            "exploration_completed",
            start_node_id=start_node_id,
            depth=depth,
            nodes_found=len(result.nodes),
            relationships_found=len(result.relationships),
        )
        
        return result

    async def find_path(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 5,
        relationship_types: Optional[List[RelationshipType]] = None,
    ) -> Optional[List[str]]:
        """
        Find the shortest path between two nodes.
        
        Uses BFS to find shortest path.
        """
        if start_node_id == end_node_id:
            return [start_node_id]
        
        max_depth = min(max_depth, settings.max_depth)
        
        visited: Set[str] = {start_node_id}
        queue: List[Tuple[str, List[str]]] = [(start_node_id, [start_node_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                break
            
            # Get neighbors
            relationships = await self._get_relationships(
                current_id, "both", relationship_types
            )
            
            for rel in relationships:
                neighbor_id = rel.target_id if rel.source_id == current_id else rel.source_id
                
                if neighbor_id == end_node_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None  # No path found

    async def wander(
        self,
        start_node_id: str,
        steps: int = 10,
        allow_backtrack: bool = False,
    ) -> WanderResult:
        """
        Perform a random walk through the graph.
        
        This is the "Wander" navigation mode - exploring
        by following random connections.
        """
        import random
        
        result = WanderResult()
        current_node_id = start_node_id
        visited: Set[str] = set()
        
        for _ in range(steps):
            # Get current node
            node_result = await self.session.execute(
                select(Node).where(Node.id == current_node_id)
            )
            current_node = node_result.scalar_one_or_none()
            
            if not current_node:
                break
            
            result.path.append(current_node)
            visited.add(current_node_id)
            
            # Get relationships
            relationships = await self._get_relationships(current_node_id, "both")
            
            if not relationships:
                result.discoveries.append(f"Dead end reached at '{current_node.label}'")
                break
            
            # Filter out visited if no backtracking
            if not allow_backtrack:
                valid_rels = []
                for rel in relationships:
                    next_id = rel.target_id if rel.source_id == current_node_id else rel.source_id
                    if next_id not in visited:
                        valid_rels.append(rel)
                relationships = valid_rels
            
            if not relationships:
                result.discoveries.append(f"No unvisited paths from '{current_node.label}'")
                break
            
            # Pick random relationship to follow
            chosen_rel = random.choice(relationships)
            result.relationships_traversed.append(chosen_rel)
            
            # Move to next node
            current_node_id = (
                chosen_rel.target_id
                if chosen_rel.source_id == current_node_id
                else chosen_rel.source_id
            )
        
        await logger.ainfo(
            "wander_completed",
            start_node_id=start_node_id,
            steps_taken=len(result.path),
            discoveries=len(result.discoveries),
        )
        
        return result

    async def find_clusters(
        self,
        node_ids: List[str],
        min_connections: int = 2,
    ) -> List[List[str]]:
        """
        Find clusters of densely connected nodes.
        
        Simple clustering based on connection density.
        """
        # Build adjacency map
        adjacency: Dict[str, Set[str]] = {node_id: set() for node_id in node_ids}
        
        for node_id in node_ids:
            relationships = await self._get_relationships(node_id, "both")
            for rel in relationships:
                other_id = rel.target_id if rel.source_id == node_id else rel.source_id
                if other_id in adjacency:
                    adjacency[node_id].add(other_id)
        
        # Find connected components
        visited: Set[str] = set()
        clusters: List[List[str]] = []
        
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            if len(adjacency[node_id]) < min_connections:
                continue
            
            # BFS to find cluster
            cluster: List[str] = []
            queue = [node_id]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                cluster.append(current)
                
                for neighbor in adjacency[current]:
                    if neighbor not in visited and len(adjacency[neighbor]) >= min_connections:
                        queue.append(neighbor)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        return clusters

    async def search_nodes(
        self,
        query: str,
        node_types: Optional[List[NodeType]] = None,
        limit: int = 20,
    ) -> List[Node]:
        """
        Search for nodes by label or description.
        
        Simple text search (for full-text, use a dedicated search service).
        """
        search_pattern = f"%{query}%"
        
        stmt = select(Node).where(
            or_(
                Node.label.ilike(search_pattern),
                Node.description.ilike(search_pattern),
            )
        )
        
        if node_types:
            stmt = stmt.where(Node.node_type.in_(node_types))
        
        stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_node_statistics(self, node_id: str) -> Dict[str, Any]:
        """Get statistics about a node's connections."""
        # Count relationships by type
        relationships = await self._get_relationships(node_id, "both")
        
        incoming = [r for r in relationships if r.target_id == node_id]
        outgoing = [r for r in relationships if r.source_id == node_id]
        
        type_counts: Dict[str, int] = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value if rel.relationship_type else "unknown"
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        
        return {
            "node_id": node_id,
            "total_connections": len(relationships),
            "incoming_connections": len(incoming),
            "outgoing_connections": len(outgoing),
            "connection_types": type_counts,
            "is_hub": len(relationships) > 10,  # Arbitrary threshold
            "is_leaf": len(relationships) <= 1,
        }

    async def _get_relationships(
        self,
        node_id: str,
        direction: str = "both",
        relationship_types: Optional[List[RelationshipType]] = None,
    ) -> List[Relationship]:
        """Helper to get relationships for a node."""
        query = select(Relationship)
        
        if direction == "outgoing":
            query = query.where(Relationship.source_id == node_id)
        elif direction == "incoming":
            query = query.where(Relationship.target_id == node_id)
        else:  # both
            query = query.where(
                or_(
                    Relationship.source_id == node_id,
                    Relationship.target_id == node_id,
                )
            )
        
        if relationship_types:
            query = query.where(Relationship.relationship_type.in_(relationship_types))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
