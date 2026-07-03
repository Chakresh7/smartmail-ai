"""
Vector retriever for SmartMail AI RAG system.

Responsible for querying the Chroma store and returning relevant context
chunks with metadata and source citations.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.config import settings
from src.utils.helpers import SmartMailException


class RAGError(SmartMailException):
    """Raised when retrieval fails."""
    pass


class RAGRetriever:
    """Retrieves relevant context from the RAG store."""

    def __init__(self, collection_name: str = "email_context"):
        self.client = chromadb.Client(
            Settings=ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.vector_db_path,
            )
        )
        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception as exc:
            raise RAGError(f"Unable to open RAG collection: {exc}") from exc

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve context chunks for a query."""
        retrieval_k = k or settings.retrieval_k
        try:
            result = self.collection.query(
                query_texts=[query],
                n_results=retrieval_k,
                include=["documents", "metadatas", "distances"],
            )

            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            contexts: List[Dict[str, Any]] = []
            for idx, doc in enumerate(documents):
                contexts.append(
                    {
                        "text": doc,
                        "metadata": metadatas[idx],
                        "distance": distances[idx],
                        "source": f"email:{metadatas[idx].get('email_id')}",
                    }
                )

            return contexts
        except Exception as exc:
            raise RAGError(f"Error retrieving RAG context: {exc}") from exc

