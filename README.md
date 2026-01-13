# 🇮🇳 Indian Market Trading System

**Intelligent Swing Trading System for NSE/BSE Markets**

## 🚀 Quick Start (5 Minutes)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run paper trading (Indian market hours)
python examples/paper_trading_example.py

# 3. Backtest with Indian market data
python examples/decision_logging_example.py

# 4. Validate system performance
python examples/walk_forward_example.py
```

## 🏛️ System Architecture

### Core Components
- **Agents**: Generate probabilistic signals adapted for Indian market volatility
- **ConfidenceEngine**: Combines agent scores with Indian market conditions
- **Governor**: Risk management with INR position sizing
- **BacktestEngine**: Realistic simulation with Indian market timings
- **KPIComputer**: Performance analysis including rupee-based metrics

### Data Flow
```
NSE/BSE Data → Indian Market Agents → ConfidenceEngine → Governor → INR Execution → Rupee KPIs
```

## 🎯 Indian Market Adaptations

### Market Timing
- **Trading Hours**: 9:15 AM - 3:30 PM IST
- **Pre-market**: 9:00 AM - 9:15 AM IST
- **After-hours**: 3:40 PM - 4:00 PM IST
- **Signal Generation**: After 3:30 PM daily

### Currency & Position Sizing
- **Base Currency**: INR (Indian Rupees)
- **Minimum Position**: ₹10,000
- **Risk per Trade**: 1-2% of portfolio in INR
- **Sector Limits**: Max 40% per sector (IT, Banking, Pharma, etc.)

### Indian Market Features
- **Circuit Breakers**: 5%, 10%, 20% limits
- **Delivery vs Intraday**: System focuses on delivery trades
- **T+2 Settlement**: Incorporated in position sizing
- **STT/Brokerage**: Indian tax structure considered

### Supported Exchanges
- **NSE**: National Stock Exchange (primary)
- **BSE**: Bombay Stock Exchange (secondary)
- **Indices**: NIFTY 50, SENSEX, NIFTY 500

### Indian Sectors Supported
- **Banking & Financial Services**: HDFC, ICICI, SBI, Kotak
- **Information Technology**: TCS, Infosys, Wipro, HCL Tech
- **Pharmaceuticals**: Sun Pharma, Dr. Reddy's, Cipla
- **FMCG**: HUL, ITC, Nestle, Britannia
- **Automobiles**: Maruti, Tata Motors, M&M, Bajaj Auto
- **Metals & Mining**: Tata Steel, JSW, Hindalco
- **Energy & Power**: Reliance, ONGC, NTPC, Power Grid
- **Telecom**: Bharti Airtel, Jio (RIL)

## 🔧 Key Files to Master

### 1. Agent System (`src/`)
```python
# AccumulationAgent - FII/DII detection
accumulation_agent.py  # Volume/price accumulation for Indian stocks

# TriggerAgent - Breakout timing (Indian market volatility)
trigger_agent.py       # Price breakouts, volume spikes, momentum

# ConfidenceEngine - INR weighted scoring
confidence_engine.py   # Combines agent outputs, 62% threshold
```

### 2. Risk Management (`src/`)
```python
# Governor - Indian market risk rules
governor.py           # Position limits, confidence gates, sector rules

# PositionSizer - INR Kelly-based sizing
position_sizer.py     # Risk-adjusted position sizing in rupees
```

### 3. Execution & Analysis (`src/`)
```python
# BacktestEngine - Indian market simulation
backtest_engine.py    # Next-open fills, stop execution, trade logging

# KPIComputer - INR performance metrics
kpi_computer.py       # Expectancy in rupees, drawdown, Signal Quality
```

## 🎯 Critical Concepts for Indian Markets

### 1. No Lookahead Bias
- All calculations use only historical NSE/BSE data
- Signals generated on day T, executed at open of T+1
- Stop losses checked using intraday lows

### 2. Indian Market Volatility
- Higher volatility than US markets requires adjusted thresholds
- FII/DII flow impact considered
- Currency fluctuation impact on IT/Pharma sectors

### 3. Signal Quality KPI (INR-based)
```python
# Track signal effectiveness in rupees
conversion_rate = executed_signals / total_signals
signal_accuracy = profitable_trades / executed_signals
rupee_expectancy = avg_profit_per_trade_inr
```

## 📊 Performance Targets (INR)

### Minimum Viable System
- **Expectancy**: > ₹500 per trade
- **Max Drawdown**: < 15%
- **Signal Conversion**: > 40%
- **Signal Accuracy**: > 45%

### Optimized System
- **Expectancy**: > ₹5,000 per trade
- **Max Drawdown**: < 10%
- **Signal Conversion**: > 60%
- **Signal Accuracy**: > 55%

## 🕰️ Indian Market Schedule

### Daily Routine
- **3:30 PM**: Market close, data collection
- **4:00 PM**: Run system analysis
- **6:00 PM**: Review signals and decisions
- **9:00 AM**: Pre-market preparation
- **9:15 AM**: Market open, execute trades

### Key Dates
- **Quarterly Results**: Mar, Jun, Sep, Dec
- **Budget Day**: February 1st
- **RBI Policy**: Every 2 months
- **FII/DII Data**: Daily after 6 PM

## 🧪 Testing Strategy

### 1. Unit Tests (`tests/`)
```bash
# Test individual components
python -m pytest tests/test_accumulation_agent.py
python -m pytest tests/test_confidence_engine.py
python -m pytest tests/test_governor.py
```

### 2. Integration Tests
```bash
# Test system interactions
python -m pytest tests/test_backtest_integration.py
python -m pytest tests/test_kpi_integration.py
```

### 3. Indian Market Validation
```python
# Prevent overfitting with Indian market data
WalkForwardTester.run(
    data=nse_historical_data,
    train_months=12,    # Training period
    test_months=3,      # Out-of-sample testing
    step_months=1       # Rolling window step
)
```

## ⚠️ Common Pitfalls in Indian Markets

### 1. Lookahead Bias
❌ Using future data in signal generation
✅ Only use data available at signal time

### 2. Overfitting to Bull Markets
❌ Optimizing only on 2020-2021 data
✅ Use walk-forward testing across market cycles

### 3. Ignoring Indian Market Structure
❌ Using US market assumptions
✅ Account for circuit breakers, settlement cycles

### 4. Currency Risk
❌ Ignoring INR volatility impact
✅ Monitor currency impact on IT/Pharma sectors

## 🚀 Deployment Checklist

- [ ] Backtest shows positive expectancy in INR
- [ ] Walk-forward validation across Indian market cycles
- [ ] Signal Quality KPI shows healthy conversion rates
- [ ] Paper trading validates current NSE/BSE behavior
- [ ] Risk management rules configured for Indian volatility
- [ ] Decision logging enabled for debugging
- [ ] INR-based KPI monitoring dashboard ready
- [ ] Indian market hours and holidays configured

## 🎯 Key Insights for Indian Market Mastery

1. **Expectancy in INR > Win Rate**: Focus on rupee profit per trade
2. **FII/DII Flow Matters**: Monitor institutional flow impact
3. **Sector Rotation**: Indian markets show strong sector momentum
4. **Volatility Management**: Higher volatility requires adjusted stops
5. **Settlement Awareness**: T+2 settlement impacts position sizing
6. **Tax Efficiency**: Consider STT and capital gains implications
7. **Market Timing**: Respect Indian market hours and holidays

This system emphasizes **expectancy-driven trading** adapted for **Indian market conditions** with **comprehensive risk management** and **robust validation**. Master these concepts for professional-grade algorithmic trading in NSE/BSE markets.