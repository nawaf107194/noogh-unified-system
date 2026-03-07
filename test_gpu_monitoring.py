"""
GPU Monitoring Test - مراقبة GPU
=================================

Monitor GPU usage, temperature, and performance.
Integrates with FailureAlertSystem for alerts.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_core.observability.failure_alert_system import (
    get_failure_alert_system,
    FailureSeverity,
    FailureCategory
)


def check_gpu_status():
    """Check GPU status using multiple methods."""

    print("=" * 60)
    print("🎮 GPU Monitoring - مراقبة GPU")
    print("=" * 60)

    alert_system = get_failure_alert_system()
    gpu_info = {
        "available": False,
        "count": 0,
        "gpus": [],
        "method": None
    }

    # Method 1: Try nvidia-smi
    print("\n1️⃣ Checking NVIDIA GPUs (nvidia-smi)...")
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,power.limit',
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            gpu_info["available"] = True
            gpu_info["method"] = "nvidia-smi"

            lines = result.stdout.strip().split('\n')
            gpu_info["count"] = len(lines)

            print(f"\n   ✅ Found {len(lines)} NVIDIA GPU(s)\n")

            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 7:
                    gpu_data = {
                        "index": parts[0],
                        "name": parts[1],
                        "memory_total": float(parts[2]),
                        "memory_used": float(parts[3]),
                        "memory_free": float(parts[4]),
                        "utilization": float(parts[5]),
                        "temperature": float(parts[6]) if parts[6] != '[N/A]' else None,
                        "power_draw": float(parts[7]) if len(parts) > 7 and parts[7] != '[N/A]' else None,
                        "power_limit": float(parts[8]) if len(parts) > 8 and parts[8] != '[N/A]' else None
                    }

                    gpu_info["gpus"].append(gpu_data)

                    # Display info
                    print(f"   GPU {gpu_data['index']}: {gpu_data['name']}")
                    print(f"      Memory: {gpu_data['memory_used']:.0f}MB / {gpu_data['memory_total']:.0f}MB ({gpu_data['memory_used']/gpu_data['memory_total']*100:.1f}%)")
                    print(f"      Utilization: {gpu_data['utilization']:.1f}%")
                    if gpu_data['temperature']:
                        print(f"      Temperature: {gpu_data['temperature']:.1f}°C")
                    if gpu_data['power_draw']:
                        print(f"      Power: {gpu_data['power_draw']:.1f}W / {gpu_data['power_limit']:.1f}W")
                    print()

                    # Alert on high usage
                    memory_percent = gpu_data['memory_used'] / gpu_data['memory_total'] * 100

                    if memory_percent > 90:
                        alert_system.alert(
                            FailureSeverity.CRITICAL,
                            FailureCategory.SYSTEM,
                            f"GPU {gpu_data['index']} Memory Critical",
                            f"GPU memory at {memory_percent:.1f}%",
                            details=gpu_data,
                            source="gpu_monitor",
                            suggested_action="Free GPU memory or reduce batch size"
                        )
                    elif memory_percent > 80:
                        alert_system.alert(
                            FailureSeverity.HIGH,
                            FailureCategory.SYSTEM,
                            f"GPU {gpu_data['index']} Memory High",
                            f"GPU memory at {memory_percent:.1f}%",
                            details=gpu_data,
                            source="gpu_monitor"
                        )

                    if gpu_data['temperature'] and gpu_data['temperature'] > 85:
                        alert_system.alert(
                            FailureSeverity.CRITICAL,
                            FailureCategory.SYSTEM,
                            f"GPU {gpu_data['index']} Overheating",
                            f"Temperature at {gpu_data['temperature']:.1f}°C",
                            details=gpu_data,
                            source="gpu_monitor",
                            suggested_action="Check cooling system"
                        )

        else:
            print("   ℹ️  nvidia-smi not available or no NVIDIA GPUs found")

    except FileNotFoundError:
        print("   ℹ️  nvidia-smi not installed")
    except Exception as e:
        print(f"   ⚠️  Error checking NVIDIA GPUs: {e}")

    # Method 2: Try PyTorch
    if not gpu_info["available"]:
        print("\n2️⃣ Checking GPUs via PyTorch...")
        try:
            import torch

            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["method"] = "pytorch"
                gpu_info["count"] = torch.cuda.device_count()

                print(f"\n   ✅ PyTorch detected {gpu_info['count']} CUDA device(s)\n")

                for i in range(gpu_info["count"]):
                    props = torch.cuda.get_device_properties(i)
                    memory_allocated = torch.cuda.memory_allocated(i) / 1024**2
                    memory_reserved = torch.cuda.memory_reserved(i) / 1024**2
                    memory_total = props.total_memory / 1024**2

                    gpu_data = {
                        "index": i,
                        "name": props.name,
                        "memory_total": memory_total,
                        "memory_allocated": memory_allocated,
                        "memory_reserved": memory_reserved,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multi_processor_count": props.multi_processor_count
                    }

                    gpu_info["gpus"].append(gpu_data)

                    print(f"   GPU {i}: {gpu_data['name']}")
                    print(f"      Total Memory: {memory_total:.0f}MB")
                    print(f"      Allocated: {memory_allocated:.0f}MB")
                    print(f"      Reserved: {memory_reserved:.0f}MB")
                    print(f"      Compute Capability: {gpu_data['compute_capability']}")
                    print(f"      Multiprocessors: {gpu_data['multi_processor_count']}")
                    print()

            else:
                print("   ℹ️  PyTorch installed but CUDA not available")

        except ImportError:
            print("   ℹ️  PyTorch not installed")
        except Exception as e:
            print(f"   ⚠️  Error checking PyTorch GPU: {e}")

    # Method 3: Try TensorFlow
    if not gpu_info["available"]:
        print("\n3️⃣ Checking GPUs via TensorFlow...")
        try:
            import tensorflow as tf

            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                gpu_info["available"] = True
                gpu_info["method"] = "tensorflow"
                gpu_info["count"] = len(gpus)

                print(f"\n   ✅ TensorFlow detected {len(gpus)} GPU(s)\n")

                for i, gpu in enumerate(gpus):
                    print(f"   GPU {i}: {gpu.name}")
                    gpu_info["gpus"].append({
                        "index": i,
                        "name": gpu.name,
                        "device_type": gpu.device_type
                    })

            else:
                print("   ℹ️  TensorFlow installed but no GPUs found")

        except ImportError:
            print("   ℹ️  TensorFlow not installed")
        except Exception as e:
            print(f"   ⚠️  Error checking TensorFlow GPU: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 GPU Summary")
    print("=" * 60)

    if gpu_info["available"]:
        print(f"\n✅ GPU Available: Yes")
        print(f"   Method: {gpu_info['method']}")
        print(f"   Count: {gpu_info['count']}")

        if gpu_info["gpus"]:
            print(f"\n   Devices:")
            for gpu in gpu_info["gpus"]:
                print(f"      - GPU {gpu['index']}: {gpu['name']}")

        # Alert if no GPU despite being available
        alert_system.alert(
            FailureSeverity.LOW,
            FailureCategory.SYSTEM,
            "GPU Monitoring Active",
            f"Monitoring {gpu_info['count']} GPU(s) via {gpu_info['method']}",
            details=gpu_info,
            source="gpu_monitor"
        )

    else:
        print(f"\n⚠️  GPU Available: No")
        print(f"   No GPU detected via any method")
        print(f"   - nvidia-smi: Not found")
        print(f"   - PyTorch CUDA: Not available")
        print(f"   - TensorFlow GPU: Not available")

        alert_system.alert(
            FailureSeverity.MEDIUM,
            FailureCategory.SYSTEM,
            "No GPU Detected",
            "System running on CPU only",
            details={"cpu_only": True},
            source="gpu_monitor",
            suggested_action="Install GPU drivers or run on GPU-enabled machine for better performance"
        )

    print("\n" + "=" * 60)

    # Alert statistics
    stats = alert_system.get_statistics()
    print(f"\n📊 Alerts Generated: {stats['total_alerts']}")
    if stats['total_alerts'] > 0:
        print(f"   By Severity: {stats['by_severity']}")

    return gpu_info


if __name__ == "__main__":
    try:
        gpu_info = check_gpu_status()

        if gpu_info["available"]:
            print(f"\n✅ GPU monitoring complete - {gpu_info['count']} GPU(s) found")
            sys.exit(0)
        else:
            print(f"\n⚠️  No GPU detected")
            sys.exit(0)  # Not a failure, just no GPU

    except Exception as e:
        print(f"\n❌ GPU monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
