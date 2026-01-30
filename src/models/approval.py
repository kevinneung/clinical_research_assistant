"""Approval model for human-in-the-loop decisions."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class Approval(Base):
    """Record of a human approval decision."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    action_description = Column(Text, nullable=False)
    details = Column(JSON)
    approved = Column(Boolean)
    researcher_notes = Column(Text)
    requested_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="approvals")

    def __repr__(self) -> str:
        status = "approved" if self.approved else "denied" if self.approved is False else "pending"
        return f"<Approval(id={self.id}, status='{status}')>"

    def approve(self, notes: str | None = None) -> None:
        """Mark as approved."""
        self.approved = True
        self.decided_at = datetime.utcnow()
        if notes:
            self.researcher_notes = notes

    def deny(self, notes: str | None = None) -> None:
        """Mark as denied."""
        self.approved = False
        self.decided_at = datetime.utcnow()
        if notes:
            self.researcher_notes = notes
