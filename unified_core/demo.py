#!/usr/bin/env python3
"""
Unified Core - Example Usage Script
Demonstrates all main capabilities
"""
import asyncio
import sys
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")


async def demo_data_router():
    """Demo: DataRouter automatic classification and routing."""
    print("\n" + "="*60)
    print("📊 DataRouter Demo - Automatic Query Classification")
    print("="*60)
    
    from unified_core.db.router import DataRouter
    
    router = DataRouter()
    
    # Test different input types
    test_cases = [
        ("2 + 3 * 4", "Mathematical expression"),
        ("if x then y else z", "Logical expression"),
        ("A is related to B", "Relational query"),
        ("What is the meaning of life?", "Semantic/NLP query"),
        ([0.1, 0.2, 0.3, 0.4], "Embedding vector"),
        ({"expression": "x = 5"}, "Equation dict"),
        ({"from": "A", "to": "B", "relationship": "KNOWS"}, "Relationship dict"),
    ]
    
    for input_data, description in test_cases:
        result = router.classify(input_data)
        print(f"\n📌 {description}")
        print(f"   Input: {str(input_data)[:50]}...")
        print(f"   Type: {result.data_type.name}")
        print(f"   Target DB: {result.primary_target}")
        print(f"   Confidence: {result.confidence:.2f}")


async def demo_security_audit():
    """Demo: SecOpsAgent security analysis."""
    print("\n" + "="*60)
    print("🔒 SecOpsAgent Demo - Security Analysis")
    print("="*60)
    
    from unified_core.secops_agent import SecOpsAgent
    from unified_core.dev_agent import CodeArtifact, CodeLanguage
    
    secops = SecOpsAgent()
    
    # Safe code
    safe_code = '''
def calculate_sum(numbers: list) -> int:
    """Calculate sum of numbers safely."""
    return sum(numbers)

def test_sum():
    assert calculate_sum([1, 2, 3]) == 6
'''
    
    # Dangerous code
    dangerous_code = '''
import pickle
import subprocess

# Dangerous patterns
data = pickle.load(open("data.pkl", "rb"))
subprocess.run(user_input, shell=True)
result = eval(request.get("expression"))
'''
    
    print("\n✅ Safe Code Audit:")
    safe_artifact = CodeArtifact(CodeLanguage.PYTHON, safe_code, "safe.py", "Safe code")
    result = await secops.audit(safe_artifact)
    print(f"   Approved: {result.approved}")
    print(f"   Risk Score: {result.risk_score}")
    print(f"   Issues: {len(result.issues)}")
    
    print("\n❌ Dangerous Code Audit:")
    dangerous_artifact = CodeArtifact(CodeLanguage.PYTHON, dangerous_code, "danger.py", "Dangerous")
    result = await secops.audit(dangerous_artifact)
    print(f"   Approved: {result.approved}")
    print(f"   Risk Score: {result.risk_score}")
    print(f"   Issues found: {len(result.issues)}")
    for issue in result.issues[:5]:
        print(f"   - {issue}")


async def demo_resource_monitor():
    """Demo: ResourceMonitor system metrics."""
    print("\n" + "="*60)
    print("📈 ResourceMonitor Demo - System Metrics")
    print("="*60)
    
    from unified_core.resources.monitor import ResourceMonitor
    
    monitor = ResourceMonitor(gpu_enabled=True)
    await monitor.initialize()
    
    snapshot = await monitor.get_snapshot()
    
    print(f"\n🖥️  CPU:")
    print(f"   Usage: {snapshot.cpu.usage_percent:.1f}%")
    print(f"   Cores: {snapshot.cpu.core_count} (threads: {snapshot.cpu.thread_count})")
    print(f"   Load: {snapshot.cpu.load_1m:.2f} / {snapshot.cpu.load_5m:.2f} / {snapshot.cpu.load_15m:.2f}")
    
    print(f"\n💾 Memory:")
    print(f"   Total: {snapshot.memory.total_bytes / (1024**3):.1f} GB")
    print(f"   Used: {snapshot.memory.used_bytes / (1024**3):.1f} GB ({snapshot.memory.usage_percent:.1f}%)")
    
    if snapshot.gpus:
        print(f"\n🎮 GPUs ({len(snapshot.gpus)}):")
        for gpu in snapshot.gpus:
            print(f"   [{gpu.device_id}] {gpu.name}")
            print(f"       Memory: {gpu.memory_used_mb}/{gpu.memory_total_mb} MB ({gpu.memory_percent:.1f}%)")
            print(f"       Utilization: {gpu.gpu_utilization}%")
            print(f"       Temperature: {gpu.temperature_c}°C")
    else:
        print("\n🎮 No GPUs detected (NVML unavailable)")
    
    print(f"\n📊 System:")
    print(f"   Processes: {snapshot.process_count}")
    print(f"   Uptime: {snapshot.uptime_seconds / 3600:.1f} hours")
    
    await monitor.shutdown()


async def demo_filesystem():
    """Demo: SecureFileSystem sandboxed access."""
    print("\n" + "="*60)
    print("📁 SecureFileSystem Demo - Sandboxed Access")
    print("="*60)
    
    import tempfile
    import os
    
    from unified_core.resources.filesystem import SecureFileSystem
    
    # Create temp directory as allowed root
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SecureFileSystem(allowed_roots=[tmpdir])
        
        test_file = os.path.join(tmpdir, "test.txt")
        
        # Write
        print(f"\n📝 Write to {test_file}...")
        result = fs.write_file(test_file, "Hello from Unified Core!", agent_id="demo")
        print(f"   Success: {result.success}")
        
        # Read
        print(f"\n📖 Read from {test_file}...")
        result = fs.read_file(test_file, agent_id="demo")
        print(f"   Content: {result.content}")
        
        # Try blocked path
        print("\n🚫 Try reading /etc/passwd...")
        result = fs.read_file("/etc/passwd", agent_id="demo")
        print(f"   Blocked: {not result.success}")
        print(f"   Error: {result.error}")
        
        # Audit log
        print("\n📋 Audit Log:")
        log = fs.get_audit_log(agent_id="demo")
        for entry in log:
            status = "✅" if entry.success else "❌"
            print(f"   {status} {entry.operation.value}: {entry.path}")


async def demo_cognitive_core():
    """Demo: CognitiveCore transformer architecture."""
    print("\n" + "="*60)
    print("🧠 CognitiveCore Demo - Transformer Architecture")
    print("="*60)
    
    from unified_core.cognitive_core import CognitiveCore, CognitiveConfig
    
    # Create small model for demo
    config = CognitiveConfig(
        vocab_size=1000,
        hidden_size=256,
        num_layers=4,
        num_attention_heads=4,
        intermediate_size=512,
        max_position_embeddings=512
    )
    
    model = CognitiveCore(config)
    param_count = model.count_parameters()
    
    print(f"\n📐 Model Configuration:")
    print(f"   Hidden Size: {config.hidden_size}")
    print(f"   Layers: {config.num_layers}")
    print(f"   Attention Heads: {config.num_attention_heads}")
    print(f"   Parameters: {param_count:,}")
    print(f"   RoPE: {config.use_rotary_embeddings}")


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🚀 THE UNIFIED CORE - Feature Demonstrations")
    print("="*60)
    
    await demo_data_router()
    await demo_security_audit()
    await demo_resource_monitor()
    await demo_filesystem()
    await demo_cognitive_core()
    
    print("\n" + "="*60)
    print("✅ All demos completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
