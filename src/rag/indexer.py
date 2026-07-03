"""
Vector indexer for SmartMail AI RAG system.

Handles email chunking, batch embedding via OpenAI-compatible API, and
persistence into a Chroma vector store.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from config.config import settings
from src.utils.schemas import EmailData
from src.utils.helpers import retry_with_backoff


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]


class RAGIndexer:
    """Builds and updates the RAG vector store."""

    def __init__(self, collection_name: str = "email_context"):
        self.client = chromadb.Client(
            settings=ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.vector_db_path,
            )
        )
        self.collection = self._get_or_create_collection(collection_name)
        self.embedding_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base_url,
        )

    def _get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(name)

    def chunk_email(self, email: EmailData) -> List[Chunk]:
        """Split email text into overlapping chunks for indexing."""
        text = email.body or ""
        if not text:
            return []

        words = text.split()
        chunks: List[Chunk] = []
        start = 0
        while start < len(words):
            end = min(start + settings.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(
                Chunk(
                    text=chunk_text,
                    metadata={
                        "email_id": email.email_id,
                        "thread_id": email.thread_id,
                        "subject": email.subject,
                        "sender": email.sender,
                        "received_at": str(email.received_at),
                    },
                )
            )
            start += settings.chunk_size - settings.chunk_overlap
            if end == len(words):
                break

        return chunks

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts in batches."""
        embeddings: List[List[float]] = []
        for i in range(0, len(texts), settings.embedding_batch_size):
            batch = texts[i : i + settings.embedding_batch_size]
            response = self.embedding_client.embeddings.create(
                model=settings.embedding_model,
                input=batch,
            )
            embeddings.extend([item.embedding for item in response.data])

        return embeddings

    @retry_with_backoff(max_retries=3)
    def index_email(self, email: EmailData) -> None:
        """Index a single email into the vector store."""
        chunks = self.chunk_email(email)
        if not chunks:
            return

        ids = [f"{email.email_id}_{idx}" for idx in range(len(chunks))]
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = self._get_embeddings(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        self.client.persist()

    @retry_with_backoff(max_retries=3)
    def index_batch(self, emails: List[EmailData]) -> None:
        """Index a batch of emails into the vector store."""
        for email in emails:
            self.index_email(email)

