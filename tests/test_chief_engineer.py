"""
Test script for Chief Engineer Meta-Specialist

Demonstrates multi-domain problem solving with deep reasoning.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unified_core.specialists.chief_engineer import (
    ChiefEngineer,
    ReasoningDepth,
    Domain
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("chief_test")


async def test_simple_code_problem():
    """Test 1: Simple code optimization problem."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Code Optimization Problem")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    problem = "Optimize the memory usage in our inference pipeline by reducing tensor copies"
    
    solution = await chief.solve(problem, ReasoningDepth.MODERATE)
    
    logger.info(f"\n📊 Solution Summary:")
    logger.info(f"   Problem: {solution['problem']}")
    logger.info(f"   Confidence: {solution['confidence']:.2%}")
    logger.info(f"   Reasoning Steps: {solution['reasoning_chain']['total_steps']}")
    logger.info(f"   Domains: {', '.join(solution['reasoning_chain']['domains'])}")
    logger.info(f"   Time: {solution['metrics']['reasoning_time_seconds']:.3f}s")
    
    # Show reasoning chain
    logger.info(f"\n🧠 Reasoning Chain:")
    for step in solution['reasoning_chain']['steps']:
        logger.info(f"   {step['step']}. {step['thought']} [{step['confidence']:.2%}]")


async def test_multi_domain_problem():
    """Test 2: Complex multi-domain problem."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Multi-Domain Problem (Code + AI + Math)")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    problem = """
    Design and implement a new attention mechanism for our transformer model 
    that reduces computational complexity from O(n²) to O(n log n) while 
    maintaining accuracy above 95% on our benchmark.
    """
    
    solution = await chief.solve(problem, ReasoningDepth.DEEP)
    
    logger.info(f"\n📊 Solution Summary:")
    logger.info(f"   Confidence: {solution['confidence']:.2%}")
    logger.info(f"   Reasoning Steps: {solution['reasoning_chain']['total_steps']}")
    logger.info(f"   Domains: {', '.join(solution['reasoning_chain']['domains'])}")
    logger.info(f"   Time: {solution['metrics']['reasoning_time_seconds']:.3f}s")
    
    # Show reasoning chain
    logger.info(f"\n🧠 Reasoning Chain:")
    for step in solution['reasoning_chain']['steps']:
        logger.info(f"   {step['step']}. {step['thought']} [{step['confidence']:.2%}]")


async def test_system_problem():
    """Test 3: System diagnostics problem."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: System Diagnostics Problem")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    problem = """
    The system is experiencing high CPU usage (>90%) and slow API response times.
    Diagnose and fix the issue.
    """
    
    solution = await chief.solve(problem, ReasoningDepth.MODERATE)
    
    logger.info(f"\n📊 Solution Summary:")
    logger.info(f"   Confidence: {solution['confidence']:.2%}")
    logger.info(f"   Reasoning Steps: {solution['reasoning_chain']['total_steps']}")
    logger.info(f"   Domains: {', '.join(solution['reasoning_chain']['domains'])}")
    logger.info(f"   Time: {solution['metrics']['reasoning_time_seconds']:.3f}s")


async def test_security_problem():
    """Test 4: Security vulnerability analysis."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Security Vulnerability Analysis")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    problem = """
    Review our authentication system for potential security vulnerabilities
    and recommend patches to prevent injection attacks.
    """
    
    solution = await chief.solve(problem, ReasoningDepth.DEEP)
    
    logger.info(f"\n📊 Solution Summary:")
    logger.info(f"   Confidence: {solution['confidence']:.2%}")
    logger.info(f"   Reasoning Steps: {solution['reasoning_chain']['total_steps']}")
    logger.info(f"   Domains: {', '.join(solution['reasoning_chain']['domains'])}")
    logger.info(f"   Time: {solution['metrics']['reasoning_time_seconds']:.3f}s")


async def test_explanation():
    """Test 5: Explanation capability."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Detailed Explanation")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    problem = "Calculate the optimal batch size for training on RTX 5070 with 16GB VRAM"
    
    explanation = await chief.explain_reasoning(problem)
    
    logger.info(f"\n{explanation}")


async def test_learning_stats():
    """Test 6: Learning statistics."""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Learning Statistics")
    logger.info("="*80)
    
    chief = ChiefEngineer()
    
    # Solve a few problems
    problems = [
        "Optimize memory usage in the inference pipeline",
        "Debug slow API response times",
        "Implement caching for database queries",
        "Refactor the authentication system for better security"
    ]
    
    for prob in problems:
        await chief.solve(prob, ReasoningDepth.SHALLOW)
    
    stats = chief.get_learning_stats()
    
    logger.info(f"\n📊 Learning Statistics:")
    logger.info(f"   Problems Solved: {stats['problems_solved']}")
    logger.info(f"   Average Confidence: {stats['avg_confidence']:.2%}")
    logger.info(f"   Average Reasoning Steps: {stats['avg_reasoning_steps']:.1f}")
    logger.info(f"   Average Solve Time: {stats['avg_solve_time']:.3f}s")
    logger.info(f"\n   Domain Usage:")
    for domain, count in stats['most_used_domains'].items():
        logger.info(f"      {domain}: {count} times")


async def main():
    """Run all tests."""
    logger.info("\n🎯 Starting Chief Engineer Tests\n")
    
    # Run tests
    await test_simple_code_problem()
    await test_multi_domain_problem()
    await test_system_problem()
    await test_security_problem()
    await test_explanation()
    await test_learning_stats()
    
    logger.info("\n" + "="*80)
    logger.info("✅ All Tests Complete")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
