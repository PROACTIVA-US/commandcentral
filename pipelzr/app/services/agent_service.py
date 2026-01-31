"""
Agent Service - handles agent session lifecycle and execution.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models.agent import Agent, AgentState
from ..config import get_settings

logger = structlog.get_logger("pipelzr.agent_service")
settings = get_settings()


class AgentService:
    """Service for managing agent sessions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(
        self,
        name: str,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        skills: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        max_iterations: int = 100,
        timeout_seconds: int = 300,
        extra_data: Optional[dict] = None,
    ) -> Agent:
        """Create a new agent session."""
        agent = Agent(
            name=name,
            model=model,
            system_prompt=system_prompt,
            project_id=project_id,
            session_id=session_id,
            skills=skills or [],
            tools=tools or [],
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            extra_data=extra_data or {},
        )
        self.session.add(agent)
        await self.session.flush()
        
        await logger.ainfo(
            "agent_created",
            agent_id=agent.id,
            name=name,
            model=model,
        )
        
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def list_agents(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        state: Optional[AgentState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Agent]:
        """List agents with optional filters."""
        query = select(Agent)
        
        if project_id:
            query = query.where(Agent.project_id == project_id)
        if session_id:
            query = query.where(Agent.session_id == session_id)
        if state:
            query = query.where(Agent.state == state)
        
        query = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def transition_state(self, agent: Agent, new_state: AgentState) -> bool:
        """Transition agent to a new state."""
        if not agent.can_transition_to(new_state):
            await logger.awarning(
                "invalid_state_transition",
                agent_id=agent.id,
                current_state=agent.state.value,
                requested_state=new_state.value,
            )
            return False
        
        old_state = agent.state
        agent.state = new_state
        agent.state_changed_at = datetime.utcnow()
        
        await logger.ainfo(
            "agent_state_changed",
            agent_id=agent.id,
            old_state=old_state.value,
            new_state=new_state.value,
        )
        
        return True

    async def initialize_agent(self, agent: Agent) -> Agent:
        """Initialize an agent for execution."""
        await self.transition_state(agent, AgentState.INITIALIZING)
        agent.started_at = datetime.utcnow()
        
        try:
            # Load skills
            # TODO: Load skill definitions and inject into context
            
            # Set up tools
            # TODO: Initialize available tools
            
            await self.transition_state(agent, AgentState.RUNNING)
            
        except Exception as e:
            agent.error = str(e)
            agent.error_count += 1
            await self.transition_state(agent, AgentState.ERROR)
            
            await logger.aerror(
                "agent_initialization_failed",
                agent_id=agent.id,
                error=str(e),
            )
        
        return agent

    async def run_iteration(self, agent: Agent, user_input: Optional[str] = None) -> Agent:
        """Run a single agent iteration."""
        if agent.state not in [AgentState.RUNNING, AgentState.WAITING]:
            await logger.awarning(
                "agent_not_running",
                agent_id=agent.id,
                state=agent.state.value,
            )
            return agent
        
        if agent.iteration_count >= agent.max_iterations:
            await logger.awarning(
                "max_iterations_reached",
                agent_id=agent.id,
                iteration_count=agent.iteration_count,
            )
            await self.transition_state(agent, AgentState.IDLE)
            return agent
        
        try:
            agent.iteration_count += 1
            agent.last_active_at = datetime.utcnow()
            
            # Add user input to conversation if provided
            if user_input:
                agent.conversation = agent.conversation + [
                    {"role": "user", "content": user_input}
                ]
            
            # TODO: Call LLM with conversation history
            # TODO: Execute any tool calls
            # TODO: Add assistant response to conversation
            
            # For now, just log
            await logger.ainfo(
                "agent_iteration",
                agent_id=agent.id,
                iteration=agent.iteration_count,
            )
            
        except Exception as e:
            agent.error = str(e)
            agent.error_count += 1
            await self.transition_state(agent, AgentState.ERROR)
            
            await logger.aerror(
                "agent_iteration_failed",
                agent_id=agent.id,
                error=str(e),
            )
        
        return agent

    async def pause_agent(self, agent: Agent) -> bool:
        """Pause a running agent."""
        if agent.state != AgentState.RUNNING:
            return False
        return await self.transition_state(agent, AgentState.PAUSED)

    async def resume_agent(self, agent: Agent) -> bool:
        """Resume a paused agent."""
        if agent.state != AgentState.PAUSED:
            return False
        return await self.transition_state(agent, AgentState.RUNNING)

    async def terminate_agent(self, agent: Agent) -> bool:
        """Terminate an agent session."""
        if agent.state == AgentState.TERMINATED:
            return False
        return await self.transition_state(agent, AgentState.TERMINATED)

    async def update_tokens(
        self,
        agent: Agent,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float = 0.0,
    ):
        """Update token usage for an agent."""
        agent.input_tokens += input_tokens
        agent.output_tokens += output_tokens
        agent.total_cost_usd += cost_usd
        
        await logger.ainfo(
            "agent_tokens_updated",
            agent_id=agent.id,
            total_input=agent.input_tokens,
            total_output=agent.output_tokens,
            total_cost=agent.total_cost_usd,
        )
