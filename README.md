# Crypto_RAG — Cryptocurrency Market Analysis with RAG

Crypto_RAG is a Retrieval-Augmented Generation (RAG) project that provides educational,
news-driven cryptocurrency market analysis. It ingests scraped news (TradingView and other
sources), indexes the content into a vector database, and uses an LLM to generate
explainable market insights and trends based on retrieved news context.

This repository contains an API-backed Python agent (`agent/`) and a Next.js
frontend (`crypto-rag-frontend/`). The agent implements a multi-stage workflow
for robust market reasoning: query analysis, strategic news collection (RAG),
news synthesis, market impact assessment, and final insight generation.

## Features

- RAG-powered news search (semantic search over news chunks)
- Multi-stage reasoning workflow (query processing → news collection → synthesis → analysis)
- Background news scraping and processing pipeline (scrape → chunk → embed → index)
- Conversation state persistence (MongoDB) and observability via Langfuse callbacks
- REST API endpoints for health, RAG status, and manual RAG triggering

## Quickstart — Prerequisites

- Docker & Docker Compose (recommended) OR Python 3.11+/3.12 and a virtualenv
- Qdrant (or your configured vector DB), MongoDB, and required cloud API keys

## Configuration

1. Copy the example environment file and fill in your values:

```bash
cp agent/.env.example agent/.env
# Edit agent/.env and provide API keys, DB URLs, and other settings
```

Key environment settings (in `agent/.env`):

- GOOGLE_API_KEY — API key for Google Gemini/GenAI (used by ChatGoogleGenerativeAI)
- QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME — Vector DB connection
- MONGODB_URI — MongoDB connection string
- LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY — optional tracing/observability
- RAG_RUN_ON_STARTUP — whether to run initial RAG processing on startup

Refer to `agent/.env.example` for the full list of variables and recommended defaults.

## Run with Docker Compose (recommended)

This repository includes a Docker Compose setup that builds the agent and frontend.

From the repository root:

```bash
docker compose up --build
```

This will build and start the services defined in `docker-compose.yml`. Check the
`agent` service logs for startup progress and RAG background job activity.

## Run locally (development)

If you prefer to run the Python agent locally without Docker:

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# copy and configure agent/.env as shown above
uvicorn app.main:app --reload
```

The FastAPI agent exposes several helpful endpoints (see `agent/app/main.py`):

- `GET /` — basic service info
- `GET /health` — health check
- `GET /rag/status` — background RAG processing status
- `POST /rag/trigger` — manually trigger RAG processing (scrape → embed → index)
- Chat APIs under `/api/chat` for sending messages to the agent and retrieving history

## How it works (high level)

1. Background pipeline scrapes news from configured sources and stores articles in MongoDB.
2. The RAG processing job chunks article text, generates embeddings, and stores vectors in Qdrant.
3. When a user sends a query, the multi-stage agent: routes intent → extracts crypto entities →
   collects news via semantic search (`search_news_rag`) → synthesizes and analyzes the news →
   returns a transparent, well-sourced response.
4. If the vector DB returns no matches for a query, the agent will attempt query rewrites and
   (if still empty) produce a helpful text-only fallback analysis explaining the situation and
   suggesting next steps.

## Developer notes

- The agent code lives in `agent/app/agent/` and composes nodes using LangGraph.
- News tools are implemented in `agent/app/agent/tools/news.py` and use `EmbedService` and
  `VectorDatabaseService` to perform semantic search.
- Background scraping and RAG processing are in `agent/app/services/` (see `scrape.py`,
  `chunk.py`, `embed.py`, and `rag.py`).

## Roadmap — chart analysis / trend-aware predictions

In future versions we plan to add a tool that analyzes historical price charts (OHLCV data,
technical indicators, trend detection). The goal is to make the agent aware of current
price trends and patterns so it can combine technical chart analysis with news-derived
fundamental context to produce more informed, forward-looking educational commentary and
predictions. This will enable features such as:

- Trend-aware insights that combine technical indicators with news impact
- Time-series-aware retrieval and embeddings for price movement contexts
- Visualization endpoints that return chart annotations alongside textual analysis

## Contributing

- Please open issues for bugs and feature requests.
- PRs should include tests where applicable and update the README when behavior changes.

## License

This project is provided as-is for educational and research purposes. Include license info as needed.

---

Happy hacking — use responsibly and remember this is educational content, not financial advice.

## Note on future updates and privacy

The project as published here covers the RAG-powered news ingestion, retrieval, and analysis
functionality described above. Any further implementations, feature additions, or enhancements
planned beyond this current step (for example, advanced proprietary chart-analysis tools,
model tuning artifacts, or other private integrations) will remain part of the personal project
and will not necessarily be published in this public repository. If you have questions about
specific roadmap items or collaboration, please open an issue and we'll discuss potential
collaboration paths.
