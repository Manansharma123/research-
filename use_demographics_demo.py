"""Demo script showing how to use demographics data with the Business Advisor system."""

import pandas as pd
from main import analyze_property


def load_demographics_data():
    """Load demographics data from CSV file."""
    try:
        df = pd.read_csv('data/dummy_property_variables.csv')
        print(f"Loaded {len(df)} property records with demographics data")
        return df
    except Exception as e:
        print(f"Error loading demographics data: {e}")
        return None


def map_demographics_to_system_format(demographics_row):
    """
    Map demographics data from CSV format to our system's format.
    
    Our system expects:
    {
        "population": int,
        "working_population": int,
        "income_level": int,
        "retail_shops": int,
        "foot_traffic": int
    }
    """
    # Extract coordinates from the Lat-Long field
    lat_long_str = demographics_row['Lat-Long']
    try:
        # Parse the coordinate string
        coords = lat_long_str.replace('"', '').strip()
        if ',' in coords:
            lat, lon = coords.split(',')
            latitude = float(lat.strip())
            longitude = float(lon.strip())
        else:
            # Fallback if format is unexpected
            latitude, longitude = 0.0, 0.0
    except:
        latitude, longitude = 0.0, 0.0
    
    # Map demographics to our system format
    demographics = {
        "population": (
            int(demographics_row.get('Population (0-18 Yrs)', 0)) +
            int(demographics_row.get('Population (18-60 Yrs)', 0)) +
            int(demographics_row.get('Population (Above 60 Yrs)', 0))
        ),
        "working_population": int(demographics_row.get('Population (18-60 Yrs)', 0)),
        "income_level": int(demographics_row.get('Household income above 10 LPA', 0)),
        "retail_shops": int(demographics_row.get('Total Retail Shops', 0)),
        "foot_traffic": int(demographics_row.get('Overall Footfall Score', 0))
    }
    
    return latitude, longitude, demographics


def demo_with_demographics():
    """Demo using actual demographics data."""
    print("=== BUSINESS ADVISOR WITH DEMOGRAPHICS DATA ===\n")
    
    # Load demographics data
    df = load_demographics_data()
    if df is None:
        return
    
    # Show first few records
    print("First 3 property records:")
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        lat, lon, demographics = map_demographics_to_system_format(row)
        print(f"\nProperty {i+1}:")
        print(f"  Coordinates: {lat}, {lon}")
        print(f"  Population: {demographics['population']:,}")
        print(f"  Working Population: {demographics['working_population']:,}")
        print(f"  High Income Households: {demographics['income_level']:,}")
        print(f"  Retail Shops: {demographics['retail_shops']}")
        print(f"  Foot Traffic Score: {demographics['foot_traffic']}")
    
    # Example analysis using the first property record
    print("\n" + "="*60)
    print("RUNNING BUSINESS ANALYSIS WITH DEMOGRAPHICS DATA")
    print("="*60)
    
    # For this demo, we'll use the system's built-in data loading
    # which automatically creates sample data if needed
    print("\nAnalyzing property for different business types:")
    
    business_types = ["cafe", "sneaker_store", "restaurant"]
    
    for business_type in business_types:
        print(f"\n--- {business_type.upper()} ANALYSIS ---")
        try:
            result = analyze_property(property_index=0, business_type=business_type)
            
            if "error" in result and result["error"]:
                print(f"Error: {result['error']}")
            else:
                # Print key information
                print(f"Area: {result.get('area_name', 'N/A')}")
                recommendation = result.get('llm_recommendation', {})
                if recommendation:
                    print(f"Recommendation: {recommendation.get('recommendation', 'N/A')}")
                    print("Key Factors Considered:")
                    print(f"  - Population: {result.get('demographic_data', {}).get('population', 0):,}")
                    print(f"  - Working Population: {result.get('demographic_data', {}).get('working_population', 0):,}")
                    print(f"  - Income Level: {result.get('demographic_data', {}).get('income_level', 0):,}")
                    print(f"  - Retail Shops: {result.get('demographic_data', {}).get('retail_shops', 0)}")
                    print(f"  - Foot Traffic: {result.get('demographic_data', {}).get('foot_traffic', 0)}")
        except Exception as e:
            print(f"Error analyzing {business_type}: {e}")


def show_demographics_mapping():
    """Show how demographics data maps to business analysis factors."""
    print("\n=== DEMOGRAPHICS DATA MAPPING ===")
    print("Our system uses demographics to inform business recommendations:")
    print("\nInput CSV Columns → System Analysis Factors")
    print("  Population (0-18 Yrs) + (18-60 Yrs) + (Above 60 Yrs) → population")
    print("  Population (18-60 Yrs) → working_population")
    print("  Household income above 10 LPA → income_level")
    print("  Total Retail Shops → retail_shops")
    print("  Overall Footfall Score → foot_traffic")
    print("\nThese factors help determine:")
    print("  - Market size and potential customer base")
    print("  - Purchasing power of the local population")
    print("  - Competition level from existing retail")
    print("  - Potential foot traffic for physical businesses")


if __name__ == "__main__":
    demo_with_demographics()
    show_demographics_mapping()
    print("\n" + "="*60)
    print("DEMO COMPLETED - The system effectively uses demographics data!")
    print("="*60)