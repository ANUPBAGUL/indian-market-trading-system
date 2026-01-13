"""
Integration tests for DataLoader - Tests complete data loading workflows.
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.data_loader import DataLoader


class TestDataLoaderIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with real files."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DataLoader(data_dir=self.temp_dir)
        
        # Create realistic test data
        self.test_data = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'] * 2,
            'date': ['2024-01-01'] * 5 + ['2024-01-02'] * 5,
            'open': [150.0, 250.0, 2800.0, 200.0, 3200.0, 152.0, 252.0, 2820.0, 205.0, 3250.0],
            'high': [155.0, 255.0, 2850.0, 210.0, 3280.0, 157.0, 257.0, 2870.0, 215.0, 3300.0],
            'low': [148.0, 248.0, 2780.0, 195.0, 3180.0, 150.0, 250.0, 2800.0, 200.0, 3220.0],
            'close': [152.0, 252.0, 2820.0, 205.0, 3250.0, 154.0, 254.0, 2840.0, 210.0, 3280.0],
            'volume': [1000000, 800000, 500000, 1200000, 600000, 1100000, 850000, 520000, 1300000, 620000],
            'sector': ['Technology'] * 10,
            'market_cap': [3000000000] * 10
        })
        
        # Create test files
        self.csv_file = Path(self.temp_dir) / "2024-01-01.csv"
        self.parquet_file = Path(self.temp_dir) / "2024-01-01.parquet"
        
        # Save test data to files
        day1_data = self.test_data[self.test_data['date'] == '2024-01-01']
        day1_data.to_csv(self.csv_file, index=False)
        day1_data.to_parquet(self.parquet_file, index=False)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_csv_real_file(self):
        """Test loading actual CSV file."""
        result = self.loader.load_csv(self.csv_file)
        
        # Verify data integrity
        self.assertEqual(len(result), 5)  # 5 stocks for one day
        self.assertEqual(list(result['symbol']), ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'])
        
        # Verify data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result['date']))
        self.assertTrue(pd.api.types.is_float_dtype(result['open']))
        self.assertTrue(pd.api.types.is_integer_dtype(result['volume']))
        
        # Verify all required columns exist
        required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, result.columns)
        
        # Verify optional columns are preserved
        self.assertIn('sector', result.columns)
        self.assertIn('market_cap', result.columns)
    
    def test_load_parquet_real_file(self):
        """Test loading actual Parquet file."""
        result = self.loader.load_parquet(self.parquet_file)
        
        # Verify data integrity
        self.assertEqual(len(result), 5)
        self.assertEqual(list(result['symbol']), ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'])
        
        # Verify data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result['date']))
        
        # Verify OHLCV data is numeric
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_load_day_workflow(self):
        """Test complete daily data loading workflow."""
        # Load CSV format
        csv_result = self.loader.load_day("2024-01-01", "csv")
        self.assertEqual(len(csv_result), 5)
        
        # Load Parquet format
        parquet_result = self.loader.load_day("2024-01-01", "parquet")
        self.assertEqual(len(parquet_result), 5)
        
        # Results should be equivalent (ignoring minor type differences)
        self.assertEqual(list(csv_result['symbol']), list(parquet_result['symbol']))
        
        # Verify price data is consistent
        pd.testing.assert_series_equal(
            csv_result['close'].astype(float), 
            parquet_result['close'].astype(float),
            check_names=False
        )
    
    def test_file_not_found_handling(self):
        """Test handling of missing files."""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_csv("nonexistent.csv")
        
        with self.assertRaises(FileNotFoundError):
            self.loader.load_parquet("nonexistent.parquet")
        
        with self.assertRaises(FileNotFoundError):
            self.loader.load_day("2099-12-31", "csv")
    
    def test_corrupted_csv_handling(self):
        """Test handling of corrupted CSV files."""
        # Create corrupted CSV file
        corrupted_file = Path(self.temp_dir) / "corrupted.csv"
        with open(corrupted_file, 'w') as f:
            f.write("invalid,csv,data\n1,2")
        
        # Should raise an error during loading or validation
        with self.assertRaises((pd.errors.ParserError, ValueError)):
            self.loader.load_csv(corrupted_file)
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        # Create empty CSV file
        empty_file = Path(self.temp_dir) / "empty.csv"
        empty_file.touch()
        
        with self.assertRaises((pd.errors.EmptyDataError, ValueError)):
            self.loader.load_csv(empty_file)
    
    def test_large_dataset_loading(self):
        """Test loading larger datasets for performance validation."""
        # Create larger test dataset
        large_data = []
        symbols = [f"STOCK{i:04d}" for i in range(100)]  # 100 stocks
        
        for symbol in symbols:
            large_data.append({
                'symbol': symbol,
                'date': '2024-01-01',
                'open': 100.0 + (hash(symbol) % 100),
                'high': 105.0 + (hash(symbol) % 100),
                'low': 95.0 + (hash(symbol) % 100),
                'close': 102.0 + (hash(symbol) % 100),
                'volume': 1000000 + (hash(symbol) % 1000000)
            })
        
        large_df = pd.DataFrame(large_data)
        large_file = Path(self.temp_dir) / "large_dataset.csv"
        large_df.to_csv(large_file, index=False)
        
        # Load and verify
        result = self.loader.load_csv(large_file)
        self.assertEqual(len(result), 100)
        self.assertEqual(len(result['symbol'].unique()), 100)
    
    def test_data_type_consistency(self):
        """Test that data types are consistent across different loading methods."""
        csv_data = self.loader.load_csv(self.csv_file)
        parquet_data = self.loader.load_parquet(self.parquet_file)
        
        # Both should have datetime dates
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(csv_data['date']))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(parquet_data['date']))
        
        # Both should have numeric OHLCV data
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(csv_data[col]))
            self.assertTrue(pd.api.types.is_numeric_dtype(parquet_data[col]))
    
    def test_schema_validation_integration(self):
        """Test schema validation with real data scenarios."""
        # Create file with missing required column
        invalid_data = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'date': ['2024-01-01', '2024-01-01'],
            'open': [150.0, 250.0],
            'high': [155.0, 255.0]
            # Missing low, close, volume
        })
        
        invalid_file = Path(self.temp_dir) / "invalid.csv"
        invalid_data.to_csv(invalid_file, index=False)
        
        with self.assertRaises(ValueError) as context:
            self.loader.load_csv(invalid_file)
        
        self.assertIn("Missing columns", str(context.exception))
    
    def test_multiple_day_loading_workflow(self):
        """Test loading multiple days of data."""
        # Create data for multiple days
        day2_data = self.test_data[self.test_data['date'] == '2024-01-02']
        day2_file = Path(self.temp_dir) / "2024-01-02.csv"
        day2_data.to_csv(day2_file, index=False)
        
        # Load both days
        day1_result = self.loader.load_day("2024-01-01")
        day2_result = self.loader.load_day("2024-01-02")
        
        # Verify both loaded correctly
        self.assertEqual(len(day1_result), 5)
        self.assertEqual(len(day2_result), 5)
        
        # Verify dates are correct
        self.assertTrue(all(day1_result['date'] == pd.Timestamp('2024-01-01')))
        self.assertTrue(all(day2_result['date'] == pd.Timestamp('2024-01-02')))
        
        # Verify same symbols in both days
        self.assertEqual(
            set(day1_result['symbol']), 
            set(day2_result['symbol'])
        )


if __name__ == '__main__':
    unittest.main()