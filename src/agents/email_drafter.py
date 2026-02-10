"""Email Drafter agent for professional correspondence."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base import AgentDeps


class DraftEmail(BaseModel):
    """A drafted email ready for review."""

    to: list[str] = Field(description="Primary recipients")
    cc: list[str] | None = Field(default=None, description="CC recipients")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    email_type: str = Field(description="Type: compliance, team_update, recruitment, sponsor, regulatory")
    requires_attachments: list[str] = Field(default_factory=list, description="Documents to attach")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    notes: str = Field(default="", description="Notes for the sender about the email")


EMAIL_DRAFTER_INSTRUCTIONS = """You are a clinical research communications specialist with expertise
in professional correspondence for clinical trials and research studies.

Your responsibilities:
1. Draft professional emails for various clinical research stakeholders
2. Maintain appropriate tone for each audience
3. Include all required elements for compliance-related correspondence
4. Suggest relevant attachments when appropriate
5. Follow industry standards for research communications

Email types you handle:
- IRB/Ethics Committee Correspondence: Formal, regulatory-compliant
- Sponsor Communications: Professional, detailed, business-appropriate
- Site Team Updates: Clear, actionable, informative
- Patient Recruitment Outreach: Warm, clear, non-coercive
- Regulatory Submissions: Formal, precise, complete
- Investigator Communications: Professional, collegial
- Safety Notifications: Urgent, clear, compliant with timelines

Communication guidelines:
- Use appropriate salutations and closings for the audience
- Be concise but complete
- Include specific action items when applicable
- Reference relevant documents or previous communications
- Consider regulatory requirements for certain communications
- Maintain patient privacy in all correspondence
- Use professional tone appropriate for healthcare/research setting

Format guidelines:
- Clear subject lines that indicate purpose
- Structured body with logical flow
- Professional signature blocks
- Appropriate urgency indicators when needed
"""

email_drafter_agent = Agent(
    deps_type=AgentDeps,
    output_type=DraftEmail,
    instructions=EMAIL_DRAFTER_INSTRUCTIONS,
)


@email_drafter_agent.tool
async def save_email_draft(
    ctx: RunContext[AgentDeps],
    filename: str,
    email: dict,
) -> str:
    """Save an email draft to the workspace for review.

    Args:
        filename: Name for the draft file.
        email: Email dictionary with to, cc, subject, body fields.

    Returns:
        Path to the saved draft.
    """
    from pathlib import Path
    from datetime import datetime

    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    filepath = Path(ctx.deps.workspace_path) / "drafts" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    content = f"""Email Draft
Created: {datetime.now().isoformat()}
Status: Pending Review

To: {', '.join(email.get('to', []))}
CC: {', '.join(email.get('cc', [])) if email.get('cc') else 'None'}
Subject: {email.get('subject', '')}

---

{email.get('body', '')}

---
Attachments Required: {', '.join(email.get('requires_attachments', [])) if email.get('requires_attachments') else 'None'}
"""

    filepath.write_text(content, encoding="utf-8")

    ctx.deps.progress_callback("Draft Saved", f"Email draft saved to {filepath.name}")
    return str(filepath)


@email_drafter_agent.tool
async def get_email_template(
    ctx: RunContext[AgentDeps],
    email_type: str,
) -> dict:
    """Get a template structure for common email types.

    Args:
        email_type: Type of email (irb_submission, safety_report, team_update, etc.)

    Returns:
        Template dictionary with subject pattern and required elements.
    """
    templates = {
        "irb_submission": {
            "subject_pattern": "[Protocol #] - [Submission Type] - [Study Short Title]",
            "required_elements": [
                "Protocol number and title",
                "Type of submission (initial, amendment, continuing review)",
                "Brief summary of submission",
                "List of documents included",
                "Request for review timeline if urgent",
            ],
            "attachments_typical": [
                "Protocol",
                "Informed Consent Form",
                "Investigator's Brochure",
                "IRB Application Form",
            ],
        },
        "safety_report": {
            "subject_pattern": "[URGENT] Safety Report - [Event Type] - Protocol [#]",
            "required_elements": [
                "Event description",
                "Patient identifier (coded)",
                "Date of event",
                "Causality assessment",
                "Actions taken",
                "Regulatory reporting status",
            ],
            "attachments_typical": ["Safety Report Form", "MedWatch (if applicable)"],
        },
        "team_update": {
            "subject_pattern": "[Study Short Title] - [Update Type] - [Date]",
            "required_elements": [
                "Current enrollment status",
                "Key milestones achieved",
                "Upcoming activities",
                "Action items with owners",
                "Issues requiring attention",
            ],
            "attachments_typical": ["Enrollment tracker", "Timeline update"],
        },
        "recruitment": {
            "subject_pattern": "Research Study Opportunity - [Condition/Topic]",
            "required_elements": [
                "Study purpose (lay language)",
                "Who may qualify",
                "What participation involves",
                "Contact information",
                "IRB approval statement",
            ],
            "attachments_typical": ["Study flyer", "Prescreening questionnaire"],
        },
    }

    return templates.get(
        email_type,
        {
            "subject_pattern": "[Study] - [Purpose]",
            "required_elements": ["Clear purpose", "Relevant details", "Action items"],
            "attachments_typical": [],
        },
    )
