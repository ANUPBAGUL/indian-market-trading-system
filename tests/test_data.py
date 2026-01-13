import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.schema import OHLCVSchema
from src.data_loader import DataLoader

class TestOHLCVSchema:
    def test_get_dtypes(self):
        dtypes = OHLCVSchema.get_dtypes()
        assert dtypes['symbol'] == 'string'
        assert dtypes['open'] == 'float64'
        assert dtypes['volume'] == 'int64'

class TestDataLoader:
    @pytest.fixture
    def sample_data(self):
        return pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'date': ['2024-01-15', '2024-01-15'],
            'open': [185.5, 385.2],
            'high': [187.2, 388.5],
            'low': [184.8, 383.1],
            'close': [186.75, 387.45],
            'volume': [45000000, 28000000],
            'sector': ['Technology', 'Technology']
        })
    
    @pytest.fixture
    def temp_csv(self, sample_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            yield f.name
        os.unlink(f.name)
    
    def test_load_csv(self, temp_csv):
        loader = DataLoader()
        df = loader.load_csv(temp_csv)
        
        assert len(df) == 2
        assert 'symbol' in df.columns
        assert df['symbol'].iloc[0] == 'AAPL'
        assert pd.api.types.is_datetime64_any_dtype(df['date'])
    
    def test_validate_schema_missing_columns(self):
        loader = DataLoader()
        bad_df = pd.DataFrame({'symbol': ['AAPL'], 'date': ['2024-01-15']})
        
        with pytest.raises(ValueError, match="Missing columns"):
            loader._validate_schema(bad_df)