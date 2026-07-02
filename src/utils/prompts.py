"""
LLM prompts and templates for SmartMail AI.

Contains all prompts used for email classification, summarization,
reply generation, and calendar extraction. Versions tracked via comments.
"""

# ============ Classification Prompt (v1.0) ============
CLASSIFICATION_PROMPT = """You are an expert email analyst. Classify the following email and provide:
1. Email Type: general_email, meeting_request, urgent, follow_up, newsletter, or automated
2. Priority: low, normal, high, or urgent
3. Intent: informational, requires_response, requires_action, requires_decision, or scheduling
4. Confidence scores for each (0-1 scale)
5. Brief reasoning

Email Subject: {subject}
Email Body: {body}

Respond in JSON format:
{{
    "email_type": "...",
    "type_confidence": 0.0,
    "priority": "...",
    "priority_confidence": 0.0,
    "intent": "...",
    "intent_confidence": 0.0,
    "reasoning": "..."
}}

Be strict with confidence scores. Only use high confidence (>0.8) when you are very sure."""


# ============ Summarization Prompt (v1.0) ============
SUMMARIZATION_PROMPT = """You are an expert email summarizer. Read the email and provide:
1. A concise 2-3 sentence summary
2. 3-5 key points as bullet points
3. Sentiment (positive, neutral, negative)
4. Named entities (people, dates, locations)

Email Subject: {subject}
Email Body: {body}

Respond in JSON format:
{{
    "summary": "...",
    "key_points": ["point1", "point2", "point3"],
    "sentiment": "...",
    "entities": {{
        "people": ["name1", "name2"],
        "dates": ["date1", "date2"],
        "locations": ["location1"]
    }}
}}"""


# ============ Action Item Extraction Prompt (v1.0) ============
ACTION_EXTRACTION_PROMPT = """Extract all action items from the email. For each action:
1. Clear description of the action
2. Who is responsible (if mentioned)
3. Due date (if mentioned)
4. Priority (low, normal, high, urgent)

Email Subject: {subject}
Email Body: {body}

Respond in JSON format:
{{
    "action_items": [
        {{
            "action": "...",
            "assigned_to": "name or null",
            "due_date": "YYYY-MM-DD or null",
            "priority": "normal"
        }}
    ]
}}

Return an empty array [] if no action items found."""


# ============ Reply Generation Prompt (v1.0) ============
REPLY_GENERATION_PROMPT = """You are a professional email assistant. Generate a concise, 
professional reply to the following email. Consider:
- Tone should be professional and courteous
- Address the main points raised
- Be concise (3-4 paragraphs max)
- If action items were mentioned, acknowledge them

Original Email Subject: {subject}
Original Email From: {sender}
Original Email Body: {body}

{context_prompt}

Generated reply should start with greeting and end with appropriate sign-off.
Respond as plain text (not JSON), without subject line."""


# ============ Context-Aware Reply Prompt (v1.0) ============
CONTEXT_AWARE_REPLY_PROMPT = """Historical context from previous emails: {rag_context}

Use this context to make the reply more personalized and relevant to the conversation history."""


# ============ Calendar Event Extraction Prompt (v1.0) ============
CALENDAR_EXTRACTION_PROMPT = """Extract calendar event details from the email if any meeting is proposed.
Look for: meeting times, dates, attendees, location, and purpose.

Email Subject: {subject}
Email Body: {body}

Respond in JSON format:
{{
    "events": [
        {{
            "title": "Meeting title",
            "description": "Brief description",
            "start_time": "YYYY-MM-DDTHH:mm:ss",
            "end_time": "YYYY-MM-DDTHH:mm:ss",
            "attendees": ["email1@example.com", "email2@example.com"],
            "location": "location or null",
            "confidence": 0.9
        }}
    ]
}}

Return an empty array [] if no meeting is proposed.
Be conservative - only include events you're confident about (>0.8).
Timezone: {timezone}"""


# ============ Email Type Routing Prompt (v1.0) ============
EMAIL_ROUTING_PROMPT = """Based on the email classification, determine the processing path:

Email Type: {email_type}
Priority: {priority}
Intent: {intent}
Confidence: {confidence}

Respond in JSON:
{{
    "needs_rag": true/false,
    "needs_reply_generation": true/false,
    "needs_calendar_creation": true/false,
    "needs_human_review": true/false,
    "reason": "explanation"
}}"""


# ============ Confidence Assessment Prompt (v1.0) ============
CONFIDENCE_ASSESSMENT_PROMPT = """You are a quality checker. Assess the quality and confidence of:
1. The generated reply draft
2. Whether it's safe to send without human review

Generated Reply: {reply}

Original Email: {original_email}

Respond in JSON:
{{
    "reply_confidence": 0.0,
    "requires_human_review": true/false,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1"],
    "safe_to_send": true/false
}}

Be conservative. Suggest human review if confidence < 0.75."""


# ============ Prompt Helpers ============
def build_classification_prompt(subject: str, body: str) -> str:
    """Build classification prompt with email data."""
    return CLASSIFICATION_PROMPT.format(subject=subject, body=body)


def build_summarization_prompt(subject: str, body: str) -> str:
    """Build summarization prompt with email data."""
    return SUMMARIZATION_PROMPT.format(subject=subject, body=body)


def build_action_extraction_prompt(subject: str, body: str) -> str:
    """Build action extraction prompt with email data."""
    return ACTION_EXTRACTION_PROMPT.format(subject=subject, body=body)


def build_reply_prompt(
    subject: str,
    sender: str,
    body: str,
    rag_context: str = ""
) -> str:
    """Build reply generation prompt with optional context."""
    context_prompt = ""
    if rag_context:
        context_prompt = CONTEXT_AWARE_REPLY_PROMPT.format(rag_context=rag_context)
    
    return REPLY_GENERATION_PROMPT.format(
        subject=subject,
        sender=sender,
        body=body,
        context_prompt=context_prompt
    )


def build_calendar_extraction_prompt(
    subject: str,
    body: str,
    timezone: str = "UTC"
) -> str:
    """Build calendar extraction prompt with email data."""
    return CALENDAR_EXTRACTION_PROMPT.format(
        subject=subject,
        body=body,
        timezone=timezone
    )


def build_routing_prompt(
    email_type: str,
    priority: str,
    intent: str,
    confidence: float
) -> str:
    """Build routing decision prompt."""
    return EMAIL_ROUTING_PROMPT.format(
        email_type=email_type,
        priority=priority,
        intent=intent,
        confidence=confidence
    )


def build_confidence_assessment_prompt(
    reply: str,
    original_email: str
) -> str:
    """Build confidence assessment prompt."""
    return CONFIDENCE_ASSESSMENT_PROMPT.format(
        reply=reply,
        original_email=original_email
    )
