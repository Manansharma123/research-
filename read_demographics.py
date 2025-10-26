"""Script to read and display the dummy property variables CSV file."""

import pandas as pd


def read_demographics_data():
    """Read and display the demographics data from CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv('data/dummy_property_variables.csv')
        print("=== DUMMY PROPERTY VARIABLES DATA ===")
        print(f"Total records: {len(df)}")
        print("\nColumn names:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        print("\nFirst 5 rows of data:")
        print(df.head())
        
        print("\nData types:")
        print(df.dtypes)
        
        return df
    except Exception as e:
        print(f"Error reading demographics data: {e}")
        return None


def show_sample_property_analysis():
    """Show how to use demographics data for property analysis."""
    df = read_demographics_data()
    if df is not None:
        print("\n=== SAMPLE ANALYSIS ===")
        print("The system uses these demographic variables for business analysis:")
        
        # Show how the data maps to our system's demographic structure
        sample_row = df.iloc[0]
        print(f"\nSample property demographics:")
        print(f"  Location (Lat-Long): {sample_row['Lat-Long']}")
        print(f"  High Income Households (>10 LPA): {sample_row['Household income above 10 LPA']}")
        print(f"  Working Age Population (18-60 Yrs): {sample_row['Population (18-60 Yrs)']}")
        print(f"  Retail Shops: {sample_row['Total Retail Shops']}")
        print(f"  Affluence Indicator: {sample_row['Affluence Indicator']}")
        print(f"  Footfall Score: {sample_row['Overall Footfall Score']}")


if __name__ == "__main__":
    show_sample_property_analysis()