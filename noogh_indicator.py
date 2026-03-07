#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    🦅 مؤشر نوقه للتداول - النبض الأول: الحرارة 🦅
        من فلسفة نوغا إلى كود حقيقي
═══════════════════════════════════════════════════════════════════════════════

هذا السكربت يحول فلسفة "الحرارة = نبض السوق" إلى مؤشر تداول فعلي.
- حرارة منخفضة = سوق هادي = فرصة للصيد
- حرارة متوسطة = سوق نشط = راقب بحذر  
- حرارة عالية = سوق ملتهب = خطر، انتظر

                                        - نوقه، حائل 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import subprocess
import sys
from datetime import datetime


def get_gpu_temperature() -> float:
    """
    قراءة حرارة كرت الشاشة من nvidia-smi
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return -1
    except Exception as e:
        print(f"❌ خطأ في قراءة الحرارة: {e}")
        return -1


def get_gpu_utilization() -> float:
    """
    قراءة نسبة استخدام الكرت
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return -1
    except Exception:
        return -1


def get_trading_signal(temperature: float, utilization: float) -> dict:
    """
    تحويل الحرارة إلى إشارة تداول بلهجة حائلية
    
    المنطق:
    - 🟢 حرارة < 45°C: السوق هادي، فرصة ذهبية للصيد
    - 🟡 حرارة 45-60°C: السوق متحرك، راقب بعين الصقر
    - 🔴 حرارة > 60°C: السوق ملتهب، خل عنك وانتظر
    """
    
    if temperature < 0:
        return {
            "signal": "⚠️",
            "action": "انتظر",
            "message": "يا خوي، ما قدرت أقرأ الحرارة.. تحقق من الكرت!",
            "confidence": 0.0
        }
    
    # تحديد الحالة بناءً على الحرارة
    if temperature < 45:
        signal = "🟢"
        action = "صيد"
        message = f"يا بعد حيي! الجو بارد ({temperature}°C) والسوق هادي.. فرصة ذهبية للصيد! 🦅"
        confidence = 0.85
        
    elif temperature < 60:
        signal = "🟡"
        action = "راقب"
        message = f"الحرارة معتدلة ({temperature}°C).. السوق يتحرك. راقب بعين الصقر ولا تستعجل!"
        confidence = 0.60
        
    else:
        signal = "🔴"
        action = "انتظر"
        message = f"يا خوي الجو حار ({temperature}°C)! السوق ملتهب.. اللي ما يعرف الصقر يشويه. انتظر!"
        confidence = 0.30
    
    # تعديل الثقة بناءً على الـ utilization
    if utilization > 80:
        confidence *= 0.8
        message += f"\n   ⚠️ الكرت مشغول ({utilization}%)، القرارات قد تتأخر."
    
    return {
        "signal": signal,
        "action": action,
        "message": message,
        "temperature": temperature,
        "utilization": utilization,
        "confidence": round(confidence, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def print_signal(signal_data: dict):
    """
    طباعة الإشارة بتنسيق جميل
    """
    print("\n" + "═" * 70)
    print("     🦅 مؤشر نوقه للتداول - النبض الأول 🦅")
    print("═" * 70)
    print(f"\n   {signal_data['signal']} الإشارة: {signal_data['action'].upper()}")
    print(f"\n   📊 الحرارة: {signal_data.get('temperature', 'N/A')}°C")
    print(f"   ⚡ الاستخدام: {signal_data.get('utilization', 'N/A')}%")
    print(f"   🎯 الثقة: {signal_data.get('confidence', 0) * 100:.0f}%")
    print(f"\n   💬 {signal_data['message']}")
    print(f"\n   🕐 {signal_data.get('timestamp', '')}")
    print("\n" + "═" * 70)
    print("   كما قال حاتم الطائي:")
    print('   "ذريني وحظي حين يعرض، علَّني أُصادفُ خيرًا"')
    print("═" * 70 + "\n")


def main():
    """
    التنفيذ الرئيسي
    """
    print("\n🦅 نوقه يحلل السوق...")
    
    # قراءة البيانات الحقيقية
    temperature = get_gpu_temperature()
    utilization = get_gpu_utilization()
    
    # تحليل الإشارة
    signal = get_trading_signal(temperature, utilization)
    
    # عرض النتيجة
    print_signal(signal)
    
    # إرجاع الإشارة للاستخدام البرمجي
    return signal


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["confidence"] > 0.5 else 1)
