# Daily Trading Workflow - Step by Step Guide

## 🌅 MORNING ROUTINE (Before Market Open)

### Step 1: Run the System
```bash
# Choose your market
python run_trading.py

# Or run directly
python run_us_trading.py      # For US markets
python run_indian_trading.py  # For Indian markets
```

### Step 2: Review System Output
The system will show you:

**Example Output:**
```
=== SIGNALS GENERATED ===
✅ RELIANCE: ENTER - Confidence 75% - Size: 100 shares - Stop: Rs.2,300
✅ TCS: ENTER - Confidence 68% - Size: 50 shares - Stop: Rs.3,200
❌ HDFCBANK: REJECTED - Low confidence (58%)
❌ INFY: REJECTED - Sector limit reached
```

### Step 3: Create Your Trading Plan
**Write down in a notebook or spreadsheet:**

| Stock | Action | Shares | Entry Price | Stop Loss | Confidence |
|-------|--------|--------|-------------|-----------|------------|
| RELIANCE | BUY | 100 | Market | Rs.2,300 | 75% |
| TCS | BUY | 50 | Market | Rs.3,200 | 68% |

### Step 4: Prepare for Market Open
- **Check your broker account** - Ensure sufficient funds
- **Set up orders** - Prepare buy orders for approved stocks
- **Set stop losses** - Use system-provided stop prices

---

## 📈 MARKET HOURS (During Trading)

### Step 1: Execute Trades Exactly
**For each approved signal:**

1. **Place Market Order**
   - Stock: As specified by system
   - Quantity: Exact shares recommended
   - Type: Market order at open

2. **Set Stop Loss Immediately**
   - Price: Exact stop price from system
   - Type: Stop-loss order
   - Good till cancelled

### Step 2: Monitor Positions
**Do NOT:**
- ❌ Change position sizes
- ❌ Override stop losses
- ❌ Add to positions
- ❌ Take profits early

**Do:**
- ✅ Let stops work automatically
- ✅ Record actual fill prices
- ✅ Stay disciplined

### Step 3: Record Actual Executions
**Update your trading log:**

| Stock | Planned Entry | Actual Entry | Planned Stop | Actual Stop | Status |
|-------|---------------|--------------|--------------|-------------|---------|
| RELIANCE | Market | Rs.2,450 | Rs.2,300 | Rs.2,300 | ACTIVE |
| TCS | Market | Rs.3,350 | Rs.3,200 | Rs.3,200 | ACTIVE |

---

## 🌙 EVENING ROUTINE (After Market Close)

### Step 1: Log All Outcomes
**For each trade, record:**

```
Trade Log - [Date]
Stock: RELIANCE
Entry Date: [Today's date]
Entry Price: Rs.2,450 (actual fill)
Shares: 100
Confidence at Entry: 75%
Current Status: ACTIVE / STOPPED / CLOSED
Exit Price: [If closed] Rs.2,380
Exit Reason: STOP LOSS / SIGNAL EXIT / TIME STOP
P&L: Rs.-7,000 (if closed)
```

### Step 2: Update Performance Tracking
**Weekly spreadsheet:**

| Week | Total Trades | Winners | Losers | Total P&L | Win Rate | Avg Win | Avg Loss |
|------|--------------|---------|---------|-----------|----------|---------|----------|
| Week 1 | 5 | 3 | 2 | Rs.12,500 | 60% | Rs.8,500 | Rs.-3,000 |

### Step 3: Review System Performance
**Monthly analysis:**
- **Expectancy**: Average profit per trade
- **Max Drawdown**: Worst losing streak
- **Signal Quality**: How many signals became trades
- **Confidence Calibration**: Are 70% confidence trades winning 70%?

### Step 4: Plan Tomorrow
**Simple checklist:**
- [ ] Any positions to monitor tomorrow?
- [ ] Any stops that might trigger?
- [ ] System running smoothly?
- [ ] Any observations to note?

---

## 📊 PRACTICAL TOOLS

### Daily Trading Log Template
```
DATE: ___________
MARKET: US / INDIAN

MORNING SIGNALS:
Stock: _______ Action: _______ Confidence: ___% Shares: _____
Stock: _______ Action: _______ Confidence: ___% Shares: _____

EXECUTIONS:
Stock: _______ Entry: _______ Stop: _______ Status: _______
Stock: _______ Entry: _______ Stop: _______ Status: _______

EVENING REVIEW:
Trades Closed Today: _____
P&L Today: _____
Notes: _________________________________
```

### Weekly Review Questions
1. **Did I follow all system signals exactly?**
2. **Did I override any decisions? (Should be NO)**
3. **Are my stops working as expected?**
4. **Is the system generating reasonable signals?**
5. **Am I staying disciplined?**

---

## 🎯 KEY RULES TO FOLLOW

### DO:
- ✅ Run system every morning
- ✅ Execute trades exactly as recommended
- ✅ Use exact position sizes
- ✅ Set stops immediately
- ✅ Log everything
- ✅ Trust "no trade" days

### DON'T:
- ❌ Override system decisions
- ❌ Change position sizes
- ❌ Move stop losses (except system updates)
- ❌ Add to losing positions
- ❌ Take profits early without system signal
- ❌ Trade on emotions or news

---

## 📱 SAMPLE DAILY SCHEDULE

**US Markets (EST):**
- **8:00 AM**: Run system, review signals
- **9:30 AM**: Execute approved trades
- **4:00 PM**: Market close, log outcomes
- **6:00 PM**: Update performance tracking

**Indian Markets (IST):**
- **8:00 AM**: Run system, review signals  
- **9:15 AM**: Execute approved trades
- **3:30 PM**: Market close, log outcomes
- **5:00 PM**: Update performance tracking

---

## 🚨 TROUBLESHOOTING

**"No signals today"**
- This is NORMAL - system is selective
- Do NOT force trades
- Use the time to review past performance

**"System rejected my favorite stock"**
- Trust the system
- The Governor has good reasons
- Your job is execution, not stock picking

**"I want to take profits early"**
- Let the system decide exits
- Early profit-taking destroys expectancy
- Trust the process

This workflow ensures you follow the system exactly while maintaining proper records for continuous improvement.