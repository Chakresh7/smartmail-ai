"""RAG retriever node

Responsible for querying the RAG vector store for contextual chunks
relevant to a given email.
"""

from typing import List

from src.rag.retriever import RAGRetriever
from src.utils.schemas import EmailData, RAGContext
from src.utils.helpers import setup_logging
from config.config import settings

logger = setup_logging(log_level=settings.log_level)


def retrieve_context(email: EmailData, k: int | None = None) -> List[RAGContext]:
	"""Retrieve RAG contexts for a given email.

	Args:
		email: `EmailData` to build the query from
		k: optional number of results to retrieve

	Returns:
		List of `RAGContext` models
	"""
	try:
		retriever = RAGRetriever()
		query = f"Subject: {email.subject}\nBody: {email.body}"
		raw_ctxs = retriever.retrieve(query, k=k)
		contexts: List[RAGContext] = []
		for item in raw_ctxs:
			md = item.get("metadata", {})
			contexts.append(
				RAGContext(
					source_email_id=md.get("email_id", ""),
					subject=md.get("subject", ""),
					snippet=item.get("text", ""),
					relevance_score=1.0 - float(item.get("distance", 0.0)),
					sender=md.get("sender", ""),
					received_at=md.get("received_at", ""),
					metadata=md,
				)
			)
		return contexts
	except Exception as exc:
		logger.warning(f"RAG retrieval failed: {exc}")
		return []

