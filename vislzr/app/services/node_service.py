"""
Node service for managing graph nodes and relationships.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Node, NodeType, Relationship, RelationshipType

logger = structlog.get_logger("vislzr.services.node")


class NodeService:
    """Service for managing nodes and relationships."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Node Operations ====================

    async def create_node(
        self,
        label: str,
        node_type: NodeType = NodeType.ENTITY,
        description: Optional[str] = None,
        external_id: Optional[str] = None,
        source_service: Optional[str] = None,
        position: Optional[Dict[str, float]] = None,
        properties: Optional[dict] = None,
        extra_data: Optional[dict] = None,
    ) -> Node:
        """Create a new node."""
        node = Node(
            label=label,
            node_type=node_type,
            description=description,
            external_id=external_id,
            source_service=source_service,
            x=position.get("x", 0.0) if position else 0.0,
            y=position.get("y", 0.0) if position else 0.0,
            properties=properties or {},
            extra_data=extra_data or {},
        )
        self.session.add(node)
        await self.session.flush()
        
        await logger.ainfo(
            "node_created",
            node_id=node.id,
            label=label,
            node_type=node_type.value,
        )
        
        return node

    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        result = await self.session.execute(
            select(Node).where(Node.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_node_by_external_id(
        self,
        external_id: str,
        source_service: Optional[str] = None,
    ) -> Optional[Node]:
        """Get a node by external ID."""
        query = select(Node).where(Node.external_id == external_id)
        if source_service:
            query = query.where(Node.source_service == source_service)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_nodes(
        self,
        node_types: Optional[List[NodeType]] = None,
        source_service: Optional[str] = None,
        include_hidden: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Node]:
        """List nodes with optional filters."""
        query = select(Node)
        
        if node_types:
            query = query.where(Node.node_type.in_(node_types))
        
        if source_service:
            query = query.where(Node.source_service == source_service)
        
        if not include_hidden:
            query = query.where(Node.is_hidden == "false")
        
        query = query.order_by(Node.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_node(
        self,
        node_id: str,
        **updates,
    ) -> Optional[Node]:
        """Update a node."""
        node = await self.get_node(node_id)
        if not node:
            return None
        
        # Handle position updates
        if "position" in updates:
            position = updates.pop("position")
            if position:
                updates["x"] = position.get("x", node.x)
                updates["y"] = position.get("y", node.y)
        
        for key, value in updates.items():
            if hasattr(node, key) and value is not None:
                setattr(node, key, value)
        
        node.updated_at = datetime.utcnow()
        
        await logger.ainfo(
            "node_updated",
            node_id=node_id,
            updates=list(updates.keys()),
        )
        
        return node

    async def update_node_position(
        self,
        node_id: str,
        x: float,
        y: float,
    ) -> Optional[Node]:
        """Update a node's position."""
        return await self.update_node(node_id, x=x, y=y)

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships."""
        # First delete relationships
        await self.session.execute(
            delete(Relationship).where(
                or_(
                    Relationship.source_id == node_id,
                    Relationship.target_id == node_id,
                )
            )
        )
        
        # Then delete node
        result = await self.session.execute(
            delete(Node).where(Node.id == node_id)
        )
        
        deleted = result.rowcount > 0
        if deleted:
            await logger.ainfo("node_deleted", node_id=node_id)
        
        return deleted

    async def bulk_create_nodes(
        self,
        nodes_data: List[Dict[str, Any]],
    ) -> List[Node]:
        """Create multiple nodes at once."""
        nodes = []
        for data in nodes_data:
            node = Node(
                label=data["label"],
                node_type=data.get("node_type", NodeType.ENTITY),
                description=data.get("description"),
                external_id=data.get("external_id"),
                source_service=data.get("source_service"),
                x=data.get("x", 0.0),
                y=data.get("y", 0.0),
                properties=data.get("properties", {}),
                extra_data=data.get("extra_data", {}),
            )
            nodes.append(node)
            self.session.add(node)
        
        await self.session.flush()
        
        await logger.ainfo(
            "nodes_bulk_created",
            count=len(nodes),
        )
        
        return nodes

    # ==================== Relationship Operations ====================

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType = RelationshipType.RELATED_TO,
        label: Optional[str] = None,
        description: Optional[str] = None,
        weight: float = 1.0,
        extra_data: Optional[dict] = None,
    ) -> Relationship:
        """Create a relationship between two nodes."""
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            label=label,
            description=description,
            weight=weight,
            extra_data=extra_data or {},
        )
        self.session.add(relationship)
        await self.session.flush()
        
        await logger.ainfo(
            "relationship_created",
            relationship_id=relationship.id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type.value,
        )
        
        return relationship

    async def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """Get a relationship by ID."""
        result = await self.session.execute(
            select(Relationship).where(Relationship.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def get_relationships_for_node(
        self,
        node_id: str,
        direction: str = "both",  # "outgoing", "incoming", "both"
        relationship_types: Optional[List[RelationshipType]] = None,
    ) -> List[Relationship]:
        """Get all relationships for a node."""
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

    async def get_connected_nodes(
        self,
        node_id: str,
        direction: str = "both",
        depth: int = 1,
    ) -> List[Node]:
        """Get nodes connected to a given node."""
        relationships = await self.get_relationships_for_node(node_id, direction)
        
        connected_ids = set()
        for rel in relationships:
            if rel.source_id != node_id:
                connected_ids.add(rel.source_id)
            if rel.target_id != node_id:
                connected_ids.add(rel.target_id)
        
        if not connected_ids:
            return []
        
        result = await self.session.execute(
            select(Node).where(Node.id.in_(connected_ids))
        )
        return list(result.scalars().all())

    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        result = await self.session.execute(
            delete(Relationship).where(Relationship.id == relationship_id)
        )
        
        deleted = result.rowcount > 0
        if deleted:
            await logger.ainfo("relationship_deleted", relationship_id=relationship_id)
        
        return deleted

    async def bulk_create_relationships(
        self,
        relationships_data: List[Dict[str, Any]],
    ) -> List[Relationship]:
        """Create multiple relationships at once."""
        relationships = []
        for data in relationships_data:
            rel = Relationship(
                source_id=data["source_id"],
                target_id=data["target_id"],
                relationship_type=data.get("relationship_type", RelationshipType.RELATED_TO),
                label=data.get("label"),
                description=data.get("description"),
                weight=data.get("weight", 1.0),
                extra_data=data.get("extra_data", {}),
            )
            relationships.append(rel)
            self.session.add(rel)
        
        await self.session.flush()
        
        await logger.ainfo(
            "relationships_bulk_created",
            count=len(relationships),
        )
        
        return relationships
