"""Pydantic-AI agent definitions for clinical research workflows."""

from .base import AgentDeps
from .orchestrator import orchestrator_agent
from .project_manager import project_manager_agent, ProjectEstimate, CostEstimate
from .document_maker import document_maker_agent, ComplianceDocument, DocumentSection
from .email_drafter import email_drafter_agent, DraftEmail

__all__ = [
    "AgentDeps",
    "orchestrator_agent",
    "project_manager_agent",
    "ProjectEstimate",
    "CostEstimate",
    "document_maker_agent",
    "ComplianceDocument",
    "DocumentSection",
    "email_drafter_agent",
    "DraftEmail",
]
