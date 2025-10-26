"""Sentiment analysis node - FIXED."""

import logging
from typing import Dict, Any
from agents.state import BusinessAnalysisState
from utils.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

def sentiment_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """Analyze sentiment of reviews."""
    logger.info("Starting sentiment analysis")
    
    try:
        reviews_data = state.get("reviews_data") or []
        
        if not reviews_data:
            logger.warning("No reviews to analyze")
            return {
                **state,
                "sentiment_analysis": {
                    "sentiment_summary": {
                        "positive_percentage": 0,
                        "neutral_percentage": 0,
                        "negative_percentage": 0
                    }
                },
                "current_step": "sentiment_completed"
            }
        
        # Filter reviews with text
        valid_reviews = []
        for review in reviews_data:
            text = review.get('snippet') or review.get('text') or ''
            if text and len(text.strip()) > 5:
                valid_reviews.append(review)
        
        logger.info(f"Analyzing {len(valid_reviews)} valid reviews out of {len(reviews_data)} total")
        
        # Analyze sentiments
        analyzer = SentimentAnalyzer()
        sentiment_results = analyzer.analyze_reviews_batch(valid_reviews)
        
        # Calculate summary
        positive_count = sum(1 for r in sentiment_results if r.get('sentiment', {}).get('compound', 0) >= 0.05)
        negative_count = sum(1 for r in sentiment_results if r.get('sentiment', {}).get('compound', 0) <= -0.05)
        neutral_count = len(sentiment_results) - positive_count - negative_count
        
        total = len(sentiment_results)
        
        sentiment_summary = {
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "positive_percentage": round((positive_count / total * 100), 1) if total > 0 else 0,
            "neutral_percentage": round((neutral_count / total * 100), 1) if total > 0 else 0,
            "negative_percentage": round((negative_count / total * 100), 1) if total > 0 else 0
        }
        
        result = {
            "sentiment_summary": sentiment_summary,
            "total_reviews": total,
            "review_sentiments": sentiment_results
        }
        
        logger.info(f"Sentiment analysis complete: {total} reviews analyzed")
        
        return {
            **state,
            "sentiment_analysis": result,
            "current_step": "sentiment_completed"
        }
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {
            **state,
            "sentiment_analysis": {
                "sentiment_summary": {
                    "positive_percentage": 0,
                    "neutral_percentage": 0,
                    "negative_percentage": 0
                }
            },
            "current_step": "sentiment_error"
        }