"""LangGraph workflow definition for business advisor."""

import logging
from langgraph.graph import StateGraph, START, END
from agents.state import BusinessAnalysisState
from agents.nodes.geocode_node import geocode_node
from agents.nodes.intent_node import intent_node
from agents.nodes.find_businesses_node import find_businesses_node
from agents.nodes.extract_reviews_node import extract_reviews_node
from agents.nodes.sentiment_node import sentiment_node
from agents.nodes.chain_brand_node import chain_brand_node  # Now finds all businesses
from agents.nodes.scraper_node import scraper_node  # NEW: Web scraper node
from agents.nodes.llm_recommendation_node import llm_recommendation_node
from agents.nodes.format_output_node import format_output_node
from agents.nodes.find_amenities_node import find_amenities_node
from agents.nodes.chart_generation_node import chart_generation_node

logger = logging.getLogger(__name__)

def create_workflow():
    """Create and compile the LangGraph workflow."""
    
    # Create graph
    workflow = StateGraph(BusinessAnalysisState)
    
    # Add nodes
    workflow.add_node("intent", intent_node)
    workflow.add_node("geocode", geocode_node)
    workflow.add_node("find_amenities", find_amenities_node)
    workflow.add_node("find_businesses", find_businesses_node)
    workflow.add_node("extract_reviews", extract_reviews_node)
    workflow.add_node("sentiment_analysis", sentiment_node)
    workflow.add_node("all_businesses", chain_brand_node)  # Renamed to reflect its new function
    workflow.add_node("scraper", scraper_node)  # NEW: Web scraper node
    workflow.add_node("llm_recommendation", llm_recommendation_node)
    workflow.add_node("chart_generation", chart_generation_node)  # NEW: Chart generation node
    workflow.add_node("format_output", format_output_node)
    
    # Define edges (sequential flow)
    workflow.add_edge(START, "intent")
    workflow.add_edge("intent", "geocode")
    workflow.add_edge("geocode", "find_amenities")
    workflow.add_edge("find_amenities", "find_businesses")
    workflow.add_edge("find_businesses", "extract_reviews")
    workflow.add_edge("extract_reviews", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "all_businesses")
    workflow.add_edge("all_businesses", "scraper")  # NEW: Run scraper after all_businesses
    workflow.add_edge("scraper", "llm_recommendation")  # Pass scraped data to LLM
    workflow.add_edge("llm_recommendation", "chart_generation")  # NEW: Generate charts after recommendations
    workflow.add_edge("chart_generation", "format_output")  # Format output with chart data
    workflow.add_edge("format_output", END)
    
    # Compile workflow
    app = workflow.compile()
    
    logger.info("LangGraph workflow created and compiled")
    
    return app