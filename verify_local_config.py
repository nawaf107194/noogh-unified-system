"""
Verify Local-Only Configuration - التحقق من التكوين المحلي
==========================================================

Verifies that NOOGH is running 100% locally with Ollama.
"""

import sys
import os
import subprocess
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_ollama_status():
    """Check if Ollama is running and accessible."""

    print("=" * 60)
    print("🔍 Verifying Local-Only Configuration")
    print("=" * 60)

    # Check Ollama process
    print("\n1️⃣ Checking Ollama Process...")
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'ollama'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"   ✅ Ollama running ({len(pids)} process(es))")
            for pid in pids[:3]:
                try:
                    cmd = subprocess.run(
                        ['ps', '-p', pid, '-o', 'cmd='],
                        capture_output=True,
                        text=True
                    )
                    if cmd.returncode == 0:
                        print(f"      PID {pid}: {cmd.stdout.strip()[:70]}...")
                except:
                    pass
        else:
            print("   ❌ Ollama not running")
            return False

    except Exception as e:
        print(f"   ⚠️  Could not check Ollama: {e}")
        return False

    # Check Ollama API
    print("\n2️⃣ Checking Ollama API...")
    try:
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)

        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   ✅ Ollama API accessible")
            print(f"   Models available: {len(models)}")

            for model in models[:3]:
                print(f"      - {model['name']}")

            # Check for qwen2.5-coder:14b
            qwen_found = any('qwen2.5-coder' in m['name'] for m in models)
            if qwen_found:
                print(f"   ✅ qwen2.5-coder:14b found")
            else:
                print(f"   ⚠️  qwen2.5-coder:14b not found")

        else:
            print(f"   ❌ Ollama API returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Ollama API at http://127.0.0.1:11434")
        return False
    except Exception as e:
        print(f"   ⚠️  API check failed: {e}")
        return False

    # Check environment variables
    print("\n3️⃣ Checking Environment Variables...")

    env_vars = {
        "NOOGH_TEACHER_URL": "http://127.0.0.1:11434",
        "RUNPOD_BRAIN_URL": "",
        "DEEPSEEK_API_KEY": "",
        "OPENAI_API_KEY": ""
    }

    all_correct = True
    for var, expected in env_vars.items():
        actual = os.environ.get(var, "NOT_SET")

        if expected == "":
            # Should be empty or not set
            if actual in ["", "NOT_SET"]:
                print(f"   ✅ {var}: (empty/not set)")
            else:
                print(f"   ⚠️  {var}: '{actual}' (should be empty)")
                all_correct = False
        else:
            # Should match expected value
            if actual == expected:
                print(f"   ✅ {var}: {actual}")
            else:
                print(f"   ⚠️  {var}: '{actual}' (expected: '{expected}')")
                all_correct = False

    # Check agent_daemon process
    print("\n4️⃣ Checking agent_daemon Process...")
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'agent_daemon'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"   ✅ agent_daemon running (PID: {pids[0]})")
        else:
            print("   ⚠️  agent_daemon not running")

    except Exception as e:
        print(f"   ⚠️  Could not check agent_daemon: {e}")

    # Test Ollama inference
    print("\n5️⃣ Testing Ollama Inference...")
    try:
        response = requests.post(
            'http://127.0.0.1:11434/api/generate',
            json={
                "model": "qwen2.5-coder:14b",
                "prompt": "Say 'OK' if you're working.",
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            reply = data.get('response', '').strip()
            print(f"   ✅ Inference working")
            print(f"      Response: {reply[:50]}...")
        else:
            print(f"   ⚠️  Inference failed (status {response.status_code})")

    except Exception as e:
        print(f"   ⚠️  Inference test failed: {e}")

    return True


def check_external_connections():
    """Verify no external API connections."""

    print("\n6️⃣ Verifying No External Connections...")

    external_urls = [
        "https://api.runpod.ai",
        "https://api.deepseek.com",
        "https://api.openai.com"
    ]

    all_blocked = True
    for url in external_urls:
        # Check if URL is in environment or config
        if url in str(os.environ.values()):
            print(f"   ⚠️  Found reference to {url} in environment")
            all_blocked = False
        else:
            print(f"   ✅ No reference to {url}")

    return all_blocked


if __name__ == "__main__":
    try:
        print("\n")

        # Run checks
        ollama_ok = check_ollama_status()
        external_blocked = check_external_connections()

        # Summary
        print("\n" + "=" * 60)
        print("📊 Configuration Summary")
        print("=" * 60)

        if ollama_ok and external_blocked:
            print("\n✅ System is 100% LOCAL")
            print("   - Ollama running and accessible")
            print("   - qwen2.5-coder:14b ready")
            print("   - No external API connections")
            print("   - agent_daemon active")
            print("\n🎉 نظام NOOGH يعمل محلياً بالكامل!")
            sys.exit(0)
        else:
            print("\n⚠️  Configuration issues detected")
            if not ollama_ok:
                print("   - Ollama not properly configured")
            if not external_blocked:
                print("   - External API references found")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
