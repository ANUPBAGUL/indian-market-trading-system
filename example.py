from src.data_loader import DataLoader
import pandas as pd

# Create sample data for demonstration
sample_data = {
    'symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'date': ['2024-01-15', '2024-01-15', '2024-01-15'],
    'open': [185.50, 385.20, 2650.00],
    'high': [187.20, 388.50, 2675.30],
    'low': [184.80, 383.10, 2640.50],
    'close': [186.75, 387.45, 2668.90],
    'volume': [45000000, 28000000, 1200000],
    'sector': ['Technology', 'Technology', 'Technology']
}

# Save sample data
df_sample = pd.DataFrame(sample_data)
df_sample.to_csv('data/raw/2024-01-15.csv', index=False)

# Example usage
if __name__ == "__main__":
    loader = DataLoader()
    
    # Load one trading day
    daily_data = loader.load_day("2024-01-15")
    
    print("Loaded data for 2024-01-15:")
    print(daily_data)
    print(f"\nData types:\n{daily_data.dtypes}")
    print(f"\nShape: {daily_data.shape}")