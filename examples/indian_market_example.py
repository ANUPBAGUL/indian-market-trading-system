"""
Indian Market Trading Example - Complete workflow for NSE/BSE stocks.

Demonstrates the trading system adapted for Indian equity markets
using NIFTY 50 stocks with Indian market conventions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from indian_data_loader import IndianDataLoader, load_indian_stocks
from indian_market_config import INDIAN_MARKET_CONFIG, IndianSectorMapper
from backtest_engine import BacktestEngine
from kpi_computer import KPIComputer
from governor import Governor
from confidence_engine import ConfidenceEngine
from accumulation_agent import AccumulationAgent
from trigger_agent import TriggerAgent
from sector_momentum_agent import SectorMomentumAgent
from position_sizer import PositionSizer

def create_indian_signal_generator():
    """Create signal generator adapted for Indian markets."""
    
    # Initialize agents with Indian market parameters
    accumulation_agent = AccumulationAgent()
    trigger_agent = TriggerAgent()
    sector_agent = SectorMomentumAgent()
    confidence_engine = ConfidenceEngine()
    position_sizer = PositionSizer()
    
    def generate_signals(day_data, existing_positions):
        """Generate trading signals for Indian stocks."""
        signals = []
        
        # Group by sector for sector analysis
        sector_data = {}
        for _, row in day_data.iterrows():
            sector = row.get('sector', 'Others')
            if sector not in sector_data:
                sector_data[sector] = []
            sector_data[sector].append(row)
        
        # Process each stock
        for _, row in day_data.iterrows():
            symbol = row['symbol']
            
            # Skip if already have position
            if symbol in existing_positions:
                continue
            
            # Skip if price too low/high for Indian market
            if row['close'] < INDIAN_MARKET_CONFIG.min_stock_price:
                continue
            if row['close'] > INDIAN_MARKET_CONFIG.max_stock_price:
                continue
            
            # Skip if volume too low
            if row['volume'] < INDIAN_MARKET_CONFIG.min_daily_volume:
                continue
            
            try:
                # Create symbol data (simplified for example)
                symbol_data = {
                    'current_price': row['close'],
                    'volume': row['volume'],
                    'high': row['high'],
                    'low': row['low'],
                    'open': row['open']
                }
                
                # Run agents
                acc_result = accumulation_agent.run(symbol_data, {})
                trigger_result = trigger_agent.run(symbol_data, {})
                
                # Get sector data for sector agent
                sector = row.get('sector', 'Others')
                sector_stocks = sector_data.get(sector, [])
                sector_result = sector_agent.run(symbol_data, {'sector_stocks': sector_stocks})
                
                # Combine with confidence engine
                confidence_result = confidence_engine.run(
                    accumulation_score=acc_result.get('confidence', 50),
                    trigger_score=trigger_result.get('confidence', 50),
                    sector_score=sector_result.get('confidence', 50),
                    earnings_score=70  # Simplified
                )
                
                # Check minimum confidence for Indian market
                if confidence_result['confidence'] < INDIAN_MARKET_CONFIG.min_confidence_threshold:
                    continue
                
                # Calculate position size
                position_size = position_sizer.calculate_shares(
                    stock_price=row['close'],
                    atr=row['close'] * 0.02,  # Simplified ATR
                    account_value=100000,  # INR 1 Lakh
                    risk_per_trade=INDIAN_MARKET_CONFIG.max_position_risk_pct
                )
                
                # Create signal
                signal = {
                    'symbol': symbol,
                    'type': 'ENTRY',
                    'confidence': confidence_result['confidence'],
                    'shares': position_size,
                    'sector': sector,
                    'stop_price': row['close'] * 0.92,  # 8% stop loss
                    'reasoning': f"Indian market signal: Confidence {confidence_result['confidence']:.1f}%"
                }
                
                signals.append(signal)
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        return signals
    
    return generate_signals

def main():
    """Run Indian market trading example."""
    
    print("=== INDIAN MARKET TRADING SYSTEM ===\\n")
    
    # Initialize Indian data loader
    loader = IndianDataLoader(data_source="yahoo")
    
    # Get sample of NIFTY 50 stocks
    nifty_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
    
    print(f"Loading data for {len(nifty_stocks)} NIFTY stocks...")
    
    try:
        # Load recent data (last 3 months)
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Try to load real data, fallback to sample data
        try:
            stock_data = loader.load_stock_data(
                symbols=nifty_stocks,
                start_date=start_date,
                end_date=end_date,
                exchange="NSE"
            )
            print(f"Loaded real market data: {len(stock_data)} records")
        except Exception as e:
            print(f"Could not load real data ({e}), using sample data...")
            stock_data = loader.create_sample_data(nifty_stocks)
            print(f"Created sample data: {len(stock_data)} records")
        
        if stock_data.empty:
            print("No data available. Exiting.")
            return
        
        # Display data summary
        print(f"\\nData Summary:")
        print(f"Date range: {stock_data['date'].min()} to {stock_data['date'].max()}")
        print(f"Stocks: {stock_data['symbol'].nunique()}")
        print(f"Sectors: {stock_data['sector'].nunique()}")
        print(f"Records: {len(stock_data)}")
        
        # Show sector distribution
        print(f"\\nSector Distribution:")
        sector_counts = stock_data['sector'].value_counts()
        for sector, count in sector_counts.items():
            print(f"  {sector}: {count} records")
        
        # Initialize backtesting components
        print(f"\\nInitializing Indian market backtester...")
        
        # Use Indian market configuration
        initial_capital = 500000  # INR 5 Lakhs
        backtester = BacktestEngine(initial_capital=initial_capital)
        
        # Create Governor with Indian market settings
        governor = Governor()
        
        # Create signal generator
        signal_generator = create_indian_signal_generator()
        
        # Run backtest
        print(f"\\nRunning backtest with INR {initial_capital:,} initial capital...")
        
        results = backtester.run(
            price_data=stock_data,
            signal_generator=signal_generator,
            governor=governor
        )
        
        # Analyze results
        print(f"\\n=== BACKTEST RESULTS ===")
        print(f"Total trades: {len(results['trades'])}")
        
        if results['trades']:
            # Calculate KPIs including Signal Quality
            kpis = KPIComputer.compute_kpis(
                trades=results['trades'],
                equity_curve=results['equity_curve'],
                signal_data=results.get('signal_log', [])
            )
            
            # Display comprehensive report
            print(KPIComputer.generate_report(kpis))
            
            # Indian market specific insights
            print(f"\\n=== INDIAN MARKET INSIGHTS ===")
            
            # Sector performance
            sector_performance = {}
            for trade in results['trades']:
                sector = 'Unknown'
                # Find sector from stock data
                stock_records = stock_data[stock_data['symbol'] == trade.symbol]
                if not stock_records.empty:
                    sector = stock_records.iloc[0]['sector']
                
                if sector not in sector_performance:
                    sector_performance[sector] = {'trades': 0, 'pnl': 0}
                
                sector_performance[sector]['trades'] += 1
                sector_performance[sector]['pnl'] += trade.pnl
            
            print("Sector Performance:")
            for sector, perf in sector_performance.items():
                avg_pnl = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
                print(f"  {sector}: {perf['trades']} trades, Avg P&L: ₹{avg_pnl:.0f}")
            
            # Currency formatting
            final_value = results['equity_curve'][-1]['total_value'] if results['equity_curve'] else initial_capital
            total_pnl = final_value - initial_capital
            
            print(f"\\nFinal Portfolio Value: ₹{final_value:,.0f}")
            print(f"Total P&L: ₹{total_pnl:,.0f}")
            print(f"Return: {(total_pnl/initial_capital)*100:.1f}%")
            
        else:
            print("No trades generated. Consider:")
            print("- Lowering confidence thresholds")
            print("- Checking data quality")
            print("- Reviewing Indian market parameters")
        
        print(f"\\n=== NEXT STEPS ===")
        print("1. Tune parameters for Indian market volatility")
        print("2. Add more NIFTY/SENSEX stocks to universe")
        print("3. Implement Indian market regime detection")
        print("4. Add sector rotation strategies")
        print("5. Consider currency hedging for global exposure")
        
    except Exception as e:
        print(f"Error in Indian market example: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()