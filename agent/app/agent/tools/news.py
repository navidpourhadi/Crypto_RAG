"""
RAG (Retrieval-Augmented Generation) Tool for searching relevant news.

This tool handles the complete RAG pipeline:
1. Processing and indexing RAG files (reference documents)
2. Querying against CHAT files using RAG knowledge base
3. Performing cybersecurity analysis with context from indexed documents
"""

from typing import Dict, List

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.services.embed import EmbedService
from app.services.vectordb import VectorDatabaseService
from app.utils.logger import get_logger

logger = get_logger(__name__)


@tool
async def search_news_rag(
    config: RunnableConfig,
    query_text: str,
    max_results: int = 10,
    similarity_threshold: float = 0.6,
) -> List[Dict]:
    """
    Search cryptocurrency news using semantic similarity for informed analysis and responses.

    This tool performs vector-based semantic search against a cryptocurrency news knowledge base.
    It converts user queries into embeddings and finds the most relevant news articles and content
    to provide factual, up-to-date information for cryptocurrency-related questions and analysis.

    **CRITICAL: When to use this tool for agent reasoning:**
    - User asks about recent crypto news, events, or developments
    - User requests information about specific cryptocurrency projects or tokens
    - User wants market analysis, trends, or price-related insights
    - Questions about crypto regulations, policy changes, or legal developments
    - Requests for information about crypto exchanges, DeFi protocols, or blockchain updates
    - When you need factual context to answer crypto-related questions accurately
    - User asks about crypto market sentiment or community reactions
    - Questions about crypto adoption, partnerships, or institutional involvement

    **DO NOT use this tool when:**
    - User asks general questions unrelated to cryptocurrency
    - Questions about basic crypto concepts that don't require recent news context
    - Simple mathematical calculations or conversions
    - Personal advice requests (investment advice, etc.)

    **Agent reasoning strategy:**
    1. First, determine if the user's question relates to cryptocurrency news or market information
    2. Formulate specific search queries using crypto terminology and concepts
    3. Search for relevant news articles to gather factual context
    4. Synthesize the retrieved information to provide accurate, well-informed responses
    5. Always cite or reference the news sources when providing information

    **Effective search query formulation:**
    - Include specific cryptocurrency names (Bitcoin, Ethereum, etc.)
    - Use market-related terms (price, bull market, bear market, adoption)
    - Include relevant time frames (today, this week, recent, latest)
    - Reference specific events or developments you're investigating
    - Use technical terms relevant to blockchain and crypto ecosystems

    **Example queries for agent reasoning:**
    - "Bitcoin price movements and market analysis"
    - "Ethereum network upgrades and developments"
    - "cryptocurrency regulation changes and policy updates"
    - "DeFi protocol hacks and security incidents"
    - "institutional adoption of Bitcoin and crypto assets"
    - "crypto exchange listings and trading updates"
    - "blockchain partnerships and enterprise adoption"
    - "altcoin performance and market trends"

    Args:
        query_text (str): Natural language query describing the crypto-related information needed.
                        Use specific cryptocurrency terms, project names, and market concepts.
                        Frame queries to capture relevant news and market context.
        max_results (int, optional): Maximum number of relevant news chunks to return.
                                Default is 10. Use higher values (15-20) for comprehensive analysis.
        similarity_threshold (float, optional): Minimum similarity score (0.0-1.0).
                                            Default 0.7. Lower to 0.6 for broader context,
                                            raise to 0.8 for highly relevant results only.

    Returns:
        List[Dict]: List of relevant cryptocurrency news chunks, each containing:
            - news_id: Unique identifier of the news
            - chunk_index: Index position within the source document
            - title: Title of the news article
            - source: Name of the news source
            - publish_date: Publication date of the news
            - chunk_text: The actual news content text
            - score: Similarity score indicating relevance (higher = more relevant)

        Returns error dict if search fails: {"error": "Error description"}

    Raises:
        Exception: If embedding service fails, vector database is unavailable,
                or authentication issues occur during search.

    Note:
        - Results ranked by semantic similarity to capture context and meaning
        - Requires cryptocurrency news to be previously processed and indexed
        - Best results when queries include specific crypto terminology and concepts
        - Use retrieved information to provide factual, well-sourced responses
    """
    try:
        # Embed the query text
        query_embedding = await EmbedService.embed_query_jina(contents=[query_text])

        # First attempt: use provided query and threshold
        results = await VectorDatabaseService.search_vectors(
            query_vector=query_embedding[0],
            limit=max_results,
            score_threshold=similarity_threshold,
        )

        # If no results, try simple query rewriting and broader search
        if not results:
            logger.debug("No results for initial query, attempting fallback query rewrites")

            # Build a couple of expanded fallback queries to broaden the semantic match
            expanded_queries = []
            core = (query_text or "").strip()
            if core:
                expanded_queries.append(f"{core} recent cryptocurrency news, price, market, sentiment, latest developments")
                expanded_queries.append(f"recent news and analysis about {core} and market impact")
            else:
                expanded_queries.append("recent cryptocurrency news and market developments")

            # Try each expanded query with a lower similarity threshold and larger window
            for fq in expanded_queries:
                try:
                    fq_embedding = await EmbedService.embed_query_jina(contents=[fq])
                    fallback_results = await VectorDatabaseService.search_vectors(
                        query_vector=fq_embedding[0],
                        limit=max_results * 2,
                        score_threshold=max(0.5, similarity_threshold - 0.1),
                    )
                    if fallback_results:
                        logger.debug("Fallback query produced results")
                        return fallback_results
                except Exception:
                    # continue to next fallback query
                    continue

        # If still no results, return descriptive no-result payload so the LLM can react
        if not results:
            logger.info("No news results found for query; returning no-results hint")
            return [
                {
                    "no_results": True,
                    "message": "No relevant news chunks were found in the vector DB for the provided query.",
                    "original_query": query_text,
                    "suggested_queries": expanded_queries if 'expanded_queries' in locals() else [],
                }
            ]

        return results

    except Exception as e:
        logger.error(f"Error in search_news_rag tool: {str(e)}")
        return [{"error": f"Search failed: {str(e)}"}]

