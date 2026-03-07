"""
NOOGH Project Analyzer via Perplexity AI
Sends key project code to Perplexity for deep architectural analysis.
"""
import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from tools.adapters.perplexity_adapter import PerplexityAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger('project_analyzer')

# Key files to analyze (most critical system files)
KEY_FILES = [
    'agents/autonomous_trading_agent.py',
    'trading/trap_hybrid_engine.py',
    'trading/binance_futures.py',
    'trading/market_analyzer.py',
    'trading/trade_tracker.py',
    'unified_core/neural_bridge.py',
    'unified_core/agent_daemon.py',
]

def collect_project_summary(src_dir: str) -> str:
    """Collect a compact summary of the project structure and key code snippets."""
    src = Path(src_dir)
    
    summary_parts = []
    summary_parts.append("# NOOGH Trading System - Project Analysis Request\n")
    summary_parts.append(f"Analysis Date: {datetime.now().isoformat()}\n")
    
    # 1. File tree
    summary_parts.append("## Project Structure (key directories):")
    for d in sorted(src.iterdir()):
        if d.is_dir() and not d.name.startswith('.') and d.name not in ['__pycache__', 'logs', 'data', 'node_modules']:
            py_count = len(list(d.rglob('*.py')))
            if py_count > 0:
                summary_parts.append(f"  {d.name}/ ({py_count} Python files)")
    summary_parts.append("")
    
    # 2. Key file snippets (first 80 lines of each)
    for rel_path in KEY_FILES:
        full_path = src / rel_path
        if full_path.exists():
            summary_parts.append(f"\n## FILE: {rel_path}")
            summary_parts.append(f"Size: {full_path.stat().st_size} bytes")
            try:
                lines = full_path.read_text(encoding='utf-8').split('\n')
                # Take first 60 lines + last 20 lines for context
                snippet = lines[:60]
                if len(lines) > 80:
                    snippet.append(f"\n... ({len(lines) - 80} lines omitted) ...\n")
                    snippet.extend(lines[-20:])
                summary_parts.append("```python")
                summary_parts.append('\n'.join(snippet))
                summary_parts.append("```")
            except Exception as e:
                summary_parts.append(f"  (Error reading: {e})")
    
    return '\n'.join(summary_parts)


async def analyze_project():
    """Send project to Perplexity for analysis."""
    adapter = PerplexityAdapter()
    src_dir = str(Path(__file__).parent.parent)
    
    if not adapter.api_key:
        logger.error("❌ PERPLEXITY_API_KEY not set!")
        return
    
    logger.info("📦 Collecting project summary...")
    project_summary = collect_project_summary(src_dir)
    
    # Truncate if too long (Perplexity has limits)
    max_chars = 12000
    if len(project_summary) > max_chars:
        project_summary = project_summary[:max_chars] + "\n\n... (truncated for API limits)"
    
    logger.info(f"📊 Project summary: {len(project_summary)} chars")
    
    # Analysis queries - split into focused questions
    queries = [
        {
            "title": "Architecture & Design Analysis",
            "query": f"""Analyze this crypto trading system architecture. Identify:
1. Major design flaws and anti-patterns
2. Missing components for a production trading system
3. Risk management gaps
4. Data flow bottlenecks

Here is the project code:

{project_summary}

Provide specific, actionable recommendations with code-level details."""
        },
        {
            "title": "Trading Logic & Strategy Analysis", 
            "query": f"""As a quantitative trading expert, analyze this trading system's strategy logic:
1. Is the signal generation (Trap Hybrid Engine) sound?
2. Is the AI Brain prompt effective for trade decisions?
3. Are the risk management rules (3 trades/day, 1% risk) appropriate?
4. What's missing compared to professional algo-trading systems?

Key code context:
- The system uses SMC/Order Flow for signals
- A local LLM (14B model) validates each signal
- Perplexity provides fundamental research
- Max 3 trades/day, 1% risk per trade

{project_summary[:6000]}

Give concrete improvements with priority ranking."""
        },
        {
            "title": "Security & Reliability Audit",
            "query": f"""Perform a security and reliability audit of this crypto trading bot:
1. API key handling vulnerabilities
2. Error handling gaps that could cause unexpected trades
3. Balance/position sync issues
4. Rate limiting and API abuse prevention
5. What happens when the system crashes mid-trade?

The system trades on Binance Futures with real money ($54 balance).

{project_summary[:6000]}

List critical issues first, then moderate, then low priority."""
        }
    ]
    
    results = []
    for i, q in enumerate(queries):
        logger.info(f"\n🔬 [{i+1}/{len(queries)}] Analyzing: {q['title']}...")
        result = await adapter.research(q['query'], model="sonar-pro")
        
        if result.get('success'):
            logger.info(f"✅ {q['title']} — completed")
            results.append({
                "title": q['title'],
                "analysis": result['content'],
                "citations": result.get('citations', [])
            })
        else:
            logger.error(f"❌ {q['title']} — failed: {result.get('error')}")
            results.append({
                "title": q['title'],
                "analysis": f"Error: {result.get('error')}",
                "citations": []
            })
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    # Save report
    report_path = Path(src_dir) / 'data' / 'perplexity_project_analysis.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# NOOGH System — Perplexity AI Analysis Report\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"---\n\n")
        
        for r in results:
            f.write(f"## {r['title']}\n\n")
            f.write(r['analysis'])
            f.write("\n\n")
            if r.get('citations'):
                f.write("**Sources:**\n")
                for c in r['citations']:
                    f.write(f"- {c}\n")
            f.write("\n---\n\n")
    
    logger.info(f"\n📄 Report saved: {report_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 PERPLEXITY ANALYSIS REPORT SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n## {r['title']}")
        print(r['analysis'][:500])
        print("...")
    
    return results


if __name__ == "__main__":
    asyncio.run(analyze_project())
