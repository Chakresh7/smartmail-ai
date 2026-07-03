"""Human review node

Provides a simple in-memory creation of human review items. In a
real system this would enqueue items to a review service or DB.
"""

from src.utils.schemas import HumanReviewItem, GraphState
from src.utils.helpers import setup_logging
from datetime import datetime
from config.config import settings

logger = setup_logging(log_level=settings.log_level)


def create_human_review_item(state: GraphState, reason: str) -> HumanReviewItem:
	item = HumanReviewItem(
		email_id=state.email.email_id if state.email else state.email_id or "",
		subject=state.email.subject if state.email else "",
		sender=state.email.sender if state.email else "",
		reason=reason,
		classification=state.classification,
		reply_draft=state.reply_draft,
		calendar_events=state.calendar_events,
		created_at=datetime.utcnow(),
		status="pending",
	)
	# TODO: persist to DB or message queue. For now just log.
	logger.info(f"Enqueued human review for {item.email_id}: {reason}")
	return item

