"""
Agent model - represents an AI agent session.

Agents execute tasks, manage context, and interact with codebases.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Integer, Float
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class AgentState(str, enum.Enum):
    """Agent lifecycle states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"  # Waiting for user input
    ERROR = "error"
    TERMINATED = "terminated"


# Valid state transitions
AGENT_TRANSITIONS = {
    AgentState.IDLE: [AgentState.INITIALIZING, AgentState.TERMINATED],
    AgentState.INITIALIZING: [AgentState.RUNNING, AgentState.ERROR, AgentState.TERMINATED],
    AgentState.RUNNING: [AgentState.PAUSED, AgentState.WAITING, AgentState.IDLE, AgentState.ERROR, AgentState.TERMINATED],
    AgentState.PAUSED: [AgentState.RUNNING, AgentState.TERMINATED],
    AgentState.WAITING: [AgentState.RUNNING, AgentState.TERMINATED],
    AgentState.ERROR: [AgentState.INITIALIZING, AgentState.TERMINATED],  # Can retry
    AgentState.TERMINATED: [],  # Terminal state
}


class Agent(Base):
    """
    Agent - an AI agent session that executes tasks.

    Agents maintain context, conversation history, and can
    interact with codebases and external tools.
    """

    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Agent configuration
    model = Column(String, default="claude-sonnet-4-20250514")
    system_prompt = Column(Text, nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    
    # Skills and capabilities
    skills = Column(JSON, default=list)  # List of skill IDs
    tools = Column(JSON, default=list)   # List of enabled tools

    # State machine
    state = Column(SQLEnum(AgentState), default=AgentState.IDLE, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    
    # Ownership
    project_id = Column(String, nullable=True, index=True)  # CommandCentral project
    session_id = Column(String, nullable=True, index=True)  # User session

    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    iteration_count = Column(Integer, default=0)
    max_iterations = Column(Integer, default=100)
    
    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # Context
    context = Column(JSON, default=dict)         # Current context
    conversation = Column(JSON, default=list)    # Conversation history
    working_directory = Column(String, nullable=True)

    # Error tracking
    error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Configuration
    timeout_seconds = Column(Integer, default=300)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Agent {self.name} ({self.state.value})>"

    def can_transition_to(self, new_state: AgentState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in AGENT_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[AgentState]:
        """Get list of allowed transitions from current state."""
        return AGENT_TRANSITIONS.get(self.state, [])
