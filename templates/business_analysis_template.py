"""Template for business analysis reports."""

# This template can be used to customize the output format for different business types

DEFAULT_TEMPLATE = """
# {business_type.upper()} OPPORTUNITY ANALYSIS
## Location: {area_name}

### PROPERTY DETAILS
- Property ID: {property_id}
- Coordinates: {latitude}, {longitude}
- Area: {area_name}

### DEMOGRAPHIC PROFILE
{demographics}

### MARKET OVERVIEW
- Competitor Count: {competitor_count}
- Average Rating: {avg_rating}/5.0
- Market Sentiment: {avg_sentiment} (scale: -1 to 1)
- Positive Sentiment: {positive_pct}%
- Negative Sentiment: {negative_pct}%

### RECOMMENDATIONS
#### PROS
{pros}

#### CONS
{cons}

#### SUGGESTIONS
{suggestions}

#### FINAL RECOMMENDATION
{recommendation}

### TOP COMPETITORS
{top_competitors}
"""

CAFE_TEMPLATE = """
# CAFE OPPORTUNITY ANALYSIS
## Location: {area_name}

### PROPERTY DETAILS
- Property ID: {property_id}
- Coordinates: {latitude}, {longitude}
- Area: {area_name}

### DEMOGRAPHIC PROFILE
{demographics}

### MARKET OVERVIEW
- Coffee Shops Count: {competitor_count}
- Average Rating: {avg_rating}/5.0
- Customer Sentiment: {avg_sentiment} (scale: -1 to 1)
- Positive Reviews: {positive_pct}%
- Negative Reviews: {negative_pct}%

### RECOMMENDATIONS
#### OPPORTUNITIES
{pros}

#### CHALLENGES
{cons}

#### BUSINESS STRATEGIES
{suggestions}

#### FINAL VERDICT
{recommendation}

### TOP COFFEE SHOPS
{top_competitors}
"""

SNEAKER_STORE_TEMPLATE = """
# SNEAKER STORE OPPORTUNITY ANALYSIS
## Location: {area_name}

### PROPERTY DETAILS
- Property ID: {property_id}
- Coordinates: {latitude}, {longitude}
- Area: {area_name}

### DEMOGRAPHIC PROFILE
{demographics}

### MARKET OVERVIEW
- Sneaker Stores Count: {competitor_count}
- Average Rating: {avg_rating}/5.0
- Customer Sentiment: {avg_sentiment} (scale: -1 to 1)
- Positive Reviews: {positive_pct}%
- Negative Reviews: {negative_pct}%

### RECOMMENDATIONS
#### MARKET OPPORTUNITIES
{pros}

#### MARKET CHALLENGES
{cons}

#### BUSINESS STRATEGIES
{suggestions}

#### FINAL VERDICT
{recommendation}

### TOP SNEAKER STORES
{top_competitors}
"""