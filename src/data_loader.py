import pandas as pd
from pathlib import Path
from typing import Union
from .schema import OHLCVSchema

class DataLoader:
    """Minimal data loader for OHLCV data"""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
    
    def load_csv(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load OHLCV data from CSV"""
        df = pd.read_csv(
            filepath,
            dtype=OHLCVSchema.get_dtypes(),
            parse_dates=['date']
        )
        return self._validate_schema(df)
    
    def load_parquet(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load OHLCV data from Parquet"""
        df = pd.read_parquet(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return self._validate_schema(df)
    
    def load_day(self, date: str, file_format: str = "csv") -> pd.DataFrame:
        """Load all stocks for a specific trading day"""
        filename = f"{date}.{file_format}"
        filepath = self.data_dir / filename
        
        if file_format == "csv":
            return self.load_csv(filepath)
        elif file_format == "parquet":
            return self.load_parquet(filepath)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    def _validate_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure required columns exist"""
        required = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        return df