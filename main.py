"""Main execution script."""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continuing without loading .env file
    pass

from typing import Dict, Any, List, Optional
from agents.workflow import create_workflow
from agents.state import BusinessAnalysisState

def run_business_analysis(user_query: str):
    """Run complete business analysis."""
    
    # Initialize workflow
    workflow = create_workflow()
    
    # Create initial state
    initial_state: BusinessAnalysisState = {
        "business_query": user_query,
        "business_type": "",
        "demographic_data": {},
        "latitude": 0.0,
        "longitude": 0.0,
        "area_name": "",
        "nearby_businesses": [],
        "reviews_data": [],
        "sentiment_analysis": {},
        "llm_recommendation": {},
        "chain_brands": [],
        "nearby_amenities": {},
        "chart_data": {},
        "query_type": "business_analysis",
        "current_step": "initialized",
        "error": "",
        "messages": []
    }
    
    # Run workflow
    print("🚀 Starting business analysis...\n")
    result = workflow.invoke(initial_state)
    
    # Print results
    print("\n" + "="*60)
    print("📊 BUSINESS ANALYSIS COMPLETE")
    print("="*60)
    
    print(f"\n📍 Location: {result.get('area_name', 'N/A')}, {result.get('city', 'N/A')}")
    print(f"🏪 Business Type: {result.get('business_type', 'N/A')}")
    
    print(f"\n👥 Demographics:")
    demographics = result.get('demographics', {}) or {}
    print(f"   Population: {demographics.get('population', 'N/A') if demographics else 'N/A'}")
    
    nearby_businesses = result.get('nearby_businesses', []) or []
    print(f"\n🏪 Competition: {len(nearby_businesses)} competitors")
    
    print(f"\n📱 Social Media Validation:")
    social_validation = result.get('social_validation', {}) or {}
    if social_validation:
        print(f"   {social_validation.get('assessment', 'N/A')}")
        print(f"   Local Posts: {social_validation.get('total_local_posts', 0)}")
        print(f"   Confidence: {social_validation.get('confidence_score', 0)}%")
    else:
        print("   N/A")
    
    print(f"\n💡 Final Recommendation:")
    print(result.get('recommendation', 'N/A'))
    
    return result


def analyze_property(business_query: str) -> Dict[str, Any]:
    """Analyze property for business opportunity - interface for Streamlit app."""
    try:
        # Initialize workflow
        workflow = create_workflow()
        
        # Create initial state
        initial_state: BusinessAnalysisState = {
            "business_query": business_query,
            "business_type": "",
            "demographic_data": {},
            "latitude": 0.0,
            "longitude": 0.0,
            "area_name": "",
            "nearby_businesses": [],
            "reviews_data": [],
            "sentiment_analysis": {},
            "llm_recommendation": {},
            "chain_brands": [],
            "nearby_amenities": {},
            "chart_data": {},
            "query_type": "business_analysis",
            "current_step": "initialized",
            "error": "",
            "messages": []
        }
        
        # Run workflow
        result = workflow.invoke(initial_state)
        
        # Return result
        return result
        
    except Exception as e:
        return {
            "error": str(e)
        }


if __name__ == "__main__":
    # Test query
    query = "I want to open a grocery shop in Sector 88, Mohali"
    
    result = run_business_analysis(query)