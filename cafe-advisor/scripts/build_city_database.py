"""Build city-wide business database from SerpAPI."""

import pandas as pd
import time
from utils.api_clients import SerpApiClient
from geopy.geocoders import Nominatim

def build_city_database(city_name: str, city_lat: float, city_lon: float, output_path: str = "data/city_businesses.csv"):
    """
    Build a database of all businesses in a city.
    
    Args:
        city_name: Name of the city
        city_lat: City center latitude
        city_lon: City center longitude
        output_path: Where to save the database
    """
    print(f"Building business database for {city_name}...")
    
    serp_client = SerpApiClient()
    geolocator = Nominatim(user_agent="city_db_builder", timeout=5)
    
    all_businesses = []
    
    # Search in a grid pattern to cover the entire city
    # Adjust grid_size based on city size (e.g., 0.05 = ~5km)
    grid_size = 0.05  # degrees
    grid_range = 0.2  # Total area to cover
    
    search_queries = ['cafe', 'restaurant', 'pharmacy', 'retail shop', 'store']
    
    for query in search_queries:
        print(f"\nSearching for: {query}")
        
        for lat_offset in range(-2, 3):  # 5x5 grid
            for lon_offset in range(-2, 3):
                search_lat = city_lat + (lat_offset * grid_size)
                search_lon = city_lon + (lon_offset * grid_size)
                
                print(f"  Grid point ({search_lat:.4f}, {search_lon:.4f})...", end=" ")
                
                try:
                    results = serp_client.search_places(
                        query=query,
                        latitude=search_lat,
                        longitude=search_lon,
                        radius=2500  # 2.5km radius per grid point
                    )
                    
                    if "local_results" in results:
                        for result in results["local_results"]:
                            gps = result.get("gps_coordinates", {})
                            
                            business = {
                                'name': result.get("title", ""),
                                'lat': gps.get("latitude", search_lat),
                                'lon': gps.get("longitude", search_lon),
                                'address': result.get("address", ""),
                                'types': result.get("type", ""),
                                'rating': result.get("rating"),
                                'reviews': result.get("reviews", 0)
                            }
                            
                            all_businesses.append(business)
                        
                        print(f"Found {len(results['local_results'])} businesses")
                    else:
                        print("No results")
                    
                    time.sleep(1)  # Rate limiting
                
                except Exception as e:
                    print(f"Error: {e}")
    
    # Create DataFrame and remove duplicates
    df = pd.DataFrame(all_businesses)
    
    # Remove duplicates based on name and approximate location
    df['lat_rounded'] = df['lat'].round(4)
    df['lon_rounded'] = df['lon'].round(4)
    df = df.drop_duplicates(subset=['name', 'lat_rounded', 'lon_rounded'])
    df = df.drop(columns=['lat_rounded', 'lon_rounded'])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Database created: {len(df)} unique businesses")
    print(f"📁 Saved to: {output_path}")
    
    return df

# Example usage
if __name__ == "__main__":
    # For Chandigarh
    build_city_database(
        city_name="Chandigarh",
        city_lat=30.7333,
        city_lon=76.7794,
        output_path="data/chandigarh_businesses.csv"
    )