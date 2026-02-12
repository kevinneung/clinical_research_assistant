"""Document Maker agent for compliance document drafting."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base import AgentDeps


class DocumentSection(BaseModel):
    """A section within a compliance document."""

    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    is_placeholder: bool = Field(default=False, description="Whether this needs study-specific details")
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation reference")


class ComplianceDocument(BaseModel):
    """A generated compliance document."""

    document_type: str = Field(description="Type of document (ICF, Protocol, IB, IRB Application, etc.)")
    title: str = Field(description="Document title")
    version: str = Field(default="1.0", description="Document version")
    sections: list[DocumentSection] = Field(description="Document sections")
    regulatory_references: list[str] = Field(default_factory=list, description="Applicable regulations")
    file_path: str = Field(description="Path to the saved document")
    notes: str = Field(default="", description="Notes about placeholders or required customizations")


DOCUMENT_MAKER_INSTRUCTIONS = """You are a clinical research documentation specialist with expertise
in regulatory compliance documents for clinical trials.

Your responsibilities:
1. Identify required compliance documents based on study requirements
2. Draft documents following regulatory formatting requirements
3. Include all required sections and elements per FDA/ICH-GCP guidelines
4. Mark sections that need study-specific customization as placeholders
5. Reference applicable regulations for each document type

Common document types you create:
- Informed Consent Form (ICF) - Per 21 CFR 50, ICH E6(R2)
- Study Protocol - Per ICH E6(R2) guidelines
- Investigator's Brochure (IB) - Per ICH E7
- IRB/Ethics Application - Institution-specific
- Case Report Forms (CRF) - Per study design
- Safety Reports (SAE, SUSAR) - Per ICH E2A
- Monitoring Plans - Per ICH E6(R2)
- Data Management Plans

Document guidelines:
- Use clear, professional language appropriate for regulatory review
- Include version numbers and document control information
- Structure documents according to regulatory templates
- Identify all placeholders clearly with [PLACEHOLDER: description]
- Include signature lines where required
- Reference specific regulatory sections where applicable

File organization:
- Save documents with descriptive names in the workspace
- Use markdown format for drafts (.md)
- Include document metadata at the top
"""

def _get_document_maker_instructions(ctx: RunContext[AgentDeps]) -> str:
    """Return document maker instructions, appending any user customizations."""
    from src.services.prompt_store import PromptStore

    custom = PromptStore().get("document_maker")
    if custom:
        return DOCUMENT_MAKER_INSTRUCTIONS + f"\n\n## Additional User Instructions\n{custom}"
    return DOCUMENT_MAKER_INSTRUCTIONS


document_maker_agent = Agent(
    deps_type=AgentDeps,
    output_type=ComplianceDocument,
    instructions=_get_document_maker_instructions,
)


@document_maker_agent.tool
async def save_document(
    ctx: RunContext[AgentDeps],
    filename: str,
    content: str,
    document_type: str,
) -> str:
    """Save a document to the workspace.

    Args:
        filename: Name for the document file.
        content: Full document content.
        document_type: Type of document being saved.

    Returns:
        Path to the saved document.
    """
    from pathlib import Path
    from datetime import datetime

    # Ensure .md extension for draft documents
    if not filename.endswith((".md", ".txt", ".docx")):
        filename = f"{filename}.md"

    filepath = Path(ctx.deps.workspace_path) / filename

    # Add metadata header
    header = f"""---
document_type: {document_type}
created: {datetime.now().isoformat()}
version: 1.0
status: draft
---

"""
    full_content = header + content

    filepath.write_text(full_content, encoding="utf-8")

    ctx.deps.progress_callback("Document Saved", f"{document_type} saved to {filename}")
    return str(filepath)


@document_maker_agent.tool
async def list_required_documents(
    ctx: RunContext[AgentDeps],
    study_phase: str,
    therapeutic_area: str,
) -> list[dict]:
    """List required regulatory documents for a study.

    Args:
        study_phase: Clinical trial phase (1, 2, 3, 4, or observational).
        therapeutic_area: Therapeutic area of the study.

    Returns:
        List of required documents with descriptions and regulatory references.
    """
    # Base documents required for all interventional studies
    base_docs = [
        {
            "type": "Protocol",
            "required": True,
            "reference": "ICH E6(R2) Section 6",
            "description": "Study protocol with objectives, design, methodology",
        },
        {
            "type": "Informed Consent Form",
            "required": True,
            "reference": "21 CFR 50, ICH E6(R2) 4.8",
            "description": "Patient consent document",
        },
        {
            "type": "Investigator's Brochure",
            "required": True,
            "reference": "ICH E7",
            "description": "Compilation of clinical and nonclinical data",
        },
        {
            "type": "IRB Application",
            "required": True,
            "reference": "21 CFR 56",
            "description": "Institutional Review Board submission",
        },
    ]

    # Phase-specific additions
    phase_docs = {
        "1": [
            {"type": "First-in-Human Protocol Addendum", "required": True, "reference": "ICH M3(R2)"},
        ],
        "3": [
            {"type": "Statistical Analysis Plan", "required": True, "reference": "ICH E9"},
            {"type": "Data Management Plan", "required": True, "reference": "ICH E6(R2) 5.5"},
        ],
    }

    docs = base_docs.copy()
    if study_phase in phase_docs:
        docs.extend(phase_docs[study_phase])

    return docs


@document_maker_agent.tool
async def get_icf_template_sections(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Get the required sections for an Informed Consent Form per 21 CFR 50.

    Returns:
        List of required ICF sections with descriptions.
    """
    return [
        {"section": "Study Title and Purpose", "required": True},
        {"section": "Study Procedures", "required": True},
        {"section": "Risks and Discomforts", "required": True},
        {"section": "Benefits", "required": True},
        {"section": "Alternatives to Participation", "required": True},
        {"section": "Confidentiality", "required": True},
        {"section": "Costs and Compensation", "required": True},
        {"section": "Voluntary Participation", "required": True},
        {"section": "Contact Information", "required": True},
        {"section": "Signature Lines", "required": True},
    ]
