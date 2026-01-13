# Indian Market Trading System

## Overview

This is a parallel implementation of the trading system specifically adapted for Indian equity markets (NSE/BSE). It handles Indian market conventions, trading hours, data formats, and regulatory requirements.

## Key Adaptations for Indian Markets

### 1. Market Configuration
- **Trading Hours**: 9:15 AM - 3:30 PM IST
- **Currency**: Indian Rupees (INR)
- **Exchanges**: NSE (National Stock Exchange), BSE (Bombay Stock Exchange)
- **Market Holidays**: Indian calendar (Republic Day, Diwali, etc.)

### 2. Risk Parameters (Adjusted for Indian Volatility)
- **Position Risk**: 2.0% per trade (vs 1.5% for US markets)
- **Portfolio Risk**: 8.0% maximum
- **Sector Allocation**: 35% maximum per sector
- **Minimum Confidence**: 60% (slightly relaxed)

### 3. Indian Stock Universe
- **NIFTY 50**: Top 50 stocks by market cap
- **Sector Coverage**: Banking, IT, FMCG, Pharma, Auto, Metals, Energy
- **Price Filters**: ₹10 - ₹10,000 per share
- **Volume Filters**: Minimum 1 lakh shares daily volume

## Quick Start

### 1. Install Dependencies
```bash
pip install yfinance pandas numpy
```

### 2. Run Indian Market Example
```bash
python examples/indian_market_example.py
```

### 3. Load Your Own Data
```python
from src.indian_data_loader import load_indian_stocks

# Load NIFTY 50 stocks
nifty_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
data = load_indian_stocks(
    symbols=nifty_stocks,
    start_date='2024-01-01',
    end_date='2024-03-01',
    exchange='NSE'
)
```

## Indian Market Components

### 1. Data Sources
- **Yahoo Finance**: Uses .NS (NSE) and .BO (BSE) suffixes
- **CSV Files**: Support for local Indian market data
- **Future**: NSE API integration planned

### 2. Sector Classification
```python
# Major Indian sectors covered
SECTORS = {
    'Banking': ['HDFCBANK', 'ICICIBANK', 'SBIN'],
    'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND'],
    'Pharma': ['SUNPHARMA', 'DRREDDY', 'CIPLA'],
    'Auto': ['MARUTI', 'TATAMOTORS', 'M&M'],
    'Energy': ['RELIANCE', 'ONGC', 'IOC']
}
```

### 3. Risk Management (Indian Context)
- **Higher Volatility**: Adjusted for Indian market conditions
- **Sector Limits**: Prevents over-concentration in banking/IT
- **Currency Risk**: All calculations in INR
- **Liquidity Filters**: Ensures tradeable volumes

## Usage Examples

### 1. Basic Indian Stock Analysis
```python
from src.indian_data_loader import IndianDataLoader

loader = IndianDataLoader()
data = loader.load_stock_data(
    symbols=['RELIANCE', 'TCS'],
    start_date='2024-01-01',
    end_date='2024-03-01'
)

print(f"Loaded {len(data)} records")
print(data.groupby('sector')['symbol'].nunique())
```

### 2. NIFTY 50 Backtest
```python
from src.indian_market_config import INDIAN_MARKET_CONFIG
from src.backtest_engine import BacktestEngine

# Initialize with Indian parameters
backtester = BacktestEngine(initial_capital=500000)  # ₹5 Lakhs

# Run backtest with Indian stocks
results = backtester.run(indian_data, signal_generator, governor)
```

### 3. Sector Analysis
```python
from src.indian_market_config import IndianSectorMapper

mapper = IndianSectorMapper()

# Get all banking stocks
banking_stocks = mapper.get_sector_stocks('Banking')
print(f"Banking stocks: {banking_stocks}")

# Get sector for a stock
sector = mapper.get_sector('RELIANCE')
print(f"RELIANCE sector: {sector}")
```

## Indian Market Considerations

### 1. Regulatory Environment
- **SEBI Regulations**: Securities and Exchange Board of India
- **Circuit Breakers**: 5%, 10%, 20% price limits
- **Settlement**: T+2 settlement cycle
- **Margin Requirements**: Higher margins for volatile stocks

### 2. Market Microstructure
- **Lot Sizes**: Vary by stock (usually 1 share minimum)
- **Tick Sizes**: ₹0.05 for stocks above ₹10
- **Market Orders**: Available during trading hours
- **After Hours**: Limited pre/post market trading

### 3. Tax Implications
- **STCG**: Short-term capital gains (15% for equity)
- **LTCG**: Long-term capital gains (10% above ₹1 lakh)
- **STT**: Securities Transaction Tax on all trades
- **Dividend Tax**: TDS on dividend income

## Performance Targets (Indian Markets)

### Minimum Viable System
- **Expectancy**: > ₹0 per trade
- **Max Drawdown**: < 18% (higher than US due to volatility)
- **Signal Conversion**: > 35%
- **Signal Accuracy**: > 40%

### Optimized System
- **Expectancy**: > ₹2,000 per trade
- **Max Drawdown**: < 12%
- **Signal Conversion**: > 55%
- **Signal Accuracy**: > 50%

## Common Indian Market Patterns

### 1. Sector Rotation
- **Banking**: Interest rate sensitive
- **IT**: Dollar strength dependent
- **FMCG**: Monsoon and rural demand
- **Auto**: Festival seasons and policy changes

### 2. Market Timing
- **Budget Season**: February impact on sectors
- **Monsoon**: June-September agricultural impact
- **Festival Season**: October-November consumption
- **Results Season**: Quarterly earnings impact

### 3. Global Factors
- **FII Flows**: Foreign institutional investor sentiment
- **Crude Oil**: Major import, affects currency
- **Dollar Strength**: IT sector correlation
- **Global Risk**: Safe haven flows

## Troubleshooting

### 1. Data Issues
```python
# Check if symbol exists
from src.indian_market_config import IndianSectorMapper
sector = IndianSectorMapper.get_sector('SYMBOL')
if sector == 'Others':
    print("Symbol not in mapping, add to SECTOR_MAPPING")
```

### 2. No Signals Generated
- Lower confidence threshold (try 55%)
- Check volume filters (reduce min_daily_volume)
- Verify data quality and date ranges
- Review sector allocation limits

### 3. High Rejection Rates
- Increase position limits in Governor
- Adjust sector concentration limits
- Review cash management settings
- Check confidence calibration

## Next Steps

1. **Expand Universe**: Add mid-cap and small-cap stocks
2. **Regime Detection**: Implement bull/bear market detection
3. **Sector Strategies**: Develop sector-specific agents
4. **Options Integration**: Add derivatives for hedging
5. **Real-time Data**: Integrate live NSE feeds
6. **Compliance**: Add SEBI regulatory checks

## Support

For Indian market specific questions:
- Review `indian_market_config.py` for parameters
- Check `indian_data_loader.py` for data issues
- Run `examples/indian_market_example.py` for testing

The system is designed to adapt to Indian market conditions while maintaining the same rigorous risk management and systematic approach as the US version.