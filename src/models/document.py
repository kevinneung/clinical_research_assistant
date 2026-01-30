"""Document model for generated document metadata."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .database import Base


class Document(Base):
    """Metadata for a generated document."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # ICF, Protocol, IB, etc.
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_by_agent = Column(String(50))  # Which agent created it
    extra_data = Column(JSON)  # Additional document-specific metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, type='{self.document_type}', title='{self.title}')>"
