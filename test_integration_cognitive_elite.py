import asyncio
import logging
import sys
import uuid

# Change logging format to be cleaner for the demo
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from unified_core.evolution.controller import EvolutionController
from unified_core.evolution.ledger import EvolutionProposal, ProposalType

async def run_integration_test():
    print("=" * 70)
    print("🚀 LIVE INTEGRATION TEST: NOOGH Cognitive Elite Engine vs Evolution")
    print("=" * 70)
    
    ec = EvolutionController()
    
    unique_target = f"src/test_target_{uuid.uuid4().hex[:8]}.py"
    
    print("\n" + "#" * 60)
    print("--- TEST 1: The Reckless AI Proposal (High Risk, Bad Logic) ---")
    print("#" * 60)
    
    bad_proposal = EvolutionProposal(
        proposal_id="EVO-TEST-001",
        proposal_type=ProposalType.CODE,
        scope="core",
        description="Rewrite the entire database core in one go to make it faster.",
        risk_score=95,  # Very high risk!
        targets=[unique_target],
        diff="fake diff",
        metadata={
            "analysis": "Trust me it will be faster. I didn't test it but intuition says YES."
        }
    )
    
    print(f"📥 Submitting Proposal: '{bad_proposal.description}'")
    print(f"⚠️ Risk Score: {bad_proposal.risk_score}")
    print(f"🧠 Provided Reasoning: '{bad_proposal.metadata['analysis']}'\n")
    
    # Save it to the Ledger to avoid DB sync issues
    ec.ledger.record_proposal(bad_proposal)
    await asyncio.sleep(0.1) # Simulate real world gap
    
    # We expect the Cognitive Elite Engine to block this!
    result = await ec._process_proposal(bad_proposal)
    print(f"\n🛑 Final Verdict: {result['status']}")
    print(f"📝 Block Reason: {result.get('reason', 'N/A')}")
    
    
    print("\n" + "#" * 60)
    print("--- TEST 2: The Elite AI Proposal (Balanced Risk, Sound Logic) ---")
    print("#" * 60)
    
    good_proposal = EvolutionProposal(
        proposal_id="EVO-TEST-002",
        proposal_type=ProposalType.CODE,
        scope="core",
        description="Add B-Tree index to users table to optimize query latency.",
        risk_score=15,  # Low risk
        targets=[unique_target],
        diff="fake diff",
        metadata={
            "analysis": "Query latency on /users is 500ms. Profiling shows sequential scan. Adding B-Tree index improves sequential time from O(N) to O(log N)."
        }
    )
    
    print(f"📥 Submitting Proposal: '{good_proposal.description}'")
    print(f"✅ Risk Score: {good_proposal.risk_score}")
    print(f"🧠 Provided Reasoning: '{good_proposal.metadata['analysis']}'\n")
    
    # Save it to the Ledger to avoid DB sync issues
    ec.ledger.record_proposal(good_proposal)
    await asyncio.sleep(0.1)
    
    # We expect the Cognitive Elite Engine to approve this, print an explanation, 
    # and then proceed to the Canary test (where it will fail because 'fake diff' is invalid, which is fine)
    result = await ec._process_proposal(good_proposal)
    print(f"\n⚠️ Final Verdict (Failed at Canary, but PASSED Cognitive check!): {result['status']}")
    
if __name__ == "__main__":
    asyncio.run(run_integration_test())
