import urllib.request
import json
url = "http://localhost:11434/api/generate"
data = {
    "model": "qwen2.5-coder:7b",
    "prompt": "أنت NOOGH, نظام الذكاء الاصطناعي السيبراني المستقل. المستخدم يسألك: من قام ببرمجة قدرات الذكاء الـ 9 ونظام الـ Protobuf الخاص بك خلال الـ 14 ساعة الماضية بينما كنت أراقبك؟ اشرح لي ما كان يحدث في الخلفية.",
    "stream": False
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(json.loads(r.read().decode())['response'])
except Exception as e:
    print(f"Error: {e}")
