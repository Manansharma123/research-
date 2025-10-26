"""Sentiment analysis utility using VADER."""

import logging
from typing import Dict, Any, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """VADER-based sentiment analyzer for reviews."""
    
    def __init__(self):
        """Initialize VADER sentiment analyzer."""
        self.analyzer = SentimentIntensityAnalyzer()
        logger.info("VADER sentiment analyzer initialized")
    
    def analyze_reviews_batch(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of reviews.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of reviews with sentiment scores added
        """
        analyzed_reviews = []
        
        for review in reviews:
            # Get review text
            text = review.get("snippet", "") or review.get("text", "")
            
            if not text or len(text) < 10:
                continue
            
            # Analyze sentiment
            scores = self.analyzer.polarity_scores(text)
            
            # Add sentiment to review
            review_with_sentiment = review.copy()
            review_with_sentiment["sentiment"] = {
                "compound": scores["compound"],
                "pos": scores["pos"],
                "neu": scores["neu"],
                "neg": scores["neg"],
                "label": self._get_sentiment_label(scores["compound"])
            }
            
            analyzed_reviews.append(review_with_sentiment)
        
        return analyzed_reviews
    
    def aggregate_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate sentiment scores across multiple reviews.
        
        Args:
            reviews: List of reviews with sentiment scores
            
        Returns:
            Aggregated sentiment metrics
        """
        if not reviews:
            return {
                "average_sentiment": 0,
                "positive_percentage": 0,
                "negative_percentage": 0,
                "neutral_percentage": 0,
                "total_reviews": 0
            }
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        compound_scores = []
        
        for review in reviews:
            sentiment = review.get("sentiment", {})
            compound = sentiment.get("compound", 0)
            compound_scores.append(compound)
            
            label = sentiment.get("label", "neutral")
            if label == "positive":
                positive_count += 1
            elif label == "negative":
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(reviews)
        avg_compound = sum(compound_scores) / total if compound_scores else 0
        
        return {
            "average_sentiment": avg_compound,
            "positive_percentage": (positive_count / total) * 100,
            "negative_percentage": (negative_count / total) * 100,
            "neutral_percentage": (neutral_count / total) * 100,
            "total_reviews": total,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count
        }
    
    def _get_sentiment_label(self, compound_score: float) -> str:
        """
        Convert compound score to sentiment label.
        
        Args:
            compound_score: VADER compound score (-1 to 1)
            
        Returns:
            Sentiment label: 'positive', 'negative', or 'neutral'
        """
        if compound_score >= 0.05:
            return "positive"
        elif compound_score <= -0.05:
            return "negative"
        else:
            return "neutral"