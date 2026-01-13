"""
Unit tests for DataLoader - Tests data loading and validation functionality.
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from src.data_loader import DataLoader
from src.schema import OHLCVSchema


class TestDataLoader(unittest.TestCase):
    
    def setUp(self):
        """Set up test data and temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DataLoader(data_dir=self.temp_dir)
        
        # Valid test data
        self.valid_data = {
            'symbol': ['AAPL', 'MSFT', 'GOOGL'],
            'date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'open': [150.0, 250.0, 2800.0],
            'high': [155.0, 255.0, 2850.0],
            'low': [148.0, 248.0, 2780.0],
            'close': [152.0, 252.0, 2820.0],
            'volume': [1000000, 800000, 500000]
        }
        
        # Invalid data (missing columns)
        self.invalid_data = {
            'symbol': ['AAPL', 'MSFT'],
            'date': ['2024-01-01', '2024-01-01'],
            'open': [150.0, 250.0],
            'high': [155.0, 255.0]
            # Missing low, close, volume
        }
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test DataLoader initialization."""
        loader = DataLoader("test/path")
        self.assertEqual(loader.data_dir, Path("test/path"))
        
        # Default path
        default_loader = DataLoader()
        self.assertEqual(default_loader.data_dir, Path("data/raw"))
    
    @patch('pandas.read_csv')
    def test_load_csv_valid(self, mock_read_csv):
        """Test loading valid CSV data."""
        # Mock pandas read_csv to return our test data
        mock_df = pd.DataFrame(self.valid_data)
        mock_df['date'] = pd.to_datetime(mock_df['date'])
        mock_read_csv.return_value = mock_df
        
        result = self.loader.load_csv("test.csv")
        
        # Verify pandas.read_csv was called with correct parameters
        mock_read_csv.assert_called_once_with(
            "test.csv",
            dtype=OHLCVSchema.get_dtypes(),
            parse_dates=['date']
        )
        
        # Verify result has all required columns
        required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, result.columns)
    
    @patch('pandas.read_csv')
    def test_load_csv_invalid_schema(self, mock_read_csv):
        """Test loading CSV with invalid schema."""
        # Mock pandas to return invalid data
        mock_df = pd.DataFrame(self.invalid_data)
        mock_df['date'] = pd.to_datetime(mock_df['date'])
        mock_read_csv.return_value = mock_df
        
        with self.assertRaises(ValueError) as context:
            self.loader.load_csv("invalid.csv")
        
        self.assertIn("Missing columns", str(context.exception))
        self.assertIn("low", str(context.exception))
        self.assertIn("close", str(context.exception))
        self.assertIn("volume", str(context.exception))
    
    @patch('pandas.read_parquet')
    def test_load_parquet_valid(self, mock_read_parquet):
        """Test loading valid Parquet data."""
        # Mock pandas read_parquet to return our test data
        mock_df = pd.DataFrame(self.valid_data)
        mock_read_parquet.return_value = mock_df
        
        result = self.loader.load_parquet("test.parquet")
        
        # Verify pandas.read_parquet was called
        mock_read_parquet.assert_called_once_with("test.parquet")
        
        # Verify date column is datetime
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result['date']))
        
        # Verify all required columns exist
        required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, result.columns)
    
    @patch('pandas.read_parquet')
    def test_load_parquet_invalid_schema(self, mock_read_parquet):
        """Test loading Parquet with invalid schema."""
        # Mock pandas to return invalid data
        mock_df = pd.DataFrame(self.invalid_data)
        mock_read_parquet.return_value = mock_df
        
        with self.assertRaises(ValueError) as context:
            self.loader.load_parquet("invalid.parquet")
        
        self.assertIn("Missing columns", str(context.exception))
    
    def test_load_day_csv(self):
        """Test loading data for specific day (CSV format)."""
        with patch.object(self.loader, 'load_csv') as mock_load_csv:
            mock_load_csv.return_value = pd.DataFrame(self.valid_data)
            
            result = self.loader.load_day("2024-01-01", "csv")
            
            expected_path = Path(self.temp_dir) / "2024-01-01.csv"
            mock_load_csv.assert_called_once_with(expected_path)
    
    def test_load_day_parquet(self):
        """Test loading data for specific day (Parquet format)."""
        with patch.object(self.loader, 'load_parquet') as mock_load_parquet:
            mock_load_parquet.return_value = pd.DataFrame(self.valid_data)
            
            result = self.loader.load_day("2024-01-01", "parquet")
            
            expected_path = Path(self.temp_dir) / "2024-01-01.parquet"
            mock_load_parquet.assert_called_once_with(expected_path)
    
    def test_load_day_invalid_format(self):
        """Test loading data with unsupported format."""
        with self.assertRaises(ValueError) as context:
            self.loader.load_day("2024-01-01", "xlsx")
        
        self.assertIn("Unsupported format: xlsx", str(context.exception))
    
    def test_load_day_default_format(self):
        """Test loading data with default CSV format."""
        with patch.object(self.loader, 'load_csv') as mock_load_csv:
            mock_load_csv.return_value = pd.DataFrame(self.valid_data)
            
            result = self.loader.load_day("2024-01-01")  # No format specified
            
            expected_path = Path(self.temp_dir) / "2024-01-01.csv"
            mock_load_csv.assert_called_once_with(expected_path)
    
    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        df = pd.DataFrame(self.valid_data)
        result = self.loader._validate_schema(df)
        
        # Should return the same dataframe
        pd.testing.assert_frame_equal(result, df)
    
    def test_validate_schema_invalid(self):
        """Test schema validation with invalid data."""
        df = pd.DataFrame(self.invalid_data)
        
        with self.assertRaises(ValueError) as context:
            self.loader._validate_schema(df)
        
        error_msg = str(context.exception)
        self.assertIn("Missing columns", error_msg)
        self.assertIn("['low', 'close', 'volume']", error_msg)
    
    def test_validate_schema_extra_columns(self):
        """Test schema validation with extra columns (should pass)."""
        extra_data = self.valid_data.copy()
        extra_data['sector'] = ['Technology', 'Technology', 'Technology']
        extra_data['market_cap'] = [3000000000, 2800000000, 1800000000]
        
        df = pd.DataFrame(extra_data)
        result = self.loader._validate_schema(df)
        
        # Should pass validation and return dataframe with extra columns
        self.assertIn('sector', result.columns)
        self.assertIn('market_cap', result.columns)


if __name__ == '__main__':
    unittest.main()