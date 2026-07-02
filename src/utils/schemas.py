"""
Pydantic models and data schemas for SmartMail AI.

Defines all data structures used throughout the application:
- Email data models
- Classification results
- RAG contexts
- Calendar events
- LangGraph state
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


# ============ Email Type & Priority Enums ============
class EmailType(str, Enum):
    """Email classification types."""
    GENERAL_EMAIL = "general_email"
    MEETING_REQUEST = "meeting_request"
    URGENT = "urgent"
    FOLLOW_UP = "follow_up"
    NEWSLETTER = "newsletter"
    AUTOMATED = "automated"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailIntent(str, Enum):
    """Email intent/action type."""
    INFORMATIONAL = "informational"
    REQUIRES_RESPONSE = "requires_response"
    REQUIRES_ACTION = "requires_action"
    REQUIRES_DECISION = "requires_decision"
    SCHEDULING = "scheduling"


# ============ Raw Email Data ============
class EmailData(BaseModel):
    """Raw email data from Gmail API."""

    email_id: str = Field(..., description="Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Sender email address")
    sender_name: Optional[str] = Field(default=None, description="Sender display name")
    to: List[str] = Field(default_factory=list, description="Recipient email addresses")
    cc: List[str] = Field(default_factory=list, description="CC email addresses")
    bcc: List[str] = Field(default_factory=list, description="BCC email addresses")
    body: str = Field(..., description="Email body text")
    html_body: Optional[str] = Field(default=None, description="Email HTML body")
    received_at: datetime = Field(..., description="Email received timestamp")
    is_reply: bool = Field(default=False, description="Whether email is a reply")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    attachments: List[str] = Field(default_factory=list, description="Attachment names")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email_id": "msg_12345",
                "thread_id": "thread_67890",
                "subject": "Project Update",
                "sender": "john@example.com",
                "body": "Here's the update..."
            }
        }


# ============ Classification Result ============
class ClassificationResult(BaseModel):
    """Email classification output."""

    email_id: str = Field(..., description="Gmail message ID")
    email_type: EmailType = Field(..., description="Classification type")
    priority: EmailPriority = Field(..., description="Priority level")
    intent: EmailIntent = Field(..., description="Email intent")
    type_confidence: float = Field(..., description="Type classification confidence (0-1)")
    priority_confidence: float = Field(..., description="Priority classification confidence (0-1)")
    intent_confidence: float = Field(..., description="Intent classification confidence (0-1)")
    reasoning: str = Field(..., description="Explanation of classification")
    requires_human_review: bool = Field(
        default=False,
        description="Whether human review is needed"
    )
    category_tags: List[str] = Field(
        default_factory=list,
        description="Additional category tags"
    )


# ============ RAG Context ============
class RAGContext(BaseModel):
    """Retrieved context from RAG system."""

    source_email_id: str = Field(..., description="Source email ID")
    subject: str = Field(..., description="Source email subject")
    snippet: str = Field(..., description="Relevant text snippet")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    sender: str = Field(..., description="Sender of source email")
    received_at: datetime = Field(..., description="When source email was received")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


# ============ Summarization & Action Extraction ============
class ActionItem(BaseModel):
    """Extracted action item."""

    action: str = Field(..., description="Action description")
    assigned_to: Optional[str] = Field(default=None, description="Who is assigned")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    priority: EmailPriority = Field(default=EmailPriority.NORMAL, description="Priority")
    status: str = Field(default="pending", description="Current status")


class SummaryResult(BaseModel):
    """Summarization and action extraction output."""

    email_id: str = Field(..., description="Gmail message ID")
    summary: str = Field(..., description="Email summary (2-3 sentences)")
    key_points: List[str] = Field(..., description="Key points (3-5 bullets)")
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Extracted action items"
    )
    sentiment: str = Field(
        default="neutral",
        description="Email sentiment (positive/neutral/negative)"
    )
    entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Named entities (people, dates, locations)"
    )


# ============ Reply Generation ============
class ReplyDraft(BaseModel):
    """Generated email reply draft."""

    email_id: str = Field(..., description="Original email ID")
    reply_text: str = Field(..., description="Reply draft text")
    tone: str = Field(default="professional", description="Reply tone")
    confidence: float = Field(..., description="Reply quality confidence (0-1)")
    requires_editing: bool = Field(
        default=False,
        description="Whether human editing is needed"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )


# ============ Calendar Event ============
class CalendarEventData(BaseModel):
    """Calendar event to be created."""

    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    attendees: List[str] = Field(default_factory=list, description="Attendee emails")
    location: Optional[str] = Field(default=None, description="Event location")
    timezone: str = Field(default="UTC", description="Event timezone")
    source_email_id: str = Field(..., description="Source email ID")
    confidence: float = Field(..., description="Event detection confidence (0-1)")
    requires_confirmation: bool = Field(
        default=True,
        description="Needs confirmation before creation"
    )


# ============ LangGraph State ============
class GraphState(BaseModel):
    """LangGraph workflow state."""

    # Input email
    email: Optional[EmailData] = Field(default=None, description="Current email")
    email_id: Optional[str] = Field(default=None, description="Current email ID")

    # Classification
    classification: Optional[ClassificationResult] = Field(
        default=None,
        description="Email classification result"
    )

    # RAG retrieval
    rag_context: List[RAGContext] = Field(
        default_factory=list,
        description="Retrieved context from RAG"
    )

    # Summarization
    summary: Optional[SummaryResult] = Field(
        default=None,
        description="Email summary and actions"
    )

    # Reply generation
    reply_draft: Optional[ReplyDraft] = Field(
        default=None,
        description="Generated reply draft"
    )

    # Calendar
    calendar_events: List[CalendarEventData] = Field(
        default_factory=list,
        description="Calendar events to create"
    )

    # Human review
    requires_human_review: bool = Field(
        default=False,
        description="Email needs human review"
    )
    human_review_reason: Optional[str] = Field(
        default=None,
        description="Reason for human review"
    )

    # Processing metadata
    processing_start_time: Optional[datetime] = Field(
        default=None,
        description="When processing started"
    )
    processing_end_time: Optional[datetime] = Field(
        default=None,
        description="When processing ended"
    )
    processing_duration_seconds: Optional[float] = Field(
        default=None,
        description="Total processing duration"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    error_type: Optional[str] = Field(default=None, description="Error category")

    # Analytics
    tokens_used: int = Field(default=0, description="Total tokens used")
    api_calls_count: int = Field(default=0, description="Number of API calls")

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


# ============ Human Review Item ============
class HumanReviewItem(BaseModel):
    """Item for human review."""

    email_id: str = Field(..., description="Email ID")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Sender email")
    reason: str = Field(..., description="Why review is needed")
    classification: Optional[ClassificationResult] = Field(
        default=None,
        description="Proposed classification"
    )
    reply_draft: Optional[ReplyDraft] = Field(
        default=None,
        description="Proposed reply"
    )
    calendar_events: List[CalendarEventData] = Field(
        default_factory=list,
        description="Proposed calendar events"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending", description="Review status")


# ============ Processing Result ============
class ProcessingResult(BaseModel):
    """Final result of email processing."""

    email_id: str = Field(..., description="Processed email ID")
    success: bool = Field(..., description="Processing successful")
    classification: Optional[ClassificationResult] = Field(default=None)
    summary: Optional[SummaryResult] = Field(default=None)
    reply_draft: Optional[ReplyDraft] = Field(default=None)
    calendar_events: List[CalendarEventData] = Field(default_factory=list)
    human_review_required: bool = Field(default=False)
    processing_time_seconds: float = Field(..., description="Total time in seconds")
    error_message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
