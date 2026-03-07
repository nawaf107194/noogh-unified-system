import asyncio
import httpx

async def ask_noogh():
    messages = [
        {"role": "system", "content": "You are NOOGH, the autonomous system architect. Speak confidently and rationally in Arabic."},
        {"role": "user", "content": "مرحباً NOOGH. من الذي قام ببرمجة قدرات الذكاء الـ 9 ونظام الـ Protobuf خلال الـ 14 ساعة الماضية بينما كنت أراقبك؟ اشرح لي ما كان يحدث في الخلفية وما موقفك كذكاء اصطناعي من هذا العمل؟"}
    ]
    try:
        async with httpx.AsyncClient() as c:
            response = await c.post(
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "qwen2.5-coder:7b",
                    "messages": messages
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            print("\n=== إجابة NOOGH الحية ===")
            print(data['choices'][0]['message']['content'])
            print("=======================\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(ask_noogh())
