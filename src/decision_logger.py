"""
Decision Logger - Captures all trading decisions for explainability and debugging.

Logs agent decisions, governor decisions, and trade rationale to enable
post-trade analysis and system debugging.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class DecisionLogger:
    """
    Comprehensive decision logging system for trade explainability.
    
    Captures:
    1. Agent decision logs (why each agent scored as it did)
    2. Governor decision logs (approval/rejection rationale)
    3. Trade rationale logging (complete decision chain)
    """
    
    def __init__(self):
        self.agent_decisions: List[Dict] = []
        self.governor_decisions: List[Dict] = []
        self.trade_rationales: List[Dict] = []
    
    def log_agent_decision(
        self,
        agent_name: str,
        symbol: str,
        date: str,
        decision_type: str,
        score: float,
        evidence: Dict,
        rationale: str
    ):
        """
        Log individual agent decision with evidence and reasoning.
        
        Args:
            agent_name: Name of the agent (AccumulationAgent, TriggerAgent, etc.)
            symbol: Stock symbol
            date: Decision date
            decision_type: ENTRY or EXIT
            score: Agent's confidence score (0-100)
            evidence: Supporting evidence data
            rationale: Human-readable explanation
        """
        decision = {
            'timestamp': datetime.now().isoformat(),
            'agent_name': agent_name,
            'symbol': symbol,
            'date': date,
            'decision_type': decision_type,
            'score': score,
            'evidence': evidence,
            'rationale': rationale
        }
        
        self.agent_decisions.append(decision)
    
    def log_governor_decision(
        self,
        symbol: str,
        date: str,
        signal_type: str,
        decision: str,
        reason: str,
        risk_checks: Dict,
        portfolio_state: Dict
    ):
        """
        Log Governor's final decision with risk analysis.
        
        Args:
            symbol: Stock symbol
            date: Decision date
            signal_type: ENTRY or EXIT
            decision: ENTER, NO_TRADE, or EXIT
            reason: Governor's reasoning
            risk_checks: Risk validation results
            portfolio_state: Current portfolio status
        """
        gov_decision = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'date': date,
            'signal_type': signal_type,
            'decision': decision,
            'reason': reason,
            'risk_checks': risk_checks,
            'portfolio_state': portfolio_state
        }
        
        self.governor_decisions.append(gov_decision)
    
    def log_trade_rationale(
        self,
        trade_id: str,
        symbol: str,
        action: str,
        date: str,
        price: float,
        agent_scores: Dict,
        confidence_score: float,
        position_size: int,
        stop_price: float,
        complete_rationale: str
    ):
        """
        Log complete trade rationale linking all decisions.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Stock symbol
            action: ENTRY or EXIT
            date: Trade date
            price: Execution price
            agent_scores: All agent scores that led to this trade
            confidence_score: Final confidence score
            position_size: Number of shares
            stop_price: Stop loss price
            complete_rationale: Full explanation of trade logic
        """
        rationale = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade_id,
            'symbol': symbol,
            'action': action,
            'date': date,
            'price': price,
            'agent_scores': agent_scores,
            'confidence_score': confidence_score,
            'position_size': position_size,
            'stop_price': stop_price,
            'complete_rationale': complete_rationale
        }
        
        self.trade_rationales.append(rationale)
    
    def get_trade_debug_info(self, symbol: str, date: str) -> Dict:
        """
        Get complete debugging information for a specific trade.
        
        Args:
            symbol: Stock symbol
            date: Trade date
            
        Returns:
            Complete decision chain for debugging
        """
        # Find all related decisions
        related_agent_decisions = [
            d for d in self.agent_decisions 
            if d['symbol'] == symbol and d['date'] == date
        ]
        
        related_governor_decisions = [
            d for d in self.governor_decisions
            if d['symbol'] == symbol and d['date'] == date
        ]
        
        related_trade_rationales = [
            d for d in self.trade_rationales
            if d['symbol'] == symbol and d['date'] == date
        ]
        
        return {
            'symbol': symbol,
            'date': date,
            'agent_decisions': related_agent_decisions,
            'governor_decisions': related_governor_decisions,
            'trade_rationales': related_trade_rationales,
            'decision_chain_summary': self._generate_decision_summary(
                related_agent_decisions,
                related_governor_decisions,
                related_trade_rationales
            )
        }
    
    def _generate_decision_summary(
        self,
        agent_decisions: List[Dict],
        governor_decisions: List[Dict],
        trade_rationales: List[Dict]
    ) -> str:
        """Generate human-readable decision chain summary."""
        if not agent_decisions and not governor_decisions:
            return "No decisions found for this trade"
        
        summary = []
        
        # Agent analysis
        if agent_decisions:
            summary.append("AGENT ANALYSIS:")
            for decision in agent_decisions:
                summary.append(f"  {decision['agent_name']}: {decision['score']:.1f} - {decision['rationale']}")
        
        # Governor decision
        if governor_decisions:
            summary.append("\nGOVERNOR DECISION:")
            for decision in governor_decisions:
                summary.append(f"  Decision: {decision['decision']} - {decision['reason']}")
        
        # Trade execution
        if trade_rationales:
            summary.append("\nTRADE EXECUTION:")
            for rationale in trade_rationales:
                summary.append(f"  {rationale['action']} {rationale['position_size']} shares at ${rationale['price']:.2f}")
                summary.append(f"  Confidence: {rationale['confidence_score']:.1f}%")
        
        return "\n".join(summary)
    
    def export_logs(self, filepath: str):
        """Export all logs to JSON file for analysis."""
        logs = {
            'agent_decisions': self.agent_decisions,
            'governor_decisions': self.governor_decisions,
            'trade_rationales': self.trade_rationales,
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def clear_logs(self):
        """Clear all logs (use with caution)."""
        self.agent_decisions.clear()
        self.governor_decisions.clear()
        self.trade_rationales.clear()
    
    def get_bad_trade_analysis(self, symbol: str, entry_date: str, exit_date: str) -> str:
        """
        Generate analysis for debugging a bad trade.
        
        Args:
            symbol: Stock symbol
            entry_date: Trade entry date
            exit_date: Trade exit date
            
        Returns:
            Detailed analysis for debugging
        """
        entry_info = self.get_trade_debug_info(symbol, entry_date)
        exit_info = self.get_trade_debug_info(symbol, exit_date)
        
        analysis = [
            f"=== BAD TRADE ANALYSIS: {symbol} ===",
            f"Entry Date: {entry_date}",
            f"Exit Date: {exit_date}",
            "",
            "ENTRY DECISION ANALYSIS:",
            entry_info['decision_chain_summary'],
            "",
            "EXIT DECISION ANALYSIS:",
            exit_info['decision_chain_summary'],
            "",
            "DEBUGGING QUESTIONS:",
            "1. Were agent scores justified by market conditions?",
            "2. Did Governor properly assess risk limits?",
            "3. Was position sizing appropriate for confidence level?",
            "4. Did exit timing follow system rules?",
            "5. What market events occurred during the trade?"
        ]
        
        return "\n".join(analysis)