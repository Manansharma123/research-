"""Streamlit UI for Business Location Advisor with LangGraph Integration."""

import streamlit as st
import pandas as pd
import os
import logging
from typing import Dict, Any
from main import analyze_property

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🏪 Business Location Advisor",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #34495e;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        color: #000000; /* Black text */
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #000000; /* Black text */
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #000000; /* Black text */
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #000000; /* Black text */
    }
    .centered-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin: 2rem 0;
    }
    .input-container {
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #000000; /* Black text */
    }
    .example-queries {
        background-color: #e8f4f8;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
        margin: 1rem 0;
        color: #000000; /* Black text */
    }
    /* Ensure all text in expanders is black */
    .streamlit-expanderHeader {
        color: #000000 !important;
    }
    .streamlit-expanderContent {
        color: #000000 !important;
    }
    /* Ensure metric labels are black */
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    [data-testid="stMetricValue"] {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def load_property_data():
    """Load property data."""
    try:
        # Get absolute path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "data", "property_project_lat_long.csv")
        
        if not os.path.exists(csv_path):
            csv_path = "data/property_project_lat_long.csv"
        
        df = pd.read_csv(csv_path)
        
        # Remove invalid coordinates and duplicates
        df = df.dropna(subset=['latitude', 'longitude'])
        df = df.drop_duplicates(subset=['latitude', 'longitude'])
        
        # Add property index
        df = df.reset_index(drop=True)
        
        return df
    
    except Exception as e:
        st.error(f"Error loading property data: {e}")
        return pd.DataFrame()


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_property_info(latitude: float, longitude: float):
    """Display property information."""
    st.markdown('<div class="sub-header">📍 Property Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Latitude", f"{latitude:.6f}")
        st.metric("Longitude", f"{longitude:.6f}")
    
    with col2:
        st.markdown("**How it works:**")
        st.markdown("- 🗺️ System extracts property location from your query")
        st.markdown("- 🔍 Finds businesses near that location")
        st.markdown("- 📊 Analyzes market conditions")
        st.markdown("- 🤖 Provides recommendations")


def display_workflow_progress(step):
    """Display current workflow step."""
    steps = [
        ("💭", "Understanding Intent", "intent"),
        ("🗺️", "Geocoding", "geocode"),
        ("🔍", "Finding Businesses", "find_businesses"),
        ("📝", "Extracting Reviews", "extract_reviews"),
        ("😊", "Sentiment Analysis", "sentiment_analysis"),
        ("🏪", "Chain Brands", "chain_brands"),
        ("🤖", "LLM Recommendations", "llm_recommendation"),
        ("📊", "Formatting Results", "format_output")
    ]
    
    st.markdown('<div class="sub-header">🔄 Analysis Pipeline</div>', unsafe_allow_html=True)
    
    cols = st.columns(len(steps))
    
    for i, (icon, name, step_name) in enumerate(steps):
        with cols[i]:
            if step == step_name:
                st.markdown(f"### {icon}\n**{name}**\n🔵 Active")
            elif steps.index((icon, name, step_name)) < steps.index([s for s in steps if s[2] == step][0] if step in [s[2] for s in steps] else steps[-1]):
                st.markdown(f"### {icon}\n**{name}**\n✅ Done")
            else:
                st.markdown(f"### {icon}\n**{name}**\n⚪ Pending")


def display_analysis_results(result):
    """Display comprehensive analysis results."""
    
    # Check for errors
    if result.get("error"):
        st.error(f"❌ Analysis Error: {result['error']}")
        return
    
    # Check query type
    query_type = result.get("query_type", "business_analysis")
    
    # Location Information
    st.markdown('<div class="sub-header">📍 Location Analysis</div>', unsafe_allow_html=True)
    location_info = f"""
    <div class="info-box">
    <strong>Area:</strong> {result.get('area_name', 'Unknown')}<br>
    <strong>Coordinates:</strong> {result.get('latitude', 0):.6f}, {result.get('longitude', 0):.6f}
    </div>
    """
    st.markdown(location_info, unsafe_allow_html=True)
    
    # For branded store lookup, only show chain brands
    if query_type == "branded_store_lookup":
        # All Businesses
        all_businesses = result.get('chain_brands', [])
        if all_businesses:
            st.markdown('<div class="sub-header">🏪 All Businesses Near You</div>', unsafe_allow_html=True)
            
            # Separate branded and non-branded businesses
            branded_businesses = [b for b in all_businesses if b.get('is_chain', False)]
            non_branded_businesses = [b for b in all_businesses if not b.get('is_chain', False)]
            
            # Group by brand for branded businesses
            from collections import defaultdict
            brand_groups = defaultdict(list)
            for business in branded_businesses:
                brand_name = business.get('brand', business.get('name', 'Unknown'))
                brand_groups[brand_name].append(business)
            
            # Display branded businesses
            if brand_groups:
                st.markdown('<div class="sub-header">🏢 Branded Stores</div>', unsafe_allow_html=True)
                for brand_name, locations in brand_groups.items():
                    with st.expander(f"**{brand_name}** ({len(locations)} location{'s' if len(locations) > 1 else ''})", expanded=False):
                        for loc in locations:
                            st.markdown(f"📍 **{loc.get('original_name', loc.get('name', 'Unknown'))}**")
                            st.markdown(f"- 📍 Area: {loc.get('area_name', 'Unknown')}")
                            st.markdown(f"- 🚶 Distance: {loc.get('distance', 0):.2f} km")
                            st.markdown(f"- 🌍 Coordinates: ({loc.get('lat', 0):.6f}, {loc.get('lon', 0):.6f})")
                            if 'rating' in loc and loc['rating'] is not None:
                                st.markdown(f"- ⭐ Rating: {loc['rating']}/5.0")
                            if 'reviews_count' in loc and loc['reviews_count'] > 0:
                                st.markdown(f"- 💬 Reviews: {loc['reviews_count']}")
                            st.markdown("---")
            
            # Display non-branded businesses
            if non_branded_businesses:
                st.markdown('<div class="sub-header">🏪 Local Businesses</div>', unsafe_allow_html=True)
                # Sort by rating and reviews count to highlight top businesses
                sorted_non_branded = sorted(
                    non_branded_businesses, 
                    key=lambda x: (x.get('rating', 0) or 0, x.get('reviews_count', 0) or 0), 
                    reverse=True
                )
                
                for business in sorted_non_branded:
                    # Highlight top-rated businesses
                    is_top_rated = (business.get('rating', 0) or 0) >= 4.0
                    is_most_reviewed = (business.get('reviews_count', 0) or 0) >= 50
                    
                    highlight = is_top_rated or is_most_reviewed
                    name_display = f"**{business.get('name', 'Unknown')}**" if highlight else business.get('name', 'Unknown')
                    
                    with st.expander(f"{name_display} ({business.get('types', 'Business')})", expanded=False):
                        st.markdown(f"📍 **{business.get('name', 'Unknown')}**")
                        st.markdown(f"- 📍 Area: {business.get('area_name', 'Unknown')}")
                        st.markdown(f"- 🚶 Distance: {business.get('distance', 0):.2f} km")
                        st.markdown(f"- 🌍 Coordinates: ({business.get('lat', 0):.6f}, {business.get('lon', 0):.6f})")
                        if 'rating' in business and business['rating'] is not None:
                            rating_star = "⭐" if is_top_rated else ""
                            st.markdown(f"- ⭐ Rating: {business['rating']}/5.0 {rating_star}")
                        if 'reviews_count' in business and business['reviews_count'] > 0:
                            review_star = "💬" if is_most_reviewed else ""
                            st.markdown(f"- 💬 Reviews: {business['reviews_count']} {review_star}")
                        st.markdown("---")
        else:
            st.info("No businesses found in this area.")
        return  # Exit early for branded store lookup
    
    # Market Overview (for business analysis)
    sentiment_data = result.get('sentiment_analysis', {})
    businesses = sentiment_data.get('businesses', [])
    
    if businesses:
        st.markdown('<div class="sub-header">📈 Market Overview</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏪 Competitors Found", len(businesses))
        
        with col2:
            avg_rating = sum(b.get('rating', 0) or 0 for b in businesses) / len(businesses)
            st.metric("⭐ Avg Rating", f"{avg_rating:.2f}/5.0")
        
        with col3:
            avg_sentiment = sentiment_data.get('average_sentiment', 0)
            st.metric("😊 Avg Sentiment", f"{avg_sentiment:.1f}%")
        
        with col4:
            total_reviews = sum(b.get('reviews_analyzed', 0) for b in businesses)
            st.metric("💬 Reviews Analyzed", total_reviews)
    
    # All Businesses
    all_businesses = result.get('chain_brands', [])
    if all_businesses:
        st.markdown('<div class="sub-header">🏪 All Businesses in Area</div>', unsafe_allow_html=True)
        
        # Separate branded and non-branded businesses
        branded_businesses = [b for b in all_businesses if b.get('is_chain', False)]
        non_branded_businesses = [b for b in all_businesses if not b.get('is_chain', False)]
        
        # Group by brand for branded businesses
        from collections import defaultdict
        brand_groups = defaultdict(list)
        for business in branded_businesses:
            brand_name = business.get('brand', business.get('name', 'Unknown'))
            brand_groups[brand_name].append(business)
        
        # Display branded businesses
        if brand_groups:
            st.markdown('<div class="sub-header">🏢 Branded Stores</div>', unsafe_allow_html=True)
            for brand_name, locations in brand_groups.items():
                with st.expander(f"**{brand_name}** ({len(locations)} location{'s' if len(locations) > 1 else ''})", expanded=False):
                    for loc in locations:
                        st.markdown(f"📍 **{loc.get('original_name', loc.get('name', 'Unknown'))}**")
                        st.markdown(f"- 📍 Area: {loc.get('area_name', 'Unknown')}")
                        st.markdown(f"- 🚶 Distance: {loc.get('distance', 0):.2f} km")
                        st.markdown(f"- 🌍 Coordinates: ({loc.get('lat', 0):.6f}, {loc.get('lon', 0):.6f})")
                        if 'rating' in loc and loc['rating'] is not None:
                            st.markdown(f"- ⭐ Rating: {loc['rating']}/5.0")
                        if 'reviews_count' in loc and loc['reviews_count'] > 0:
                            st.markdown(f"- 💬 Reviews: {loc['reviews_count']}")
                        st.markdown("---")
        
        # Display non-branded businesses with highlighting for top-rated/most reviewed
        if non_branded_businesses:
            st.markdown('<div class="sub-header">🏪 Local Businesses</div>', unsafe_allow_html=True)
            # Sort by rating and reviews count to highlight top businesses
            sorted_non_branded = sorted(
                non_branded_businesses, 
                key=lambda x: (x.get('rating', 0) or 0, x.get('reviews_count', 0) or 0), 
                reverse=True
            )
            
            for business in sorted_non_branded:
                # Highlight top-rated businesses
                is_top_rated = (business.get('rating', 0) or 0) >= 4.0
                is_most_reviewed = (business.get('reviews_count', 0) or 0) >= 50
                
                highlight = is_top_rated or is_most_reviewed
                name_display = f"**{business.get('name', 'Unknown')}**" if highlight else business.get('name', 'Unknown')
                
                with st.expander(f"{name_display} ({business.get('types', 'Business')})", expanded=False):
                    st.markdown(f"📍 **{business.get('name', 'Unknown')}**")
                    st.markdown(f"- 📍 Area: {business.get('area_name', 'Unknown')}")
                    st.markdown(f"- 🚶 Distance: {business.get('distance', 0):.2f} km")
                    st.markdown(f"- 🌍 Coordinates: ({business.get('lat', 0):.6f}, {business.get('lon', 0):.6f})")
                    if 'rating' in business and business['rating'] is not None:
                        rating_star = "⭐" if is_top_rated else ""
                        st.markdown(f"- ⭐ Rating: {business['rating']}/5.0 {rating_star}")
                    if 'reviews_count' in business and business['reviews_count'] > 0:
                        review_star = "💬" if is_most_reviewed else ""
                        st.markdown(f"- 💬 Reviews: {business['reviews_count']} {review_star}")
                    st.markdown("---")
    
    # Add after the business analysis results section
    if result.get("nearby_amenities"):
        st.markdown('<div class="sub-header">🏥 Nearby Amenities</div>', unsafe_allow_html=True)
        
        amenities = result["nearby_amenities"]
        
        # Create tabs for different amenity types
        amenity_tabs = st.tabs(list(amenities.keys()))
        
        for idx, (amenity_type, places) in enumerate(amenities.items()):
            with amenity_tabs[idx]:
                if places:
                    st.write(f"Found **{len(places)}** {amenity_type}(s) nearby")
                    
                    for i, place in enumerate(places[:5], 1):
                        with st.expander(f"{i}. {place['name']} ⭐ {place.get('rating', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Address:** {place.get('address', 'N/A')}")
                                st.write(f"**Rating:** {place.get('rating', 'N/A')} ({place.get('reviews_count', 0)} reviews)")
                            
                            with col2:
                                distance = place.get('distance', 0)
                                st.write(f"**Distance:** {distance:.2f} km")
                                
                                # Map link
                                lat = place.get('latitude')
                                lon = place.get('longitude')
                                if lat and lon:
                                    st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={lat},{lon})")
                else:
                    st.info(f"No {amenity_type}s found nearby")
    
    # LLM Recommendations
    llm_rec = result.get('llm_recommendation', {})
    
    if llm_rec:
        # Pros
        st.markdown('<div class="sub-header">✅ Opportunities (Pros)</div>', unsafe_allow_html=True)
        pros = llm_rec.get('pros', [])
        if pros:
            for i, pro in enumerate(pros, 1):
                st.markdown(f"**{i}.** {pro}")
        else:
            st.info("No pros identified")
        
        # Cons
        st.markdown('<div class="sub-header">⚠️ Challenges (Cons)</div>', unsafe_allow_html=True)
        cons = llm_rec.get('cons', [])
        if cons:
            for i, con in enumerate(cons, 1):
                st.markdown(f"**{i}.** {con}")
        else:
            st.info("No cons identified")
        
        # Suggestions
        st.markdown('<div class="sub-header">💡 Actionable Suggestions</div>', unsafe_allow_html=True)
        suggestions = llm_rec.get('suggestions', [])
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"**{i}.** {suggestion}")
        else:
            st.info("No suggestions available")
        
        # Final Recommendation
        st.markdown('<div class="sub-header">🎯 Final Recommendation</div>', unsafe_allow_html=True)
        recommendation = llm_rec.get('recommendation', 'Analysis complete')
        st.markdown(f'<div class="success-box"><strong>{recommendation}</strong></div>', unsafe_allow_html=True)
    
    # Top Competitors - Use businesses from chain_brands which have review data
    if all_businesses:
        st.markdown('<div class="sub-header">🏆 Top 3 Competitors</div>', unsafe_allow_html=True)
        
        # Sort by rating (most rated) and reviews count (most reviewed)
        most_rated = sorted(
            all_businesses,
            key=lambda x: (x.get('rating', 0) or 0, x.get('positive_percentage', 0) or 0),
            reverse=True
        )[:1]
        
        most_reviewed = sorted(
            all_businesses,
            key=lambda x: (x.get('reviews_count', 0) or 0, x.get('rating', 0) or 0),
            reverse=True
        )[:1]
        
        # Combine and deduplicate
        top_competitors = list({b.get('name', ''): b for b in most_rated + most_reviewed}.values())[:2]
        
        for i, business in enumerate(top_competitors, 1):
            with st.expander(f"{i}. {business.get('name', 'Unknown Business')}", expanded=(i == 1)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Rating:** {business.get('rating', 'N/A')}/5.0 ⭐")
                    st.write(f"**Total Reviews:** {business.get('reviews_count', 0):,}")
                    st.write(f"**Reviews Analyzed:** {business.get('reviews_analyzed', business.get('reviews_count', 0))}")
                
                with col2:
                    sentiment_pct = business.get('positive_percentage', 0)
                    st.write(f"**Positive Sentiment:** {sentiment_pct:.1f}% 😊")
                    st.write(f"**Negative Sentiment:** {100-sentiment_pct:.1f}% 😞")
                    st.write(f"**Address:** {business.get('address', 'N/A')}")
                
                # Show top 2 positive reviews
                positive_reviews = business.get('positive_reviews', [])
                if positive_reviews:
                    st.markdown("**Top Positive Reviews:**")
                    for j, review in enumerate(positive_reviews[:2], 1):
                        review_text = review.get('snippet', review.get('text', 'N/A'))
                        st.info(f"{j}. {review_text[:300]}{'...' if len(review_text) > 300 else ''}")
                
                # Show top 2 negative reviews
                negative_reviews = business.get('negative_reviews', [])
                if negative_reviews:
                    st.markdown("**Top Negative Reviews:**")
                    for j, review in enumerate(negative_reviews[:2], 1):
                        review_text = review.get('snippet', review.get('text', 'N/A'))
                        st.warning(f"{j}. {review_text[:300]}{'...' if len(review_text) > 300 else ''}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🏪 Business Location Advisor</div>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Market Analysis for Opening a Business**")
    st.markdown("---")
    
    # Load property data for examples
    property_df = load_property_data()
    
    # Centered input section
    st.markdown('<div class="centered-content">', unsafe_allow_html=True)
    st.markdown("### 🎯 Describe Your Business Idea")
    
    # Example queries
    st.markdown('<div class="example-queries">', unsafe_allow_html=True)
    st.markdown("**Example queries:**")
    st.markdown("- \"I want to open a coffee shop near Noble Aurellia\"")
    st.markdown("- \"Looking to start a sneaker store at Homeland Regalia\"")
    st.markdown("- \"Want to open a pharmacy near Marbella Twin Towers\"")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Business query input in the center
    business_query = st.text_input(
        "Describe your business idea and location:",
        placeholder="e.g., I want to open a coffee shop near Noble Aurellia",
        help="Mention both the business type and property name/area",
        key="business_query"
    )
    
    # Analysis button
    analyze_button = st.button(
        "🚀 Analyze Business Opportunity",
        type="primary",
        width='stretch'
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis section
    if analyze_button and business_query:
        st.markdown('<div class="sub-header">🔄 Running Analysis...</div>', unsafe_allow_html=True)
        
        # Progress placeholder
        progress_placeholder = st.empty()
        result_placeholder = st.empty()
        
        with st.spinner("Understanding your query and analyzing business opportunity..."):
            try:
                # Run analysis with business query
                result = analyze_property(
                    business_query=business_query
                )
                
                # Display results
                with result_placeholder.container():
                    display_analysis_results(result)
                
                st.success("✅ Analysis Complete!")
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                logger.error(f"Analysis error: {e}", exc_info=True)
    
    elif analyze_button and not business_query:
        st.warning("⚠️ Please describe your business idea and location first!")
    
    else:
        st.info("👆 Describe your business idea and location above and click **'Analyze Business Opportunity'** to begin the analysis.")
        
        # Show sample properties
        if not property_df.empty:
            with st.expander("📋 View Sample Properties"):
                display_df = property_df[['project_name', 'brand_name']].head(10)
                st.dataframe(display_df, width='stretch')


if __name__ == "__main__":
    main()