# SmartMail AI - Intelligent Email & Calendar Automation Agent

An AI-powered email and calendar automation system that automatically reads, summarizes, classifies, drafts replies, and manages scheduling from Gmail with minimal human intervention.

## 🎯 Project Goal

Build a production-ready system that:
- 📧 Automatically fetches and processes Gmail emails
- 🧠 Understands email context using RAG (Retrieval-Augmented Generation)
- 📝 Generates intelligent summaries and action items
- ✉️ Drafts contextual email replies
- 📅 Detects meetings and auto-schedules calendar events
- 👤 Maintains human-in-the-loop for safety and control

## ✨ Key Features

1. **Email Ingestion & Classification** - Smart categorization by type, priority, and intent
2. **Summarization + Action Extraction** - Extract key points and actionable items
3. **Contextual RAG** - Retrieve relevant past emails for context
4. **Intelligent Reply Drafting** - Generate context-aware responses
5. **Calendar Conflict Detection** - Smart scheduling with conflict avoidance
6. **Human-in-the-Loop Approval** - Safety layer for critical actions
7. **Analytics Dashboard** - Track processed emails and metrics

## 🏗️ Architecture

```
Trigger: New Emails
    ↓
Gmail API Fetch
    ↓
Preprocess & Clean
    ↓
Classification Node
    ├→ General Email → RAG Node → Summarization
    └→ Meeting Request → Calendar Agent
         ↓
    Reply Generation
         ↓
    Confidence Check
    ├→ High → Auto-save Draft
    └→ Low → Human Review Queue
         ↓
    Calendar Event Creation
         ↓
    Logging & Analytics
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Agent Framework | LangGraph + LangChain |
| LLM | Claude 3.5 Sonnet / GPT-4o / Grok |
| Vector DB | Chroma (local) / PGVector |
| APIs | Gmail API + Google Calendar API |
| Frontend | Streamlit |
| Storage | SQLite + Chroma |
| Deployment | Docker + Railway/Render |
| Observability | LangSmith |

## 📁 Project Structure

```
smartmail-ai/
├── src/
│   ├── nodes/              # LangGraph nodes
│   ├── tools/              # Gmail & Calendar API wrappers
│   ├── rag/                # Vector DB & retrieval
│   └── utils/              # Schemas, prompts, helpers
├── config/                 # Configuration management
├── data/
│   └── vector_db/          # Chroma vector database
├── logs/                   # Application logs
├── streamlit_app.py        # Dashboard
├── requirements.txt        # Dependencies
├── .env.example            # Environment variables template
└── Dockerfile              # Docker configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud Project with Gmail & Calendar APIs enabled
- API Keys for LLM (OpenAI, Anthropic, or Grok)

### Setup

1. **Clone & Enter Directory**
   ```bash
   cd SmartMail_AI
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Set Up Google APIs**
   - Download `credentials.json` from Google Cloud Console
   - Place in project root
   - Update `GMAIL_CREDENTIALS_PATH` in `.env`

6. **Run Application**
   ```bash
   # Start LangGraph agent
   python -m src.main
   
   # Or start dashboard
   streamlit run streamlit_app.py
   ```

## 📋 Development Phases

- [x] **Phase 1** - Foundation (Config, Schemas, Prompts, Helpers)
- [ ] **Phase 2** - External Integrations (Gmail Tools, Calendar Tools)
- [ ] **Phase 3** - RAG System (Indexer, Retriever)
- [ ] **Phase 4** - LangGraph Nodes (7 nodes)
- [ ] **Phase 5** - Orchestration (Graph, Main entry)
- [ ] **Phase 6** - Dashboard & Deployment (Streamlit, Docker)

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src

# Specific test file
pytest tests/test_classifier.py -v
```

## 📊 Configuration

All settings are managed through environment variables. See [`.env.example`](.env.example) for all available options:

- **LLM Settings** - Provider, model, temperature, timeouts
- **RAG Config** - Chunk size, overlap, retrieval parameters
- **Thresholds** - Confidence scores for auto-processing
- **API Rate Limiting** - Request limits per minute
- **Feature Flags** - Enable/disable components

## 🔐 Security

- ✅ All secrets loaded from `.env` (never hardcoded)
- ✅ OAuth2 for Gmail & Calendar APIs
- ✅ Human-in-the-loop approval layer
- ✅ No full email content in logs (production mode)
- ✅ Confidence thresholds before auto-actions
- ✅ Comprehensive error handling

## 📝 Logging

Logs are written to `./logs/smartmail.log` with:
- **JSON format** for easy parsing
- **Log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rotation** - Automatic file rotation at 10MB
- **No sensitive data** - Sanitized email content

## 🤝 Contributing

Follow these standards:
- **Commits** - Use Conventional Commits (feat:, fix:, docs:, refactor:)
- **Code Style** - Black formatting, Ruff linting, PEP 8
- **Type Hints** - Required on all functions
- **Docstrings** - Required on all classes and major functions
- **Branch Names** - feature/*, bugfix/*, hotfix/*

## 📈 Performance

- **Async Processing** - Concurrent email processing
- **Caching** - Results cached for identical queries
- **Batch Operations** - Bulk Gmail/Calendar API calls
- **Token Optimization** - Efficient LLM token usage

## 📊 Observability

- **LangSmith Integration** - Full tracing of LangGraph execution
- **Token Tracking** - Monitor LLM API costs
- **Analytics Dashboard** - Email processing metrics
- **Error Tracking** - Comprehensive error categorization

## 📚 Documentation

- See [`best_practices.md`](best_practices.md) for coding standards
- See [`.env.example`](.env.example) for configuration options
- Architecture diagrams in this README

## 🐛 Known Limitations

- Currently supports Gmail only (Exchange coming soon)
- Calendar support limited to Google Calendar
- Requires active API credentials

## 📄 License

Private Project - All Rights Reserved

## 👤 Author

**SmartMail AI Development Team**

---

**Last Updated:** 2026-07-03  
**Current Phase:** 1 (Foundation) ✅  
**Next Phase:** 2 (External Integrations)
