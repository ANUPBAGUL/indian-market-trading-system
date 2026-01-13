# How to Run Indian and US Trading Systems

## ✅ READY TO USE - Both Systems Working!

### 🚀 Quick Start (Choose One)

#### Option 1: Interactive Menu (Recommended)
```bash
python run_trading.py
```
**What it does:**
- Shows menu to choose US Markets, Indian Markets, or Both
- Handles everything automatically
- User-friendly interface

#### Option 2: Direct Execution

**Run US Market Trading:**
```bash
python run_us_trading.py
```

**Run Indian Market Trading:**
```bash
python run_indian_trading.py
```

#### Option 3: Test Both Systems
```bash
python test_runners.py
```

## 📊 What Each System Does

### 🇺🇸 US Market System
- **Market**: NASDAQ/NYSE stocks
- **Currency**: USD ($)
- **Hours**: 9:30 AM - 4:00 PM EST
- **Risk**: 1.5% per trade
- **Output**: US stock signals and analysis

### 🇮🇳 Indian Market System  
- **Market**: NSE/BSE stocks (NIFTY 50 focus)
- **Currency**: INR (Rs.)
- **Hours**: 9:15 AM - 3:30 PM IST  
- **Risk**: 2.0% per trade (higher volatility)
- **Output**: Indian stock signals and analysis

## 📋 Daily Usage Workflow

### Morning (Before Market Open)
1. **Choose your market** based on your trading focus
2. **Run the system**: `python run_trading.py`
3. **Review signals**: Check generated recommendations
4. **Plan trades**: Note approved entries and position sizes

### During Market Hours
- **Execute trades** exactly as system recommends
- **No discretion** - follow system decisions
- **Monitor positions** for stop loss triggers

### Evening (After Market Close)
- **Log outcomes**: Record actual fills and exits
- **Review performance**: Check expectancy and win rates
- **Plan tomorrow**: Note any system observations

## 🔧 System Status

**✅ US Market System**: Working
- Connects to existing paper trading engine
- Processes US market data
- Generates USD-based signals

**✅ Indian Market System**: Working  
- Uses Indian market configuration
- Processes NSE/BSE data (sample data included)
- Generates INR-based signals
- Includes 10 major Indian stocks

**✅ Signal Quality KPI**: Active
- Tracks conversion rates
- Measures signal accuracy
- Analyzes rejection reasons

## 🎯 Expected Outputs

### Successful Run
```
=== INDIAN MARKET TRADING SYSTEM ===
Market: NSE/BSE
Currency: INR (Indian Rupees)

=== RESULTS ===
Total Trades: 3
Expectancy: Rs.1,250 per trade
Win Rate: 66.7%

Recent Signals:
  RELIANCE: EXECUTED (High confidence)
  TCS: REJECTED (Low volume)
```

### No Signals Day
```
No trades generated today.
This is normal - the system trades selectively.
```

## ⚙️ Configuration

### Default Settings Work Out of Box
- **US Markets**: 62% confidence threshold
- **Indian Markets**: 60% confidence threshold  
- **Risk Management**: Automatic position sizing
- **Stop Losses**: Volatility-based (5-8%)

### To Modify Settings
- **US Settings**: Edit `src/governor.py`
- **Indian Settings**: Edit `src/indian_market_config.py`

## 🚨 Troubleshooting

### "No signals generated"
- **Normal behavior** - system is selective
- Try lowering confidence thresholds if needed
- Check that data is loading correctly

### Import errors
- Run from main project directory
- Ensure all files are in correct locations
- Check Python path settings

### Data issues
- **US Markets**: May need `pip install yfinance` for live data
- **Indian Markets**: Uses sample data by default
- Both systems work with included sample data

## 🎉 You're Ready to Trade!

Both US and Indian market systems are fully functional and tested. Start with the interactive menu (`python run_trading.py`) to explore both markets and see which fits your trading style.

**Remember**: The system is designed to trade selectively. Many days will have no signals - this is a feature, not a bug!