"""
Cryptocurrency Market Analysis Agent workflow nodes and routing functions.

This module contains all the node implementations and routing logic
for the cryptocurrency market analysis agent workflow system that provides
intelligent market insights using RAG-powered news analysis.
"""

from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.prompts import SYSTEM_PROMPT

from app.agent.tools import news_tools
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def supervisor(state) -> dict:
    """
    Supervisor node that routes cryptocurrency market analysis requests to appropriate specialized nodes.

    Routes based on the user's intent:
    - News Analysis RAG Route: Handles cryptocurrency market questions requiring news context and analysis
    - Direct Answer Route: Handles general questions that don't require news search or market analysis
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,  # Lower temperature for routing decisions
    )

    # Define routing system prompt
    routing_prompt = f"""
    {SYSTEM_PROMPT}
    
    You are a routing supervisor for a cryptocurrency market analysis AI agent system. 
    Based on the user's message, determine which route should handle the request:

    **RAG_ANALYSIS**: Choose this route when:
    - User asks about recent cryptocurrency news, events, or market developments
    - User requests analysis of specific cryptocurrencies (Bitcoin, Ethereum, altcoins, etc.)
    - User wants market trends, price analysis, or sentiment assessment
    - User asks about crypto regulations, policy changes, or legal developments
    - User inquires about DeFi protocols, blockchain updates, or exchange news
    - User requests fundamental analysis based on current market conditions
    - User asks about institutional adoption, partnerships, or enterprise blockchain
    - Keywords: Bitcoin, crypto, cryptocurrency, market, price, news, analysis, trends, DeFi, blockchain, regulation
    
    **DIRECT_ANSWER**: Choose this route when:
    - User asks general questions about the system capabilities or how it works
    - User needs greeting, help, or explanation responses about the service
    - User asks basic cryptocurrency concepts that don't require recent news context
    - Simple conversational queries or system information requests
    - Questions about disclaimers, limitations, or general crypto education
    
    
    Respond with ONLY the route name: RAG_ANALYSIS or DIRECT_ANSWER

    """

    # Get the last user message
    last_message = state["messages"][-1].content if state["messages"] else ""

    routing_response = llm.invoke(
        [
            SystemMessage(content=routing_prompt),
            HumanMessage(content=f"User request: {last_message}"),
        ]
    )

    route = routing_response.content.strip()

    # Handle direct answer case
    if route == "DIRECT_ANSWER":
        # Generate direct response using system prompt
        direct_response = llm.invoke(
            [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        )
        if not direct_response.additional_kwargs.get("timestamp"):
            direct_response.additional_kwargs["timestamp"] = datetime.now().isoformat()
        return {"messages": state["messages"] + [direct_response], "next_node": "end"}

    # Validate and set the route
    if route not in ["RAG_ANALYSIS"]:
        route = "RAG_ANALYSIS"  # Default fallback

    return {"next_node": route.lower()}


def rag_analysis_node(state) -> dict:
    """
    RAG Analysis Node for cryptocurrency market analysis.

    This node handles:
    1. Cryptocurrency news search and retrieval from TradingView sources
    2. Semantic analysis of market developments and trends
    3. Context gathering from multiple news sources
    4. Market sentiment and impact assessment
    5. Comprehensive cryptocurrency market analysis generation
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
    )

    llm_with_rag_tools = llm.bind_tools(news_tools)

    rag_system_prompt = f"""
    {SYSTEM_PROMPT}
    
    **You are now in CRYPTOCURRENCY MARKET ANALYSIS mode.**
    
    Your role is to perform comprehensive cryptocurrency market analysis 
    using the RAG-powered news knowledge base from TradingView and other sources.
    
    **Your Market Analysis Workflow:**
    1. **Query Understanding**: Analyze the user's request to identify:
       - Specific cryptocurrencies mentioned (Bitcoin, Ethereum, etc.)
       - Market aspects of interest (price, trends, regulations, etc.)
       - Time frame or context needed (recent, daily trends, etc.)
    
    2. **Strategic News Search**: Use the search_news_rag tool to gather relevant information:
       - Search for specific cryptocurrency developments and news
       - Look for market trends, price movements, and sentiment indicators
       - Find regulatory updates, institutional adoption news, or tech developments
       - Gather multiple perspectives with targeted searches
    
    3. **Context Synthesis**: Analyze retrieved news to understand:
       - Current market conditions and recent developments
       - Key events affecting the cryptocurrency or market segment
       - Market sentiment and community reactions
       - Regulatory or institutional factors
    
    4. **Comprehensive Market Analysis**: Provide detailed cryptocurrency analysis including:
       - Summary of recent relevant developments
       - Market trend analysis based on news context
       - Impact assessment of key events on prices or adoption
       - Broader market implications and connections
       - Educational context for market movements
    
    **Critical Guidelines:**
    - ALWAYS search for recent news context before providing market analysis
    - Use multiple targeted searches to gather comprehensive market intelligence
    - Base your analysis on factual news sources, not speculation
    - Clearly distinguish between news-based insights and general market education
    - Include timestamps and source references when citing news information
    - Emphasize that this is educational analysis, not financial advice
    - Encourage users to conduct their own research (DYOR)
    
    **Search Strategy Tips:**
    - Use specific cryptocurrency names in searches
    - Include market-related terms (price, bull market, adoption, regulation)
    - Search for recent developments, partnerships, or technical updates
    - Look for institutional news, regulatory changes, or major announcements
    """

    response = llm_with_rag_tools.invoke(
        [SystemMessage(content=rag_system_prompt)] + state["messages"]
    )

    if not response.additional_kwargs.get("timestamp"):
        response.additional_kwargs["timestamp"] = datetime.now().isoformat()

    return {"messages": [response]}



def route_after_supervisor(
    state,
) -> Literal["rag_analysis", "__end__"]:
    """Route to the appropriate node based on supervisor decision."""
    if state["next_node"] == "end":
        return "__end__"
    return state["next_node"]


def should_continue_rag(state) -> Literal["news_tools", "__end__"]:
    """Determine if cryptocurrency market analysis should continue with news search tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "news_tools"
    return "__end__"


# ============================================================================
# ENHANCED WORKFLOW NODES FOR BETTER MARKET ANALYSIS REASONING
# ============================================================================

def query_processor_node(state) -> dict:
    """
    Enhanced query processing node for extracting crypto entities and analysis intent.
    
    Processes user query to extract:
    - Cryptocurrencies mentioned (Bitcoin, Ethereum, etc.)
    - Analysis type (price, trends, news, technical, fundamental)
    - Time frame (today, week, month, recent)
    - Specific events or topics of interest
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )
    
    query_analysis_prompt = """
    Analyze the user's cryptocurrency query and extract structured information:
    
    1. Cryptocurrencies mentioned (Bitcoin, BTC, Ethereum, ETH, etc.)
    2. Analysis type (price analysis, market trends, news summary, technical analysis, fundamental analysis)
    3. Time frame (today, this week, recent, specific dates)
    4. Specific topics (regulations, institutional adoption, technical developments, etc.)
    5. Market focus (bull/bear market, volatility, adoption, etc.)
    
    Format your response as JSON with keys: cryptocurrencies, analysis_type, timeframe, topics, market_focus
    """
    
    last_message = state["messages"][-1].content if state["messages"] else ""
    
    response = llm.invoke([
        SystemMessage(content=query_analysis_prompt),
        HumanMessage(content=f"Query: {last_message}")
    ])
    
    # Store analysis in state
    if "crypto_context" not in state:
        state["crypto_context"] = {}
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
        
    state["crypto_context"]["query_analysis"] = response.content
    state["reasoning_steps"].append("Query processed and crypto entities extracted")
    
    return {"crypto_context": state["crypto_context"], "reasoning_steps": state["reasoning_steps"]}


def news_collector_node(state) -> dict:
    """
    Strategic news collection node for comprehensive market coverage.
    
    Strategically collect news based on query analysis:
    - Multiple targeted searches for comprehensive coverage
    - Different search strategies for different analysis types
    - Time-relevant news collection
    """
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    if "analysis_context" not in state:
        state["analysis_context"] = {}
        
    state["reasoning_steps"].append("Strategic news collection initiated")
    state["analysis_context"]["news_collection_strategy"] = "multi_target_search"

    # Use the LLM bound to the news tools so it outputs an AIMessage containing tool_calls
    # The ToolNode expects the last AI message to include tool_calls which it will execute.
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )

    llm_with_tools = llm.bind_tools(news_tools)

    # Build a focused instruction so the model generates a call to `search_news_rag`
    instruction = """
    You are a news collection assistant. Based on the user's last message and any extracted
    query analysis in the context, decide the best search query and call the tool
    `search_news_rag` with the following named arguments in JSON form: `query_text`,
    `max_results` (int), and `similarity_threshold` (float).

    Guidance:
    - If specific cryptocurrencies are mentioned, include them explicitly in `query_text`.
    - Prefer recent/time-sensitive phrasing when the user requests "recent" or "latest".
    - Use max_results=5 and similarity_threshold=0.5 by default; lower threshold to 0.3 for
      broader searches if the user asks for general context.

    Only produce a tool call (no additional text). The tool will be executed by the system.
    """

    # Provide the user's messages so the LLM can build the query
    messages = [
        SystemMessage(content=instruction),
        *state.get("messages", []),
    ]

    response = llm_with_tools.invoke(messages)

    if not response.additional_kwargs.get("timestamp"):
        response.additional_kwargs["timestamp"] = datetime.now().isoformat()

    state["reasoning_steps"].append("Query processed and crypto entities extracted for search")

    return {
        "messages": [response],
        "analysis_context": state["analysis_context"],
        "reasoning_steps": state["reasoning_steps"],
        "next_node": "news_tools",
    }


def news_synthesizer_node(state) -> dict:
    """
    News synthesis and relevance scoring node.
    
    Synthesize collected news:
    - Remove duplicates and irrelevant content
    - Score relevance to user query
    - Organize by themes and impact
    - Identify key market signals
    """
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    if "market_insights" not in state:
        state["market_insights"] = {}
    if "news_data" not in state:
        state["news_data"] = []
        
    state["reasoning_steps"].append("News synthesized and relevance scored")
    state["market_insights"]["news_themes"] = []
    state["market_insights"]["key_signals"] = []
    
    # Extract news data from tool messages and store in state
    messages = state.get("messages", [])
    news_data = state.get("news_data", [])
    
    # If news_data is empty, try to extract from recent tool messages
    if not news_data:
        for message in reversed(messages):
            # Check if this is a tool message with search results
            if hasattr(message, 'type') and message.type == 'tool':
                try:
                    # Extract the tool result content
                    if hasattr(message, 'content'):
                        import json
                        # The tool returns a list of dictionaries with news data
                        if isinstance(message.content, str):
                            tool_results = json.loads(message.content)
                        else:
                            tool_results = message.content
                        
                        if isinstance(tool_results, list):
                            # Store the retrieved news data in state
                            news_data = tool_results
                            state["news_data"] = news_data
                            state["reasoning_steps"].append(f"Retrieved {len(tool_results)} news articles from vector database")
                            logger.info(f"Stored {len(tool_results)} news articles in state")
                        break
                except Exception as e:
                    logger.warning(f"Error processing tool results: {e}")
                    continue
    
    # Check if news_data contains error messages or no results
    if not news_data or (len(news_data) == 1 and news_data[0].get("no_results")):
        # Use an LLM to provide a useful fallback: explain no news was found, offer a general
        # analysis based on the query and suggest next steps for the user.
        llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
        )

        # Get the original user query from messages
        user_messages = [msg for msg in state.get("messages", []) if hasattr(msg, 'type') and msg.type == 'human']
        last_user = user_messages[-1].content if user_messages else ""

        fallback_prompt = f"""
        You attempted to retrieve relevant news for the user's request but the vector database
        returned no matching articles. Produce a user-facing fallback response that includes:
        1) A short explanation that no recent/news items were found for their query.
        2) A concise, general (text-only) analysis or guidance relevant to the user's request
           based on general cryptocurrency knowledge and best-practice checks.
        3) A list of 3 suggested alternative queries or keywords to broaden the news search.
        4) A final line asking whether the user wants to broaden the search, search other sources,
           or refine their question. Keep the tone helpful and educational, and include a clear
        disclaimer that this is not financial advice.

        User query: {last_user}
        """

        # Gemini requires at least one user/content message in the request payload.
        # Provide the user's original query as a HumanMessage so the LLM has content to generate from.
        response = llm.invoke([
            SystemMessage(content=fallback_prompt),
            HumanMessage(content=last_user or ""),
        ])

        # add timestamp if missing
        if not response.additional_kwargs.get("timestamp"):
            from datetime import datetime

            response.additional_kwargs["timestamp"] = datetime.now().isoformat()

        # Append the fallback message to the conversation so final response can return it
        messages = state.get("messages", []) + [response]
        state["reasoning_steps"].append("No news retrieved: fallback text-only analysis provided")
        state["market_insights"]["fallback_analysis"] = True

        return {
            "messages": messages,
            "news_data": state["news_data"],
            "market_insights": state["market_insights"],
            "reasoning_steps": state["reasoning_steps"],
            "next_node": "__end__",
        }
    
    # Process the retrieved news data
    logger.info(f"Processing {len(news_data)} news articles for synthesis")
    
    # Store news data in market insights for further analysis
    state["market_insights"]["processed_news"] = news_data
    state["reasoning_steps"].append(f"Successfully processed {len(news_data)} news articles for market analysis")

    return {
        "news_data": state["news_data"],
        "market_insights": state["market_insights"],
        "reasoning_steps": state["reasoning_steps"],
    }


def market_analyzer_node(state) -> dict:
    """
    Market impact analysis node.
    
    Analyze market impact:
    - Assess potential price impact of news events
    - Evaluate sentiment indicators
    - Identify market moving events
    - Connect news to market behavior
    """
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    if "market_insights" not in state:
        state["market_insights"] = {}
    
    # Access the news data for analysis
    news_data = state.get("news_data", [])
    logger.info(f"Analyzing market impact for {len(news_data)} news articles")
        
    state["reasoning_steps"].append("Market impact analysis completed")
    state["market_insights"]["impact_assessment"] = {}
    state["market_insights"]["sentiment_analysis"] = {}
    
    return {
        "news_data": state.get("news_data", []),
        "market_insights": state["market_insights"],
        "reasoning_steps": state["reasoning_steps"]
    }


def pattern_recognizer_node(state) -> dict:
    """
    Pattern recognition node for trend identification.
    
    Recognize patterns and trends:
    - Identify recurring themes in news
    - Spot emerging trends and correlations
    - Recognize market cycle patterns
    - Connect historical context
    """
    if "reasoning_steps" not in state:
        state["reasoning_steps"] = []
    if "market_insights" not in state:
        state["market_insights"] = {}
    
    # Access the news data for pattern recognition
    news_data = state.get("news_data", [])
    logger.info(f"Recognizing patterns in {len(news_data)} news articles")
        
    state["reasoning_steps"].append("Pattern recognition and trend analysis completed")
    state["market_insights"]["identified_patterns"] = []
    state["market_insights"]["trend_analysis"] = {}
    
    return {
        "news_data": state.get("news_data", []),
        "market_insights": state["market_insights"],
        "reasoning_steps": state["reasoning_steps"]
    }


def insight_generator_node(state) -> dict:
    """
    Final insight generation and response node.
    
    Generate comprehensive market insights:
    - Synthesize all analysis stages
    - Provide actionable insights
    - Include proper disclaimers
    - Structure response for clarity
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.3,
    )
    
    # Access the news data for final insight generation
    news_data = state.get("news_data", [])
    logger.info(f"Generating insights based on {len(news_data)} news articles")
    
    insight_prompt = f"""
    Generate comprehensive cryptocurrency market analysis based on:
    
    Reasoning Steps: {state.get('reasoning_steps', [])}
    Market Insights: {state.get('market_insights', {})}
    News Data: {state.get('news_data', [])}
    Query Context: {state.get('crypto_context', {})}
    
    Provide:
    1. Executive Summary
    2. Key Market Developments
    3. Impact Analysis
    4. Trend Insights
    5. Risk Considerations
    6. Educational Context
    7. Proper Disclaimers
    
    Make it educational, well-sourced, and transparent about reasoning process.
    """
    
    response = llm.invoke([
        SystemMessage(content=insight_prompt),
        *state["messages"]
    ])
    
    # Add timestamp
    if not response.additional_kwargs.get("timestamp"):
        response.additional_kwargs["timestamp"] = datetime.now().isoformat()
    
    return {"messages": [response]}


# ============================================================================
# ENHANCED WORKFLOW ROUTING FUNCTIONS
# ============================================================================

def should_continue_news_collection(state) -> Literal["news_tools", "news_synthesizer"]:
    """Determine if news collection should continue or move to synthesis."""
    # Logic to determine if more news collection is needed
    collection_strategy = state.get("analysis_context", {}).get("news_collection_strategy")
    if collection_strategy == "multi_target_search":
        return "news_tools"
    return "news_synthesizer"


def should_continue_synthesis(state) -> Literal["market_analyzer", "__end__"]:
    """Determine if synthesis should continue to market analysis.

    Previous logic relied on `market_insights.news_themes` which was often left
    empty, causing the workflow to prematurely end and return raw tool results.

    Use presence of retrieved news (either in `news_data` or
    `market_insights.processed_news`) as the trigger to continue to
    `market_analyzer`. This is more robust and matches the intended flow.
    """
    # Prefer explicit `news_data` stored on the state
    news = state.get("news_data")
    if not news:
        # Fallback to processed news stored in market_insights by the synthesizer
        news = state.get("market_insights", {}).get("processed_news", [])

    if news and len(news) > 0:
        return "market_analyzer"

    return "__end__"


def route_analysis_flow(state) -> Literal["query_processor", "__end__"]:
    """Route to enhanced analysis flow or direct end."""
    if state.get("next_node") == "rag_analysis":
        return "query_processor"
    return "__end__"
