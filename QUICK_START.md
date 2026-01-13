# Quick Start Guide - Running Trading Systems

## How to Run Indian and US Trading Systems

### Option 1: Interactive Menu (Recommended)
```bash
python run_trading.py
```
- Choose between US Markets, Indian Markets, or Both
- Interactive menu with clear options
- Handles errors gracefully

### Option 2: Direct Execution

#### Run US Market Trading
```bash
python run_us_trading.py
```
- Executes US market analysis (NASDAQ/NYSE)
- Currency: USD
- Trading hours: 9:30 AM - 4:00 PM EST

#### Run Indian Market Trading
```bash
python run_indian_trading.py
```
- Executes Indian market analysis (NSE/BSE)
- Currency: INR (Indian Rupees)
- Trading hours: 9:15 AM - 3:30 PM IST

### Option 3: Example Scripts

#### US Market Examples
```bash
# Paper trading with US stocks
python examples/paper_trading_example.py

# Decision logging for US markets
python examples/decision_logging_example.py

# Walk-forward testing
python examples/walk_forward_example.py
```

#### Indian Market Examples
```bash
# Indian market demo with sample data
python examples/indian_market_demo.py

# Signal quality analysis
python examples/signal_quality_example.py
```

## System Outputs

### US Market System
- **Signals**: Entry/exit recommendations for US stocks
- **Currency**: All amounts in USD
- **Stocks**: NASDAQ/NYSE listed companies
- **Risk**: 1.5% position risk per trade

### Indian Market System
- **Signals**: Entry/exit recommendations for Indian stocks
- **Currency**: All amounts in INR (Rs.)
- **Stocks**: NSE/BSE listed companies (NIFTY 50 focus)
- **Risk**: 2.0% position risk per trade (higher volatility)

## Key Differences

| Feature | US Markets | Indian Markets |
|---------|------------|----------------|
| **Currency** | USD ($) | INR (Rs.) |
| **Exchanges** | NASDAQ/NYSE | NSE/BSE |
| **Trading Hours** | 9:30 AM - 4:00 PM EST | 9:15 AM - 3:30 PM IST |
| **Position Risk** | 1.5% per trade | 2.0% per trade |
| **Stop Loss** | 5-8% typical | 8% typical (wider) |
| **Data Source** | Yahoo Finance (.com) | Yahoo Finance (.NS/.BO) |

## Daily Workflow

### Morning Routine
1. **Choose Market**: US or Indian based on your focus
2. **Run System**: Execute the appropriate script
3. **Review Signals**: Check generated recommendations
4. **Execute Trades**: Follow system decisions exactly

### Evening Review
1. **Check Results**: Review trade outcomes
2. **Update Logs**: Record actual fills and exits
3. **Monitor KPIs**: Track expectancy and win rates
4. **Plan Tomorrow**: Note any system observations

## Troubleshooting

### No Signals Generated
- **Normal Behavior**: System trades selectively
- **US Markets**: Try lowering confidence threshold to 60%
- **Indian Markets**: Try lowering confidence threshold to 55%

### Data Issues
- **US Markets**: Check internet connection for Yahoo Finance
- **Indian Markets**: System uses sample data by default
- **Real Data**: Install yfinance: `pip install yfinance`

### System Errors
- **Import Errors**: Check that all files are in correct directories
- **Path Issues**: Run from main project directory
- **Dependencies**: Ensure pandas, numpy are installed

## Configuration

### US Market Settings
```python
# Default settings in src/governor.py
MIN_CONFIDENCE = 62.0
MAX_POSITION_RISK = 1.5
CURRENCY = "USD"
```

### Indian Market Settings
```python
# Settings in src/indian_market_config.py
MIN_CONFIDENCE = 60.0
MAX_POSITION_RISK = 2.0
CURRENCY = "INR"
```

## Next Steps

1. **Start with Paper Trading**: Use demo mode first
2. **Monitor Performance**: Track KPIs over time
3. **Gradual Deployment**: Start with small position sizes
4. **System Tuning**: Adjust thresholds based on results

## Support

- **Test System**: Run `python tests/test_new_functionality.py`
- **Check Examples**: All examples in `examples/` directory
- **Documentation**: See README.md files for detailed info