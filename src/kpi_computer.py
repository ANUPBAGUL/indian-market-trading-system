"""
KPI Computation - Calculates key performance indicators for trading system evaluation.

The system computes essential metrics that guide trading decisions and system
optimization without requiring charts or visual analysis.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class KPIComputer:
    """
    KPI computation system with four key metrics:
    1. Expectancy (average profit per trade)
    2. Max drawdown (worst peak-to-trough decline)
    3. Win rate (percentage of profitable trades)
    4. Confidence bucket stats (calibration analysis)
    """
    
    @staticmethod
    def compute_kpis(
        trades: List,
        equity_curve: List[Dict],
        confidence_buckets: Optional[List[Dict]] = None,
        signal_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Compute comprehensive KPI report.
        
        Args:
            trades: List of Trade objects with pnl, pnl_pct attributes
            equity_curve: List of equity curve points with total_value
            confidence_buckets: Optional list with confidence_bucket, outcome fields
            
        Returns:
            Dict with all KPI metrics and analysis
            
        Example:
            kpis = KPIComputer.compute_kpis(
                trades=backtest_results['trades'],
                equity_curve=backtest_results['equity_curve'],
                confidence_buckets=confidence_data
            )
        """
        if not trades:
            return KPIComputer._empty_kpis()
        
        # Core metrics
        expectancy = KPIComputer._calculate_expectancy(trades)
        max_drawdown = KPIComputer._calculate_max_drawdown(equity_curve)
        win_rate = KPIComputer._calculate_win_rate(trades)
        
        # Confidence bucket analysis
        bucket_stats = {}
        if confidence_buckets:
            bucket_stats = KPIComputer._analyze_confidence_buckets(confidence_buckets)
        
        # Signal quality analysis
        signal_quality = {}
        if signal_data:
            signal_quality = KPIComputer._analyze_signal_quality(signal_data, trades)
        
        # Additional metrics
        trade_stats = KPIComputer._calculate_trade_stats(trades)
        
        return {
            'expectancy': expectancy,
            'max_drawdown_pct': max_drawdown,
            'win_rate_pct': win_rate,
            'confidence_bucket_stats': bucket_stats,
            'signal_quality_stats': signal_quality,
            'trade_statistics': trade_stats,
            'total_trades': len(trades),
            'summary': KPIComputer._generate_summary(expectancy, max_drawdown, win_rate, len(trades))
        }
    
    @staticmethod
    def _calculate_expectancy(trades: List) -> float:
        """Calculate expectancy (average profit per trade)."""
        if not trades:
            return 0.0
        
        total_pnl = sum(trade.pnl for trade in trades)
        return round(total_pnl / len(trades), 2)
    
    @staticmethod
    def _calculate_max_drawdown(equity_curve: List[Dict]) -> float:
        """Calculate maximum drawdown percentage."""
        if len(equity_curve) < 2:
            return 0.0
        
        values = [point['total_value'] for point in equity_curve]
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return round(max_dd * 100, 2)
    
    @staticmethod
    def _calculate_win_rate(trades: List) -> float:
        """Calculate win rate percentage."""
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for trade in trades if trade.pnl > 0)
        return round((winning_trades / len(trades)) * 100, 1)
    
    @staticmethod
    def _analyze_confidence_buckets(confidence_data: List[Dict]) -> Dict:
        """Analyze confidence bucket calibration."""
        if not confidence_data:
            return {}
        
        # Group by confidence bucket
        bucket_groups = {}
        for record in confidence_data:
            bucket = record.get('confidence_bucket', 'Unknown')
            outcome = record.get('outcome', False)  # True for wins, False for losses
            
            if bucket not in bucket_groups:
                bucket_groups[bucket] = {'wins': 0, 'total': 0}
            
            bucket_groups[bucket]['total'] += 1
            if outcome:
                bucket_groups[bucket]['wins'] += 1
        
        # Calculate actual win rates
        bucket_stats = {}
        for bucket, data in bucket_groups.items():
            actual_win_rate = (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0
            
            # Extract expected win rate from bucket name (e.g., "70-75" -> 72.5)
            expected_rate = KPIComputer._extract_expected_rate(bucket)
            
            calibration_error = abs(actual_win_rate - expected_rate) if expected_rate else 0
            
            bucket_stats[bucket] = {
                'trades': data['total'],
                'wins': data['wins'],
                'actual_win_rate': round(actual_win_rate, 1),
                'expected_win_rate': expected_rate,
                'calibration_error': round(calibration_error, 1)
            }
        
        return bucket_stats
    
    @staticmethod
    def _analyze_signal_quality(signal_data: List[Dict], trades: List) -> Dict:
        """Analyze signal quality and conversion rates."""
        if not signal_data:
            return {}
        
        total_signals = len(signal_data)
        executed_signals = len([s for s in signal_data if s.get('executed', False)])
        
        # Calculate conversion rate
        conversion_rate = (executed_signals / total_signals * 100) if total_signals > 0 else 0
        
        # Analyze signal accuracy (for executed signals that became trades)
        profitable_signals = 0
        executed_count = 0
        
        for signal in signal_data:
            if signal.get('executed', False):
                executed_count += 1
                # Find corresponding trade
                matching_trade = next(
                    (t for t in trades if t.symbol == signal.get('symbol') and 
                     t.entry_date == signal.get('date')), None
                )
                if matching_trade and matching_trade.pnl > 0:
                    profitable_signals += 1
        
        signal_accuracy = (profitable_signals / executed_count * 100) if executed_count > 0 else 0
        
        # Analyze rejection reasons
        rejection_reasons = {}
        for signal in signal_data:
            if not signal.get('executed', False):
                reason = signal.get('rejection_reason', 'Unknown')
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        return {
            'total_signals': total_signals,
            'executed_signals': executed_signals,
            'conversion_rate_pct': round(conversion_rate, 1),
            'signal_accuracy_pct': round(signal_accuracy, 1),
            'profitable_signals': profitable_signals,
            'rejection_reasons': rejection_reasons
        }
    
    @staticmethod
    def _extract_expected_rate(bucket_name: str) -> Optional[float]:
        """Extract expected win rate from bucket name."""
        if '-' in bucket_name:
            try:
                parts = bucket_name.split('-')
                if len(parts) == 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    return (low + high) / 2
            except ValueError:
                pass
        return None
    
    @staticmethod
    def _calculate_trade_stats(trades: List) -> Dict:
        """Calculate detailed trade statistics."""
        if not trades:
            return {}
        
        pnls = [trade.pnl for trade in trades]
        winning_trades = [trade.pnl for trade in trades if trade.pnl > 0]
        losing_trades = [trade.pnl for trade in trades if trade.pnl < 0]
        
        stats = {
            'avg_win': round(np.mean(winning_trades), 2) if winning_trades else 0.0,
            'avg_loss': round(np.mean(losing_trades), 2) if losing_trades else 0.0,
            'largest_win': round(max(pnls), 2),
            'largest_loss': round(min(pnls), 2),
            'profit_factor': 0.0
        }
        
        # Profit factor = Gross Profit / Gross Loss
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0
        
        if gross_loss > 0:
            stats['profit_factor'] = round(gross_profit / gross_loss, 2)
        
        return stats
    
    @staticmethod
    def _generate_summary(expectancy: float, max_dd: float, win_rate: float, total_trades: int) -> str:
        """Generate text summary of system performance."""
        if total_trades == 0:
            return "No trades to analyze"
        
        # System viability assessment
        if expectancy > 0:
            viability = "PROFITABLE"
        elif expectancy > -50:
            viability = "MARGINAL"
        else:
            viability = "UNPROFITABLE"
        
        # Risk assessment
        if max_dd < 5:
            risk_level = "LOW"
        elif max_dd < 15:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        
        return f"{viability} system with {risk_level} risk. " \
               f"Expectancy: ${expectancy}, Max DD: {max_dd}%, Win Rate: {win_rate}%"
    
    @staticmethod
    def _empty_kpis() -> Dict:
        """Return empty KPI structure for no-trade scenarios."""
        return {
            'expectancy': 0.0,
            'max_drawdown_pct': 0.0,
            'win_rate_pct': 0.0,
            'confidence_bucket_stats': {},
            'signal_quality_stats': {},
            'trade_statistics': {},
            'total_trades': 0,
            'summary': "No trades to analyze"
        }
    
    @staticmethod
    def generate_report(kpis: Dict) -> str:
        """Generate formatted KPI report."""
        if kpis['total_trades'] == 0:
            return "=== KPI REPORT ===\nNo trades to analyze"
        
        report = ["=== KPI REPORT ===\n"]
        
        # Core Metrics
        report.append("CORE METRICS:")
        report.append(f"  Expectancy: ${kpis['expectancy']:.2f} per trade")
        report.append(f"  Max Drawdown: {kpis['max_drawdown_pct']:.1f}%")
        report.append(f"  Win Rate: {kpis['win_rate_pct']:.1f}%")
        report.append(f"  Total Trades: {kpis['total_trades']}")
        report.append("")
        
        # Trade Statistics
        if kpis['trade_statistics']:
            stats = kpis['trade_statistics']
            report.append("TRADE STATISTICS:")
            report.append(f"  Average Win: ${stats['avg_win']:.2f}")
            report.append(f"  Average Loss: ${stats['avg_loss']:.2f}")
            report.append(f"  Largest Win: ${stats['largest_win']:.2f}")
            report.append(f"  Largest Loss: ${stats['largest_loss']:.2f}")
            report.append(f"  Profit Factor: {stats['profit_factor']:.2f}")
            report.append("")
        
        # Signal Quality Analysis
        if kpis['signal_quality_stats']:
            sq = kpis['signal_quality_stats']
            report.append("SIGNAL QUALITY:")
            report.append(f"  Total Signals: {sq['total_signals']}")
            report.append(f"  Executed: {sq['executed_signals']} ({sq['conversion_rate_pct']:.1f}%)")
            report.append(f"  Signal Accuracy: {sq['signal_accuracy_pct']:.1f}%")
            
            if sq['rejection_reasons']:
                report.append("  Rejection Reasons:")
                for reason, count in sq['rejection_reasons'].items():
                    pct = (count / sq['total_signals'] * 100) if sq['total_signals'] > 0 else 0
                    report.append(f"    {reason}: {count} ({pct:.1f}%)")
            report.append("")
        
        # Confidence Bucket Analysis
        if kpis['confidence_bucket_stats']:
            report.append("CONFIDENCE CALIBRATION:")
            report.append("  Bucket    | Trades | Actual | Expected | Error")
            report.append("  ----------|--------|--------|----------|------")
            
            for bucket, stats in kpis['confidence_bucket_stats'].items():
                expected = stats['expected_win_rate'] or 0
                report.append(f"  {bucket:<9} | {stats['trades']:>6} | "
                            f"{stats['actual_win_rate']:>5.1f}% | {expected:>7.1f}% | "
                            f"{stats['calibration_error']:>4.1f}%")
            report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  {kpis['summary']}")
        
        return "\n".join(report)