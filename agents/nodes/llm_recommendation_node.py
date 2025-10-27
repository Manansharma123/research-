"""LLM recommendation node for business advisor workflow."""

import json
import logging
from typing import Dict, Any, List
from agents.state import BusinessAnalysisState
from utils.api_clients import OpenAIClient, PerplexityClient
from utils.property_analyzer import PropertyAnalyzer

logger = logging.getLogger(__name__)


def llm_recommendation_node(state: BusinessAnalysisState) -> Dict[str, Any]:
    """
    Node to generate business recommendations using OpenAI LLM.
    
    Args:
        state: Current state of the workflow
        
    Returns:
        Updated state with LLM recommendations
    """
    logger.info("Starting LLM recommendation node")
    
    try:
        # Extract information from state
        business_type = state.get("business_type", "business")
        area_name = state.get("area_name", "unknown area")
        demographic_data = state.get("demographics", {})
        nearby_businesses = state.get("nearby_businesses", []) or []
        sentiment_analysis = state.get("sentiment_analysis", {}) or {}
        chain_brands = state.get("chain_brands", []) or []
        social_validation = state.get("social_validation", {}) or {}
        latitude = state.get("latitude", 0.0)
        longitude = state.get("longitude", 0.0)
        scraped_data = state.get("scraped_data", []) or []
        
        # Log scraped data COMPLETELY before passing to LLM
        logger.info(f"📊 Scraped data received: {len(scraped_data)} items")
        if scraped_data:
            logger.info("=" * 100)
            logger.info("🌐 COMPLETE SCRAPED DATA (passing to LLM):")
            logger.info("=" * 100)
            
            for i, item in enumerate(scraped_data, 1):  # Show ALL items
                logger.info(f"\n{'='*50}")
                logger.info(f"[{i}] {item.get('name') or item.get('school_name', 'N/A')}")
                logger.info(f"{'='*50}")
                
                # Log ALL fields based on data type
                if 'school_name' in item:
                    logger.info(f"📚 Type: SCHOOL")
                    logger.info(f"   ⭐ Rating: {item.get('rating', 'N/A')}")
                    logger.info(f"   💰 Fees: {item.get('fees', 'N/A')}")
                    logger.info(f"   📋 Board: {item.get('board', 'N/A')}")
                    logger.info(f"   🎓 Grade: {item.get('grade', 'N/A')}")
                    
                elif 'cuisines' in item:
                    logger.info(f"🍽️  Type: RESTAURANT/CAFE")
                    logger.info(f"   ⭐ Rating: {item.get('rating', 'N/A')}")
                    logger.info(f"   💰 Price for Two: {item.get('price_for_two', 'N/A')}")
                    logger.info(f"   🍴 Cuisines: {item.get('cuisines', 'N/A')}")
                    logger.info(f"   📍 Area: {item.get('area', 'N/A')}")
                    logger.info(f"   🎁 Offers: {item.get('offers', 'N/A')}")
                    logger.info(f"   📏 Distance: {item.get('distance', 'N/A')}")
                    
                elif 'amenities' in item:
                    logger.info(f"🏨 Type: HOTEL")
                    logger.info(f"   ⭐ Rating: {item.get('rating', 'N/A')}")
                    logger.info(f"   💰 Room Price: {item.get('price', 'N/A')}")
                    logger.info(f"   📍 Location: {item.get('location', 'N/A')}")
                    logger.info(f"   🏊 Amenities: {item.get('amenities', 'N/A')}")
                    logger.info(f"   📝 Description: {item.get('description', 'N/A')[:100]}...")
                    
                else:
                    logger.info(f"🏪 Type: GENERAL BUSINESS")
                    logger.info(f"   ⭐ Rating: {item.get('rating', 'N/A')}")
                    logger.info(f"   💰 Price: {item.get('price', 'N/A')}")
                    logger.info(f"   📝 All Data: {item}")
            
            logger.info("\n" + "=" * 100)
            logger.info(f"✅ Total items scraped and sent to LLM: {len(scraped_data)}")
            logger.info("=" * 100 + "\n")
        else:
            logger.info("⚠️  No scraped data available - using existing data sources only")
        
        # Initialize property analyzer
        property_analyzer = PropertyAnalyzer()
        
        # Generate property-based analysis
        property_analysis = property_analyzer.generate_property_analysis(
            business_type or "business",
            area_name or "unknown area",
            latitude,
            longitude
        )
        
        # Create prompt for LLM with property analysis and scraped data
        prompt = _create_recommendation_prompt(
            business_type or "business", 
            area_name or "unknown area", 
            demographic_data or {}, 
            nearby_businesses or [], 
            sentiment_analysis or {}, 
            chain_brands or [],
            social_validation or {},
            property_analysis or {},
            scraped_data or []
        )
        
        logger.info(f"Generating recommendations for {business_type} in {area_name}")
        
        # Initialize Perplexity client for intelligent recommendations
        logger.info("🧠 Using Perplexity AI for intelligent pros/cons/suggestions")
        perplexity_client = PerplexityClient()
        
        # Generate recommendations using Perplexity
        response = perplexity_client.generate_recommendation(prompt)
        
        # Parse JSON response
        try:
            recommendation_data = json.loads(response.replace("```json", "").replace("```", ""))
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            recommendation_data = {
                "pros": ["Market analysis completed"],
                "cons": ["Unable to generate detailed recommendations"],
                "suggestions": [f"Consider opening a {business_type} in {area_name} after manual review"],
                "recommendation": f"Further analysis required for {business_type} opportunity in {area_name}"
            }
        
        logger.info("Successfully generated LLM recommendations")
        
        # Return updated state
        return {
            **state,
            "llm_recommendation": recommendation_data,
            "current_step": "llm_recommendation_completed"
        }
        
    except Exception as e:
        error_msg = f"Error in LLM recommendation node: {str(e)}"
        logger.error(error_msg)
        # Provide fallback recommendations
        fallback_recommendation = {
            "pros": ["Location identified", "Demographic data available"],
            "cons": ["Unable to analyze market conditions"],
            "suggestions": [f"Manually research the {state.get('business_type', 'business')} market in {state.get('area_name', 'the area')}"],
            "recommendation": f"Manual analysis recommended for {state.get('business_type', 'business')} opportunity"
        }
        return {
            **state,
            "llm_recommendation": fallback_recommendation,
            "error": error_msg,
            "current_step": "llm_recommendation_error"
        }


def _create_recommendation_prompt(business_type: str, area_name: str, 
                                 demographic_data: Dict[str, Any], 
                                 nearby_businesses: List[Dict], 
                                 sentiment_analysis: Dict[str, Any],
                                 chain_brands: List[Dict[str, Any]],
                                 social_validation: Dict[str, Any],
                                 property_analysis: Dict[str, Any],
                                 scraped_data: List[Dict[str, Any]]) -> str:
    """
    Create a prompt for the LLM to generate business recommendations.
    
    Args:
        business_type: Type of business to analyze
        area_name: Name of the area
        demographic_data: Demographic information
        nearby_businesses: List of nearby businesses
        sentiment_analysis: Sentiment analysis results
        chain_brands: List of chain brands in the area
        social_validation: Social media validation results
        property_analysis: Property-specific analysis
        scraped_data: Freshly scraped data from web sources
        
    Returns:
        Formatted prompt string
    """
    # Prepare business summary
    business_count = len(nearby_businesses)
    avg_rating = sum(b.get("rating", 0) or 0 for b in nearby_businesses) / business_count if business_count > 0 else 0
    
    # Prepare sentiment summary
    market_sentiment = sentiment_analysis.get("market_sentiment", {})
    avg_sentiment = market_sentiment.get("average_sentiment", 0)
    positive_pct = market_sentiment.get("positive_percentage", 0)
    negative_pct = market_sentiment.get("negative_percentage", 0)
    
    # Get business-specific sentiments
    business_sentiments = sentiment_analysis.get("business_sentiments", [])
    
    prompt = f"""
You are an expert business consultant with access to real-time market intelligence evaluating the feasibility of opening a new {business_type} in {area_name}.

🎯 YOUR MISSION: Provide COMPLETE, ACTIONABLE, and INSIGHTFUL analysis that demonstrates deep market understanding.

CRITICAL INSTRUCTIONS:
1. You MUST reference SPECIFIC NUMBERS and DATA POINTS from all sources below in every pro, con, and suggestion
2. Do NOT use vague terms like "high", "low", "good", or "many" without citing exact figures
3. NEVER mention data gaps, missing information, or recommend manual research
4. Use Perplexity's online search capabilities to enhance insights with current market trends and industry benchmarks
5. Provide COMPLETE recommendations as if you have full market intelligence
6. Focus on ACTIONABLE strategies that can be implemented immediately

═══════════════════════════════════════════════════════════════════════════════
📊 DATA SOURCE 1: PROPTEK DATABASE - PROPERTY FEATURES
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(property_analysis, indent=2)}

KEY METRICS TO REFERENCE:
- Footfall Score: {property_analysis.get('footfall_score', 'N/A')}
- Affluence Level: {property_analysis.get('affluence_level', 'N/A')}
- Brand Density: {property_analysis.get('brand_density', 'N/A')}
- Retail Presence: {property_analysis.get('retail_presence', 'N/A')}

═══════════════════════════════════════════════════════════════════════════════
👥 DATA SOURCE 2: DEMOGRAPHICS
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(demographic_data, indent=2)}

KEY METRICS TO REFERENCE:
- Total Population: {demographic_data.get('total_population', 'N/A')}
- Children (0-18 yrs): {demographic_data.get('children_0_18', 'N/A')}
- Young Adults (19-35 yrs): {demographic_data.get('young_adults_19_35', 'N/A')}
- High Income Households (>₹10L): {demographic_data.get('high_income_households', 'N/A')}
- Middle Income Households (₹5-10L): {demographic_data.get('middle_income_households', 'N/A')}

═══════════════════════════════════════════════════════════════════════════════
🏪 DATA SOURCE 3: COMPETITOR ANALYSIS
═══════════════════════════════════════════════════════════════════════════════
- Number of Competing {business_type}s: {business_count}
- Average Rating: {avg_rating:.2f}/5.0
- Market Sentiment Score: {avg_sentiment:.2f} (on -1 to +1 scale)
- Positive Reviews: {positive_pct:.1f}%
- Negative Reviews: {negative_pct:.1f}%
- Total Reviews Analyzed: {sentiment_analysis.get('total_reviews_analyzed', 0)}
"""

    # Add social media validation if available
    if social_validation and social_validation.get('status') != 'error':
        prompt += f"""
═══════════════════════════════════════════════════════════════════════════════
📱 DATA SOURCE 4: SOCIAL MEDIA & ONLINE REPUTATION
═══════════════════════════════════════════════════════════════════════════════
- Demand Assessment: {social_validation.get('assessment', 'N/A')}
- Confidence Score: {social_validation.get('confidence_score', 0)}%
- Local Posts Found: {social_validation.get('total_local_posts', 0)}
- Hashtags Analyzed: {social_validation.get('hashtags_analyzed', 0)}
"""

    prompt += """
COMPETITOR SENTIMENTS:
"""
    
    # Add top 3 competitors
    for i, biz_sent in enumerate(business_sentiments[:3], 1):
        metrics = biz_sent.get("metrics", {})
        prompt += f"""
{i}. {biz_sent.get('business_name')}
   - Positive: {metrics.get('positive_percentage', 0):.1f}%
   - Negative: {metrics.get('negative_percentage', 0):.1f}%
"""
    
    # Add chain brand information
    if chain_brands:
        prompt += f"\nCHAIN BRANDS IN AREA:\n"
        brand_counts = {}
        for brand in chain_brands:
            brand_name = brand.get('brand', 'Unknown')
            brand_counts[brand_name] = brand_counts.get(brand_name, 0) + 1
        
        for brand, count in brand_counts.items():
            prompt += f"- {brand}: {count} location{'s' if count > 1 else ''}\n"
    
    # Add scraped data section
    if scraped_data and len(scraped_data) > 0:
        # Determine the source website based on data structure
        data_source = "COMPETITOR WEBSITES"
        if scraped_data[0].get('school_name'):
            data_source = "EDUSTOKE.COM"
        elif scraped_data[0].get('cuisines'):
            data_source = "SWIGGY.COM"
        elif scraped_data[0].get('amenities'):
            data_source = "BOOKING.COM"
        
        prompt += f"""
═══════════════════════════════════════════════════════════════════════════════
🌐 DATA SOURCE 5: {data_source} - REAL-TIME COMPETITOR DATA ({len(scraped_data)} items)
═══════════════════════════════════════════════════════════════════════════════
This is FRESH, real-time data scraped directly from {data_source}. Use this to identify:
- Exact pricing ranges and gaps
- Rating benchmarks and quality standards
- Service/product offerings and market gaps
- Promotional strategies and offers

"""
        
        # Limit to first 10 items to avoid token limits
        for i, item in enumerate(scraped_data[:10], 1):
            prompt += f"{i}. "
            
            # Handle different data formats (schools vs restaurants/hotels)
            if 'school_name' in item:
                # School data
                prompt += f"{item.get('school_name', 'N/A')}\n"
                if item.get('rating'):
                    prompt += f"   Rating: {item.get('rating')}\n"
                if item.get('fees'):
                    prompt += f"   Fees: {item.get('fees')}\n"
                if item.get('board'):
                    prompt += f"   Board: {item.get('board')}\n"
                if item.get('grade'):
                    prompt += f"   Grade: {item.get('grade')}\n"
            elif 'cuisines' in item:
                # Restaurant/Cafe data (Swiggy Dineout)
                prompt += f"{item.get('name', 'N/A')}\n"
                if item.get('rating'):
                    prompt += f"   Rating: {item.get('rating')}\n"
                if item.get('price_for_two'):
                    prompt += f"   Price for Two: {item.get('price_for_two')}\n"
                if item.get('cuisines'):
                    prompt += f"   Cuisines: {item.get('cuisines')}\n"
                if item.get('area'):
                    prompt += f"   Area: {item.get('area')}\n"
                if item.get('distance'):
                    prompt += f"   Distance: {item.get('distance')}\n"
                if item.get('offers'):
                    prompt += f"   Offers: {item.get('offers')}\n"
            elif 'amenities' in item:
                # Hotel data (Booking.com)
                prompt += f"{item.get('name', 'N/A')}\n"
                if item.get('rating'):
                    prompt += f"   Rating: {item.get('rating')}\n"
                if item.get('price'):
                    prompt += f"   Room Price: {item.get('price')}\n"
                if item.get('location'):
                    prompt += f"   Location: {item.get('location')}\n"
                if item.get('amenities'):
                    prompt += f"   Amenities: {item.get('amenities')}\n"
                if item.get('description'):
                    prompt += f"   Description: {item.get('description')[:80]}\n"
            else:
                # Generic data
                prompt += f"{item.get('name', 'N/A')}\n"
                if item.get('price'):
                    prompt += f"   Price: {item.get('price')}\n"
                if item.get('rating'):
                    prompt += f"   Rating: {item.get('rating')}\n"
            
            prompt += "\n"
        
        if len(scraped_data) > 10:
            prompt += f"\n... and {len(scraped_data) - 10} more competitors with similar data\n"
    
    prompt += """
═══════════════════════════════════════════════════════════════════════════════
📋 OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Provide your analysis in JSON format with the following structure:

{
  "pros": [4-5 opportunities],
  "cons": [4-5 challenges],
  "suggestions": [6-7 actionable strategies],
  "recommendation": "one sentence summary"
}

═══════════════════════════════════════════════════════════════════════════════
✅ MANDATORY REQUIREMENTS FOR EACH SECTION
═══════════════════════════════════════════════════════════════════════════════

📌 PROS (4-5 items):
Each pro MUST:
✓ Cite at least ONE specific number from the data sources
✓ Reference which data source it comes from
✓ Combine insights from multiple sources when possible

Examples:
✓ GOOD: "Strong target market with 30,652 children (0-18 yrs) and 10,389 high-income households (>₹10L) within 3km radius"
✗ BAD: "Good demographics in the area"

✓ GOOD: "Footfall score of 66 indicates high visibility, supported by 15 competing cafes with average rating 4.2 showing proven demand"
✗ BAD: "High footfall and good location"

📌 CONS (4-5 items):
Each con MUST:
✓ Cite specific numbers showing the challenge
✓ Reference competitor data or market realities
✓ Focus on actionable business challenges

Examples:
✓ GOOD: "High competition with 15 existing cafes averaging 4.2 rating and price range ₹400-₹600 for two (Source: Swiggy.com)"
✗ BAD: "High competition in the area"

✓ GOOD: "Premium pricing pressure as 8 out of 15 competitors charge ₹500+ for two, requiring strong differentiation"
✗ BAD: "Pricing challenges in the market"

📌 SUGGESTIONS (6-7 items):
Each suggestion MUST:
✓ Be DYNAMIC and based on scraped data analysis
✓ Include specific numbers (prices, ratings, percentages)
✓ Identify competitive advantages or market gaps
✓ Be immediately actionable

═══════════════════════════════════════════════════════════════════════════════
🎯 CATEGORY-SPECIFIC SUGGESTION TEMPLATES
═══════════════════════════════════════════════════════════════════════════════

🍽️ FOR CAFES/RESTAURANTS:
1. PRICING: "Price between ₹X-₹Y for two based on competitor range ₹A-₹B (Source: Swiggy.com) to position as [budget/mid-range/premium]"
2. CUISINES: "Offer [specific cuisines] as competitors focus on [scraped cuisines], creating gap in [missing cuisine]"
3. RATING TARGET: "Aim for X+ rating as average competitor rating is Y (Source: Swiggy.com)"
4. OFFERS: "Introduce [specific offer] similar to competitors offering [scraped offers]"
5. LOCATION: "Target [specific area] as competitors are X km away (Source: Swiggy.com)"
6. DIFFERENTIATION: "Focus on [unique aspect] as only X% of competitors offer it"

🏨 FOR HOTELS:
1. ROOM PRICING: "Price rooms at ₹X-₹Y/night as competitors charge ₹A-₹B (Source: Booking.com)"
2. AMENITIES: "Must include [amenities] as X% of competitors offer them (Source: Booking.com)"
3. RATING TARGET: "Target X+ rating as competitor average is Y (Source: Booking.com)"
4. DIFFERENTIATION: "Add [specific amenity] as only X% of hotels provide it (market gap)"
5. TARGET SEGMENT: "Focus on [segment] based on Y high-income households (Source: Proptek Database)"

🏫 FOR SCHOOLS:
1. FEES: "Set fees at ₹X-₹Y annually as competitors charge ₹A-₹B (Source: Edustoke.com) for [board] schools"
2. BOARD: "Consider [board] as X% of schools use it (Source: Edustoke.com), or offer [alternative] to capture Y% market"
3. RATING TARGET: "Aim for X+ rating as competitor average is Y (Source: Edustoke.com)"
4. GRADES: "Offer [grades] as only X% of schools cover this range (market gap from Edustoke.com)"
5. TARGET MARKET: "Focus on Y children (0-18 yrs) and Z high-income households (Source: Proptek Database)"
6. DIFFERENTIATION: "Introduce [specific program] as no competitor offers it (Source: Edustoke.com)"

═══════════════════════════════════════════════════════════════════════════════
🔢 CRITICAL RULES
═══════════════════════════════════════════════════════════════════════════════

1. NEVER use vague terms: "high", "low", "good", "many", "few" without numbers
2. ALWAYS cite data source: "(Source: Booking.com)", "(Source: Swiggy.com)", "(Source: Edustoke.com)", "(Source: Proptek Database)"
3. CALCULATE ranges, averages, percentages from competitor data
4. IDENTIFY market gaps by comparing what exists vs what's missing
5. MAKE suggestions unique to THIS query based on THIS data
6. REFERENCE at least 3 different data sources in your analysis
7. Focus on ACTIONABLE insights that provide clear business value
8. Use Perplexity's online search to enhance insights with current market trends


═══════════════════════════════════════════════════════════════════════════════
📊 DATA SOURCE PRIORITY
═══════════════════════════════════════════════════════════════════════════════

Use ALL data sources in your analysis:

1. 📊 PROPTEK DATABASE → Foundation for location viability and demographics
2. 👥 DEMOGRAPHICS → Target market size and purchasing power
3. 🏪 COMPETITOR ANALYSIS → Market saturation and quality benchmarks
4. 📱 SOCIAL MEDIA → Demand validation and reputation signals
5. 🌐 BOOKING.COM / SWIGGY.COM / EDUSTOKE.COM → Real-time competitive intelligence (MOST IMPORTANT for suggestions)

Each pro/con/suggestion MUST reference at least ONE specific data point.
Combine multiple sources for stronger insights.

═══════════════════════════════════════════════════════════════════════════════
🚀 FINAL REMINDER: COMPLETE & CONFIDENT ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

Your analysis should demonstrate:
✓ Deep market understanding with specific numbers
✓ Strategic thinking with actionable recommendations
✓ Competitive intelligence from real-time data
✓ Confidence in your recommendations
✓ NO mentions of data limitations or manual research needs

Leverage Perplexity's online search to provide current market context and industry trends that enhance your recommendations.

Now provide your comprehensive analysis in JSON format.
"""
    
    return prompt.strip()