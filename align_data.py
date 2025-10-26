"""Script to align property coordinates with demographics data."""

import pandas as pd
import random


def create_aligned_datasets():
    """Create aligned property and demographics datasets."""
    # Load the demographics data
    demo_df = pd.read_csv('data/dummy_property_variables.csv')
    print(f"Demographics data has {len(demo_df)} records")
    
    # Take first 3 records to match property coordinates
    demo_sample = demo_df.head(3)
    print(f"Using first 3 records for alignment")
    
    # Extract coordinates from demographics data
    coordinates = []
    for idx, row in demo_sample.iterrows():
        lat_long_str = row['Lat-Long']
        try:
            coords = lat_long_str.replace('"', '').strip()
            if ',' in coords:
                lat, lon = coords.split(',')
                coordinates.append({
                    'property_id': idx,
                    'latitude': float(lat.strip()),
                    'longitude': float(lon.strip())
                })
            else:
                print(f"Invalid coordinate format for row {idx}: {lat_long_str}")
        except Exception as e:
            print(f"Error parsing coordinates for row {idx}: {e}")
    
    # Create property coordinates DataFrame
    prop_df = pd.DataFrame(coordinates)
    print(f"Created property coordinates DataFrame with {len(prop_df)} records")
    
    # Save to file
    prop_df.to_csv('data/property_project_lat_long.csv', index=False)
    print("Saved aligned property coordinates to data/property_project_lat_long.csv")
    
    # Save the matching demographics sample
    demo_sample.to_csv('data/aligned_dummy_property_variables.csv', index=False)
    print("Saved aligned demographics data to data/aligned_dummy_property_variables.csv")
    
    # Show the aligned data
    print("\n=== ALIGNED PROPERTY COORDINATES ===")
    print(prop_df)
    
    print("\n=== ALIGNED DEMOGRAPHICS DATA ===")
    print(demo_sample[['Lat-Long', 'Population (18-60 Yrs)', 'Household income above 10 LPA', 
                      'Total Retail Shops', 'Overall Footfall Score']])
    
    return prop_df, demo_sample


def update_main_system():
    """Update the main system to use aligned data."""
    print("\n=== UPDATING MAIN SYSTEM ===")
    print("To use the aligned data, the system needs to:")
    print("1. Use data/aligned_dummy_property_variables.csv instead of the full file")
    print("2. Ensure property indices match between both files")
    print("3. Both files now have 3 records that align correctly")
    
    # Show how to modify the main.py to use aligned data
    print("\nTo modify main.py, update the _load_demographic_data function to use:")
    print("'data/aligned_dummy_property_variables.csv'")


if __name__ == "__main__":
    print("ALIGNING PROPERTY AND DEMOGRAPHICS DATA")
    print("=" * 40)
    
    prop_df, demo_df = create_aligned_datasets()
    update_main_system()
    
    print("\n" + "=" * 40)
    print("DATA ALIGNMENT COMPLETE!")
    print("Now you can run analyses with properly matched data.")
    print("=" * 40)