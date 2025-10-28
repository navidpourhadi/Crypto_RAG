# 🚀 Crypto_RAG — Cryptocurrency Market Analysis with RAG 💰

Crypto_RAG is a Retrieval-Augmented Generation (RAG) project that provides educational, news-driven cryptocurrency market analysis. It ingests scraped news 📰 (TradingView and other
sources), indexes the content into a vector database 🗃️, and uses an LLM 🤖 to generate
explainable market insights and trends based on retrieved news context.

This repository contains an API-backed Python agent 🐍 (`agent/`) and a Next.js
frontend ⚛️ (`crypto-rag-frontend/`). The agent implements a multi-stage workflow
for robust market reasoning: query analysis 🔍, strategic news collection (RAG) 📊,
news synthesis 🔄, market impact assessment 📈, and final insight generation ✨.

## ✨ Features

- 🔍 RAG-powered news search (semantic search over news chunks)
- 🧠 Multi-stage reasoning workflow (query processing → news collection → synthesis → analysis)
- ⚙️ Background news scraping and processing pipeline (scrape → chunk → embed → index)
- 💾 Conversation state persistence (MongoDB) and observability via Langfuse callbacks
- 🌐 REST API endpoints for health, RAG status, and manual RAG triggering

## 🚀 Quickstart — Prerequisites

- 🐳 Docker & Docker Compose (recommended)
- 🔑 Required cloud API keys
- 📝 Configuration file setup

## ⚙️ Configuration

1. 📋 Copy the example environment file and fill in your values:

```bash
cp agent/.env.example agent/.env
# Edit agent/.env and provide API keys, DB URLs, and other settings
```

🔑 Key environment settings (in `agent/.env`):

- `GOOGLE_API_KEY` — 🤖 API key for Google Gemini/GenAI (used by ChatGoogleGenerativeAI)
- `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_NAME` — 🗃️ Vector DB connection
- `MONGODB_URI` — 🍃 MongoDB connection string
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` — 📊 optional tracing/observability
- `RAG_RUN_ON_STARTUP` — 🚀 whether to run initial RAG processing on startup

📖 Refer to `agent/.env.example` for the full list of variables and recommended defaults.

## 🐳 Setup & Execution with Docker Compose

This repository includes a complete Docker Compose setup that builds both the agent and frontend services with all required dependencies.

### 🚀 Quick Start

From the repository root:

```bash
# Build and start all services
docker compose up --build
```

### 📊 What's Included

The Docker Compose setup automatically handles:

- 🐍 **Python Agent**: FastAPI backend with RAG capabilities
- ⚛️ **Next.js Frontend**: React-based user interface
- 🗃️ **Qdrant Vector Database**: For semantic search
- 🍃 **MongoDB**: For conversation persistence
- 🔗 **Networking**: All services connected and configured

### 📝 Monitoring

Check the service logs for startup progress:

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f agent
docker compose logs -f crypto-rag-frontend
```

### 🛠️ Development Mode

For development with live reload:

```bash
# Start services in detached mode
docker compose up -d

# Follow logs
docker compose logs -f agent
```

### 🔄 Managing Services

```bash
# Stop services
docker compose down

# Rebuild specific service
docker compose build agent
docker compose up agent

# Clean restart
docker compose down && docker compose up --build
```

## 🌐 API Endpoints

The FastAPI agent exposes several helpful endpoints (see `agent/app/main.py`):

- `GET /` — 📋 basic service info
- `GET /health` — ❤️ health check
- `GET /rag/status` — 📊 background RAG processing status
- `POST /rag/trigger` — 🔄 manually trigger RAG processing (scrape → embed → index)
- `POST /api/chat` — 💬 send messages to the agent and retrieve chat history

## 🔄 How it works (high level)

1. 📰 **News Ingestion**: Background pipeline scrapes news from configured sources and stores articles in MongoDB
2. 🔍 **RAG Processing**: The job chunks article text, generates embeddings, and stores vectors in Qdrant
3. 🤖 **Multi-stage Agent**: When a user sends a query, the agent performs:
   - 🎯 Routes intent → extracts crypto entities
   - 📊 Collects news via semantic search (`search_news_rag`)
   - 🔄 Synthesizes and analyzes the news
   - ✨ Returns a transparent, well-sourced response
4. 🛠️ **Fallback Handling**: If the vector DB returns no matches, the agent attempts query rewrites and produces helpful text-only fallback analysis

## 👨‍💻 Developer Notes

- 🧠 **Agent Code**: Lives in `agent/app/agent/` and composes nodes using LangGraph
- 🔧 **News Tools**: Implemented in `agent/app/agent/tools/news.py` using `EmbedService` and `VectorDatabaseService` for semantic search
- ⚙️ **Background Processing**: Scraping and RAG processing in `agent/app/services/` (see `scrape.py`, `chunk.py`, `embed.py`, and `rag.py`)

## 🗺️ Roadmap — Chart Analysis & Trend-Aware Predictions

In future versions we plan to add a tool that analyzes historical price charts 📈 (OHLCV data,
technical indicators, trend detection). The goal is to make the agent aware of current
price trends and patterns so it can combine technical chart analysis with news-derived
fundamental context to produce more informed, forward-looking educational commentary and
predictions. This will enable features such as:

- 📊 **Trend-aware insights** that combine technical indicators with news impact
- ⏰ **Time-series-aware retrieval** and embeddings for price movement contexts
- 📈 **Visualization endpoints** that return chart annotations alongside textual analysis


## 🔒 Note on Future Updates and Privacy

The project as published here covers the RAG-powered news ingestion, retrieval, and analysis
functionality described above. Any further implementations, feature additions, or enhancements
planned beyond this current step (for example, advanced proprietary chart-analysis tools 📊,
model tuning artifacts 🧠, or other private integrations 🔐) will remain part of the personal project
and will not necessarily be published in this public repository. If you have questions about
specific roadmap items or collaboration 🤝, please open an issue and we'll discuss potential
collaboration paths.


## 📄 License

This project is provided as-is for educational and research purposes.

---

🛡️ Use responsibly and remember this is educational content, not financial advice.