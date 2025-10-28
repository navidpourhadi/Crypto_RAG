"""
Cryptocurrency Market Analysis Agent

This module implements an intelligent cryptocurrency market analysis agent that provides
comprehensive Bitcoin and cryptocurrency market insights using RAG (Retrieval-Augmented Generation)
powered by real-time news data from TradingView and other cryptocurrency sources.

The agent leverages LangGraph for sophisticated workflow management and MongoDB for
conversation state persistence, enabling contextual market analysis conversations.
"""

from datetime import datetime
from uuid import UUID

from langchain_core.messages import HumanMessage
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.nodes import (
    supervisor,
    query_processor_node,
    news_collector_node,
    news_synthesizer_node,
    market_analyzer_node,
    pattern_recognizer_node,
    insight_generator_node,
    should_continue_news_collection,
    should_continue_synthesis,
    route_analysis_flow
)

from app.agent.tools import news_tools

# Additional tools for future expansion (portfolio tracking, price alerts, etc.)
# from app.agent.tools import portfolio_tools, price_tools, news_tools
from app.core.config import settings
from app.core.mongodb import MongoDatabase


lf = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    host=settings.LANGFUSE_HOST
)

langfuse_handler = CallbackHandler(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    update_trace=True
)



class ExtendedState(MessagesState):
    """
    Extended state for the cryptocurrency market analysis agent workflow.
    
    Maintains conversation context including:
    - next_node: Routing information for workflow navigation
    - analysis_context: Market analysis context and retrieved news data
    - crypto_context: Cryptocurrency-specific context (prices, trends, etc.)
    - news_data: Structured storage for retrieved news articles and sources
    - reasoning_steps: Track analysis reasoning steps for transparency
    - market_insights: Synthesized market insights and patterns
    """

    next_node: str = ""
    analysis_context: dict = {}
    crypto_context: dict = {}
    news_data: list = []
    reasoning_steps: list = []
    market_insights: dict = {}


async def get_checkpointer():
    """
    Get an asynchronous MongoDB checkpointer for conversation state persistence.
    
    Enables the cryptocurrency analysis agent to maintain conversation context
    across multiple interactions, allowing for follow-up questions about
    specific cryptocurrencies, continued market analysis, and personalized
    conversation history.
    """
    client = MongoDatabase.get_client()
    # MongoDB database name for storing cryptocurrency conversation checkpoints
    return AsyncMongoDBSaver(client)


async def create_agent_graph() -> StateGraph:
    """
    Create and configure an enhanced cryptocurrency market analysis agent workflow graph.

    Enhanced multi-stage workflow for superior market analysis reasoning:
    
    STAGE 1 - QUERY PROCESSING:
    User Query → Supervisor (intelligent routing) → Query Analysis (extract crypto entities, intent, timeframe)
    
    STAGE 2 - STRATEGIC NEWS COLLECTION:
    Query Analysis → News Collection (multiple targeted searches) → News Synthesis (relevance scoring, deduplication)
    
    STAGE 3 - MARKET ANALYSIS REASONING:
    News Synthesis → Market Impact Analysis (price/sentiment impact) → Pattern Recognition (trends, correlations)
    
    STAGE 4 - INSIGHT GENERATION:
    Pattern Recognition → Market Synthesis (comprehensive analysis) → Final Response (actionable insights)
    
    Benefits:
    - Multi-stage reasoning prevents hallucination
    - Strategic news collection ensures comprehensive context
    - Pattern recognition identifies market signals
    - Structured analysis provides transparent reasoning
    
    Returns:
        StateGraph: Enhanced workflow graph with MongoDB checkpointing for reasoning persistence
    """
    workflow = StateGraph(ExtendedState)

    # Intelligent routing and query processing
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("query_processor", query_processor_node)
    
    # Strategic news collection and synthesis
    workflow.add_node("news_collector", news_collector_node)
    workflow.add_node("news_synthesizer", news_synthesizer_node)
    
    # Market analysis and pattern recognition
    workflow.add_node("market_analyzer", market_analyzer_node)
    workflow.add_node("pattern_recognizer", pattern_recognizer_node)
    
    # Final insight generation and response
    workflow.add_node("insight_generator", insight_generator_node)
    
    # Tools integration
    workflow.add_node("news_tools", ToolNode(news_tools))

    # Define enhanced workflow edges
    workflow.add_edge(START, "supervisor")

    # Route from supervisor to enhanced analysis flow
    workflow.add_conditional_edges(
        "supervisor",
        route_analysis_flow,
        {
            "query_processor": "query_processor",  # Enhanced analysis flow
            "__end__": END,  # Direct answer path
        },
    )

    # Enhanced multi-stage analysis flow
    workflow.add_edge("query_processor", "news_collector")
    workflow.add_conditional_edges(
        "news_collector",
        should_continue_news_collection,
        {
            "news_tools": "news_tools",
            "news_synthesizer": "news_synthesizer",
        },
    )
    workflow.add_edge("news_tools", "news_synthesizer") 
    workflow.add_conditional_edges(
        "news_synthesizer",
        should_continue_synthesis,
        {
            "market_analyzer": "market_analyzer",
            "__end__": END,
        },
    )
    workflow.add_edge("market_analyzer", "pattern_recognizer")
    workflow.add_edge("pattern_recognizer", "insight_generator")
    workflow.add_edge("insight_generator", END)

    checkpointer = await get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)




class Agent:
    """
    Cryptocurrency Market Analysis Agent for intelligent Bitcoin and crypto market insights.

    This agent provides comprehensive cryptocurrency market analysis by:
    - Processing natural language queries about cryptocurrencies, prices, and market trends
    - Searching real-time news data from TradingView and other sources using RAG technology
    - Generating informed market analysis based on current news and developments
    - Maintaining conversation context for follow-up questions and personalized interactions

    Features:
    - Intelligent request routing based on cryptocurrency analysis intent
    - RAG-powered news search for factual market context
    - Educational market analysis with proper disclaimers
    - Conversation state persistence through MongoDB checkpointing
    - Support for both threaded conversations and ephemeral interactions
    """

    def __init__(self, graph=None):
        """
        Initialize the Cryptocurrency Market Analysis Agent.
        
        Args:
            graph: Optional pre-configured StateGraph for the agent workflow.
                  If not provided, will be created during first use.
        """
        self.graph = graph
        self._initialized = graph is not None

    @classmethod
    async def create(cls):
        """
        Asynchronously create and initialize a Cryptocurrency Market Analysis Agent.
        
        This factory method sets up the complete agent workflow including:
        - Multi-stage reasoning for superior market analysis
        - Strategic news collection and synthesis
        - Pattern recognition and trend analysis
        - MongoDB checkpointing for conversation persistence
        - Transparent reasoning process tracking
        
        Args:
            enhanced: Use enhanced multi-stage workflow for better reasoning (default: True)
        
        Returns:
            Agent: Fully initialized cryptocurrency market analysis agent
        """
        
        graph = await create_agent_graph()
        return cls(graph=graph)

    @property
    def is_initialized(self) -> bool:
        """Check if the cryptocurrency analysis agent has been properly initialized."""
        return self._initialized and self.graph is not None

    async def ensure_initialized(self):
        """
        Ensure the cryptocurrency market analysis agent is fully initialized before processing requests.
        
        Lazy initialization of the agent workflow graph and news search capabilities.
        """
        if not self.is_initialized:
            self.graph = await create_agent_graph()
            self._initialized = True

    async def generate_response(
        self,
        user_input: HumanMessage,
        thread_id: UUID | None = None,
    ) -> str:
        """
        Generate comprehensive cryptocurrency market analysis response to user queries.
        
        Processes user questions about cryptocurrencies, market trends, news, and analysis
        using the RAG-powered news search system and intelligent market analysis.
        
        Args:
            user_input: User's cryptocurrency-related question or request
            thread_id: Optional conversation thread ID for maintaining context across interactions
            user_id: Optional user identifier for personalized responses
            
        Returns:
            str: Comprehensive market analysis response with news-based insights
            
        Process:
        1. Routes query based on cryptocurrency analysis intent
        2. Searches relevant news from TradingView sources if needed
        3. Synthesizes market analysis with educational context
        4. Provides response with proper disclaimers and source attribution
        """
        # Ensure the agent is initialized
        await self.ensure_initialized()

        # Add timestamp to user message if not present
        if not user_input.additional_kwargs.get("timestamp"):
            user_input.additional_kwargs["timestamp"] = datetime.now().isoformat()

        config = {
            "configurable": {"thread_id": thread_id},
            "callbacks": [langfuse_handler],
        }

        # Prepare the input state for enhanced cryptocurrency market analysis
        input_state = {
            "messages": [user_input],
            "next_node": "",
            "analysis_context": {},   # Market analysis context and retrieved news
            "crypto_context": {},     # Cryptocurrency-specific context (prices, trends, etc.)
            "news_data": [],          # Structured storage for retrieved news articles
            "reasoning_steps": [],    # Track analysis reasoning steps for transparency
            "market_insights": {},    # Synthesized market insights and patterns
        }

        if thread_id:
            # Persistent conversation with context for follow-up cryptocurrency questions
            result = await self.graph.ainvoke(
                input_state,
                config=config,
            )
        else:
            # Single-turn cryptocurrency analysis without conversation persistence
            result = await self.graph.ainvoke(input_state, config=config)

        return result["messages"][-1].content


_agent_instance = None


async def get_agent():
    """Get or create the singleton agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = await Agent.create()
    return _agent_instance
