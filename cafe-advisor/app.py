"""Flask API server for Business Advisor - replicates Streamlit functionality."""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import analyze_property

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    API endpoint to analyze property for business opportunities.
    
    Request JSON:
    {
        "query": "cafe in Emporio Mohali"
    }
    
    Response JSON:
    {
        "success": true,
        "data": {
            "business_type": "cafe",
            "property_name": "Emporio Mohali",
            "area_name": "...",
            "coordinates": {...},
            "nearby_businesses": [...],
            "reviews_data": [...],
            "sentiment_analysis": {...},
            "chain_brands": [...],
            "nearby_amenities": {...},
            "llm_recommendation": {...},
            "scraped_data": [...],
            "final_report": "..."
        },
        "error": null
    }
    """
    try:
        # Get query from request
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'data': None,
                'error': 'Query is required'
            }), 400
        
        logger.info(f"Received analysis request: {query}")
        
        # Run analysis
        result = analyze_property(query)
        
        # Check if analysis was successful
        if result.get('error'):
            return jsonify({
                'success': False,
                'data': None,
                'error': result['error']
            }), 500
        
        # Add final_report field from recommendation or formatted_output
        if 'final_report' not in result:
            # Try to get from recommendation field
            if result.get('recommendation'):
                result['final_report'] = result['recommendation']
            # Or create from formatted_output
            elif result.get('formatted_output'):
                formatted = result['formatted_output']
                report_lines = []
                report_lines.append("📊 BUSINESS ANALYSIS REPORT")
                report_lines.append("=" * 60)
                report_lines.append(f"\nBusiness Type: {result.get('business_type', 'N/A')}")
                report_lines.append(f"Location: {result.get('area_name', 'N/A')}")
                
                if formatted.get('market_overview'):
                    mo = formatted['market_overview']
                    report_lines.append(f"\n📈 Market Overview:")
                    report_lines.append(f"  - Competitors: {mo.get('competitor_count', 0)}")
                    report_lines.append(f"  - Average Rating: {mo.get('average_rating', 0)}/5.0")
                    report_lines.append(f"  - Positive Sentiment: {mo.get('positive_sentiment_percentage', 0)}%")
                
                if formatted.get('recommendations'):
                    rec = formatted['recommendations']
                    if rec.get('pros'):
                        report_lines.append(f"\n✅ Pros:")
                        for pro in rec['pros'][:3]:
                            report_lines.append(f"  • {pro}")
                    if rec.get('cons'):
                        report_lines.append(f"\n❌ Cons:")
                        for con in rec['cons'][:3]:
                            report_lines.append(f"  • {con}")
                
                report_lines.append("\n" + "=" * 60)
                result['final_report'] = "\n".join(report_lines)
            else:
                result['final_report'] = "Analysis complete. Please review the sections above for detailed insights."
        
        # Return successful response
        return jsonify({
            'success': True,
            'data': result,
            'error': None
        })
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'data': None,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Business Advisor API'
    })

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Run Flask app
    logger.info("Starting Flask API server on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)
