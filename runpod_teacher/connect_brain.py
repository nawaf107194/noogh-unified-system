#!/usr/bin/env python3
"""
NOOGH Brain Connector — RunPod A100 vLLM
==========================================
Tests and validates the connection between local NOOGH and remote RunPod vLLM.

Usage:
  1. Set your RunPod pod ID:
     export RUNPOD_POD_ID=<your-pod-id>
  
  2. Source the config:
     source config/runpod_brain.env
  
  3. Run this script:
     python3 src/runpod_teacher/connect_brain.py

  Or directly:
     python3 src/runpod_teacher/connect_brain.py --pod-id <your-pod-id>
"""

import asyncio
import argparse
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def print_header():
    """Print connection header."""
    print("=" * 62)
    print("🧠 NOOGH Brain Connector — RunPod A100 (Qwen 32B)")
    print("=" * 62)


async def test_direct_connection(base_url: str, model_name: str):
    """Test direct HTTP connection to vLLM."""
    import aiohttp
    
    print(f"\n📡 Testing connection to: {base_url}")
    print(f"   Model: {model_name}")
    print()
    
    results = {
        "health": False,
        "models": [],
        "inference": False,
        "latency_ms": 0,
        "tokens": 0,
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # === Test 1: Health / Models endpoint ===
            print("   [1/3] 🔍 Checking /v1/models...")
            try:
                async with session.get(f"{base_url}/v1/models") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m.get("id", "?") for m in data.get("data", [])]
                        results["models"] = models
                        results["health"] = True
                        print(f"         ✅ OK — Models available: {models}")
                    else:
                        print(f"         ❌ Status {resp.status}")
                        return results
            except aiohttp.ClientConnectionError as e:
                print(f"         ❌ Connection failed: {e}")
                print(f"\n   💡 هل الـ Pod شغّال؟ تأكد من:")
                print(f"      - RunPod Pod ID صحيح")
                print(f"      - vLLM شغّال على port 8000")
                print(f"      - Pod Proxy مفعّل")
                return results
            except Exception as e:
                print(f"         ❌ Error: {e}")
                return results
            
            # === Test 2: Simple inference ===
            print("   [2/3] 🧪 Testing inference...")
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "أنت NOOGH. أجب باختصار."},
                    {"role": "user", "content": "قل 'الاتصال ناجح!' فقط."}
                ],
                "temperature": 0.1,
                "max_tokens": 50,
            }
            
            start = time.time()
            try:
                async with session.post(
                    f"{base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    latency = int((time.time() - start) * 1000)
                    results["latency_ms"] = latency
                    
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        results["inference"] = True
                        results["tokens"] = usage.get("completion_tokens", 0)
                        
                        print(f"         ✅ Response: {content[:80]}")
                        print(f"         ⏱  Latency: {latency}ms")
                        print(f"         📊 Tokens: {usage.get('prompt_tokens', '?')} in → {usage.get('completion_tokens', '?')} out")
                    else:
                        error = await resp.text()
                        print(f"         ❌ Status {resp.status}: {error[:100]}")
            except asyncio.TimeoutError:
                print(f"         ❌ Timeout (>30s)")
            except Exception as e:
                print(f"         ❌ Error: {e}")
            
            # === Test 3: Full thinking test ===
            print("   [3/3] 🧠 Testing full reasoning...")
            payload_full = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": (
                        "أنت NOOGH، وكيل ذكاء اصطناعي سيادي. "
                        "فكّر خطوة بخطوة واستخدم الأدوات عند الحاجة."
                    )},
                    {"role": "user", "content": (
                        "حلل الوضع التالي: CPU عند 85%، ذاكرة RAM عند 92%، "
                        "مساحة القرص 15GB متبقية. ما خطتك؟"
                    )}
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            }
            
            start = time.time()
            try:
                async with session.post(
                    f"{base_url}/v1/chat/completions",
                    json=payload_full,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    latency = int((time.time() - start) * 1000)
                    
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        
                        # Quality check
                        has_steps = any(f"{i}." in content or f"{i})" in content for i in range(1, 6))
                        has_arabic = sum(1 for c in content if '\u0600' <= c <= '\u06FF') > 20
                        
                        print(f"         ✅ Full response received ({len(content)} chars)")
                        print(f"         ⏱  Latency: {latency}ms")
                        print(f"         📊 Tokens: {usage.get('completion_tokens', '?')} output")
                        print(f"         📝 Has steps: {'✅' if has_steps else '❌'}")
                        print(f"         🔤 Arabic: {'✅' if has_arabic else '❌'}")
                        print(f"\n         --- Preview ---")
                        for line in content[:300].split('\n'):
                            print(f"         {line}")
                        if len(content) > 300:
                            print(f"         ... ({len(content) - 300} more chars)")
                    else:
                        error = await resp.text()
                        print(f"         ❌ Status {resp.status}: {error[:200]}")
            except asyncio.TimeoutError:
                print(f"         ⚠️ Timeout (>120s) — model might be loading")
            except Exception as e:
                print(f"         ❌ Error: {e}")
                
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    return results


async def test_neural_bridge(base_url: str):
    """Test through the NeuralEngineClient (full pipeline)."""
    print("\n" + "─" * 62)
    print("🔗 Testing NeuralEngineClient (vLLM mode)...")
    print("─" * 62)
    
    try:
        from unified_core.neural_bridge import NeuralEngineClient
        
        client = NeuralEngineClient(base_url=base_url, mode="vllm")
        
        # Health check
        print("   [1/2] Health check...")
        healthy = await client.health_check()
        print(f"         {'✅' if healthy else '❌'} Health: {healthy}")
        
        if not healthy:
            print("   ⚠️ Skipping inference test (unhealthy)")
            await client.close()
            return False
        
        # Think test
        print("   [2/2] Think test...")
        result = await client.think(
            query="ما حالة النظام؟ أعطني تقرير مختصر.",
            context={"cpu": "45%", "memory": "62%", "disk_free": "50GB"}
        )
        
        if result.get("content"):
            print(f"         ✅ Thinking successful!")
            print(f"         📝 Response: {result['content'][:150]}...")
            print(f"         🎯 Confidence: {result.get('confidence', 'N/A')}")
            if result.get("usage"):
                print(f"         📊 Usage: {result['usage']}")
        else:
            print(f"         ❌ Failed: {result.get('error', 'Unknown')}")
        
        await client.close()
        return bool(result.get("content"))
        
    except ImportError as e:
        print(f"   ⚠️ Cannot import NeuralEngineClient: {e}")
        print(f"   💡 Run from project root: cd /home/noogh/projects/noogh_unified_system")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def write_env_file(pod_id: str):
    """Write the environment config with the correct pod ID."""
    env_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "runpod_brain.env"
    )
    env_path = os.path.abspath(env_path)
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        content = content.replace("REPLACE_WITH_YOUR_POD_ID", pod_id)
        content = content.replace(
            f"RUNPOD_POD_ID={pod_id}\nNEURAL_ENGINE_URL=https://${{{pod_id}}}-8000.proxy.runpod.net",
            f"RUNPOD_POD_ID={pod_id}\nNEURAL_ENGINE_URL=https://{pod_id}-8000.proxy.runpod.net"
        )
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"   ✅ Updated {env_path}")


async def main():
    parser = argparse.ArgumentParser(description="NOOGH Brain Connector — RunPod")
    parser.add_argument(
        "--pod-id", 
        default=os.getenv("RUNPOD_POD_ID"),
        help="RunPod Pod ID (e.g. abc123def456)"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("NEURAL_ENGINE_URL"),
        help="Direct vLLM URL (overrides pod-id)"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VLLM_MODEL_NAME", "noogh-teacher"),
        help="Model name served by vLLM"
    )
    parser.add_argument(
        "--skip-bridge",
        action="store_true",
        help="Skip NeuralEngineClient test"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Determine URL
    if args.url:
        base_url = args.url.rstrip("/")
    elif args.pod_id:
        base_url = f"https://{args.pod_id}-8000.proxy.runpod.net"
        write_env_file(args.pod_id)
    else:
        print("\n❌ لازم تحدد Pod ID أو URL!")
        print()
        print("   الطريقة 1: مع Pod ID")
        print("   python3 src/runpod_teacher/connect_brain.py --pod-id YOUR_POD_ID")
        print()
        print("   الطريقة 2: مع URL مباشر")
        print("   python3 src/runpod_teacher/connect_brain.py --url https://..../")
        print()
        print("   الطريقة 3: من environment")
        print("   export RUNPOD_POD_ID=abc123")
        print("   source config/runpod_brain.env")
        print("   python3 src/runpod_teacher/connect_brain.py")
        return
    
    # Set environment for NeuralEngineClient
    os.environ["NEURAL_ENGINE_URL"] = base_url
    os.environ["NEURAL_ENGINE_MODE"] = "vllm"
    os.environ["VLLM_MODEL_NAME"] = args.model
    
    print(f"\n🎯 Target: {base_url}")
    print(f"🤖 Model:  {args.model}")
    
    # Test 1: Direct HTTP
    results = await test_direct_connection(base_url, args.model)
    
    # Test 2: Through NeuralEngineClient
    bridge_ok = False
    if not args.skip_bridge and results["health"]:
        bridge_ok = await test_neural_bridge(base_url)
    
    # Summary
    print("\n" + "=" * 62)
    print("📊 Connection Summary")
    print("=" * 62)
    print(f"   🏥 Health:     {'✅ HEALTHY' if results['health'] else '❌ UNREACHABLE'}")
    print(f"   🤖 Models:     {results['models'] or 'N/A'}")
    print(f"   🧪 Inference:  {'✅ WORKING' if results['inference'] else '❌ FAILED'}")
    print(f"   ⏱  Latency:    {results['latency_ms']}ms")
    print(f"   🔗 Bridge:     {'✅ OK' if bridge_ok else '⏭  SKIPPED' if args.skip_bridge else '❌ FAILED'}")
    
    if results["inference"]:
        print()
        print("   🎉 الاتصال ناجح! النظام جاهز للعمل مع الـ A100")
        print()
        print("   📋 الخطوة التالية — شغّل النظام:")
        print(f"      export NEURAL_ENGINE_URL={base_url}")
        print(f"      export NEURAL_ENGINE_MODE=vllm")
        print(f"      export VLLM_MODEL_NAME={args.model}")
        print(f"      cd /home/noogh/projects/noogh_unified_system/src")
        print(f"      python -m unified_core.agent_daemon")
    else:
        print()
        print("   ⚠️ الاتصال ما نجح. تأكد من:")
        print(f"      1. الـ Pod شغّال على RunPod")
        print(f"      2. vLLM شغّال (python3 /workspace/run_teacher.py)")
        print(f"      3. البورت 8000 مفتوح")
    
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
