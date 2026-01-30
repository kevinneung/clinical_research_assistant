"""Agent run model for tracking agent execution history."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .database import Base


class AgentRun(Base):
    """Record of an agent execution."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)  # orchestrator, project_manager, etc.
    prompt = Column(Text, nullable=False)
    output = Column(JSON)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    token_usage = Column(JSON)  # {prompt_tokens, completion_tokens, total_tokens}

    # Relationships
    project = relationship("Project", back_populates="runs")
    approvals = relationship("Approval", back_populates="agent_run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent_type='{self.agent_type}', status='{self.status}')>"

    def start(self) -> None:
        """Mark the run as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def complete(self, output: dict | str) -> None:
        """Mark the run as completed with output."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.output = output if isinstance(output, dict) else {"result": output}

    def fail(self, error: str) -> None:
        """Mark the run as failed with error message."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error
