import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.rag.indexer import RAGIndexer
from src.rag.retriever import RAGRetriever, RAGError
from src.utils.schemas import EmailData


@pytest.fixture(autouse=True)
def patch_chroma_and_openai(monkeypatch):
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_collection.side_effect = [mock_collection]
    mock_client.create_collection.return_value = mock_collection
    monkeypatch.setattr('src.rag.indexer.chromadb.Client', lambda Settings: mock_client)
    monkeypatch.setattr('src.rag.retriever.chromadb.Client', lambda Settings: mock_client)
    monkeypatch.setattr('src.rag.indexer.OpenAI', lambda api_key, base_url: MagicMock(
        embeddings=MagicMock(create=lambda model, input: MagicMock(data=[MagicMock(embedding=[0.1]*1536) for _ in input]))
    ))
    yield


def test_chunk_email_splits_text():
    indexer = RAGIndexer()
    email = EmailData(
        email_id='email_1',
        thread_id='thread_1',
        subject='Test',
        sender='sender@example.com',
        sender_name='Sender',
        to=['recipient@example.com'],
        cc=[],
        bcc=[],
        body='This is a test email body for chunking purposes.',
        html_body=None,
        received_at=datetime.utcnow(),
        is_reply=False,
        labels=[],
        attachments=[],
    )

    chunks = indexer.chunk_email(email)
    assert len(chunks) >= 1
    assert chunks[0].metadata['email_id'] == 'email_1'


def test_index_email_adds_documents():
    indexer = RAGIndexer()
    indexer.collection.add.return_value = None
    email = EmailData(
        email_id='email_1',
        thread_id='thread_1',
        subject='Test',
        sender='sender@example.com',
        sender_name='Sender',
        to=['recipient@example.com'],
        cc=[],
        bcc=[],
        body='This is a test email body for chunking purposes.',
        html_body=None,
        received_at=datetime.utcnow(),
        is_reply=False,
        labels=[],
        attachments=[],
    )

    indexer.index_email(email)
    assert indexer.collection.add.called


def test_retriever_returns_context(monkeypatch):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        'documents': [['chunk1', 'chunk2']],
        'metadatas': [[{'email_id': 'email_1'}, {'email_id': 'email_2'}]],
        'distances': [[0.1, 0.2]],
    }
    monkeypatch.setattr('src.rag.retriever.chromadb.Client', lambda Settings: MagicMock(get_collection=lambda name: mock_collection))

    retriever = RAGRetriever()
    result = retriever.retrieve('test query')
    assert len(result) == 2
    assert result[0]['source'] == 'email:email_1'


def test_retriever_raises_when_collection_missing(monkeypatch):
    monkeypatch.setattr('src.rag.retriever.chromadb.Client', lambda Settings: MagicMock(get_collection=lambda name: (_ for _ in ()).throw(Exception('missing'))))
    with pytest.raises(RAGError):
        RAGRetriever()
