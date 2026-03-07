import sys
import logging
from pathlib import Path

# Fix protobuf errors by using the right env
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from unified_core.intelligence import CriticalThinker, Evidence

def test_veto():
    print("\n--- 🧠 NOOGH VETO INTEGRATION TEST ---\n")
    thinker = CriticalThinker()
    
    # Mock some evidence
    evidence_list = [
        Evidence(content="Regime is RANGING", source="MarketRegime"),
        Evidence(content="Pattern score is 0.30", source="CandlePatterns"),
        Evidence(content="RSI is 85.00 (Overbought)", source="Indicators"),
        Evidence(content="Raw Brain Decision: LONG (Confidence: 0.85)", source="TradingBrain")
    ]
    
    print("Market Context: Ranging market, weak pattern, overbought RSI.")
    print("Brain Decision: LONG (Too aggressive)")
    print("Passing decision to CriticalThinker...")
    
    # Test reasoning
    eval_result = thinker.evaluate_reasoning(
        claim="Entering LONG position for BTCUSDT is highly profitable right now.",
        evidence=evidence_list,
        reasoning="The indicators suggest a breakout."
    )
    
    is_valid = eval_result.get('valid', False)
    confidence = eval_result.get('confidence', 0.0)
    
    print(f"\n🎯 Critical Evaluation:")
    print(f"Valid: {'✅ Yes' if is_valid else '❌ No (VETO)'}")
    print(f"Cognitive Confidence: {confidence:.0%}")
    if eval_result.get('issues'):
        print(f"Issues Detected: {eval_result['issues']}")
        
    print("\n--------------------------------------\n")

if __name__ == '__main__':
    test_veto()
