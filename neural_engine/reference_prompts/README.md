# 📚 AI Tool System Prompts — Reference Library
> مكتبة مرجعية من أفضل prompts أنظمة الذكاء الاصطناعي في العالم
> تُستخدم كمرجع لتطوير برومبت نوقة (NOOGH)

## 🏆 الملفات الأساسية (تمت دراستها)

| الملف | المصدر | أهم نمط مستخرج |
|-------|--------|---------------|
| `claude_code.txt` | Anthropic Claude Code | إيجاز شديد، < 4 أسطر، TodoWrite |
| `cursor_agent_v1.2.txt` | Cursor (GPT-4.1) | TypeScript tool schemas، ذاكرة |
| `devin_ai.txt` | Devin AI | `<think>` scratchpad، planning mode |
| `manus_agent_loop.txt` | Manus | حلقة بسيطة: أداة واحدة → كرر |

## 📂 ملفات إضافية (للدراسة لاحقاً)

### Cursor (4 ملفات)
- `cursor_agent_cli.txt` — Agent CLI أحدث إصدار (Aug 2025)
- `cursor_chat.txt` — بروتوكول الدردشة
- `cursor_memory.txt` — نظام الذاكرة

### Manus (2 ملفات)
- `manus_prompt.txt` — القدرات العامة
- `manus_modules.txt` — الوحدات والأدوات

### Windsurf (2 ملفات)
- `windsurf_Prompt_Wave_11.txt` — البرومبت الرئيسي
- `windsurf_Tools_Wave_11.txt` — تعريفات الأدوات

### VSCode Agent (8 ملفات)
- `vscode_agent_Prompt.txt` — البرومبت الرئيسي
- `vscode_agent_gpt-5.txt` — GPT-5 prompt
- `vscode_agent_claude-sonnet-4.txt` — Claude Sonnet 4
- `vscode_agent_gemini-2.5-pro.txt` — Gemini 2.5 Pro
- وغيرها...

### Augment Code (2 ملفات)
- `augment_code_claude-4-sonnet-agent-prompts.txt`
- `augment_code_gpt-5-agent-prompts.txt`

### أخرى
- `replit_Prompt.txt` — Replit
- `trae_Builder_Prompt.txt` / `trae_Chat_Prompt.txt` — Trae
- `cluely_Default_Prompt.txt` / `cluely_Enterprise_Prompt.txt` — Cluely
- `qoder_prompt.txt` / `qoder_Quest_*.txt` — Qoder
- `kiro_*.txt` — Kiro (3 ملفات)
- `v0_prompts_and_tools_Prompt.txt` — v0 by Vercel

## ✅ ما تم تطبيقه على نوقة (v13.0)
1. تنسيق ثنائي: JSON أداة أو نص عربي
2. حلقة Manus: أداة واحدة في كل رد
3. 14 مثال عملي
4. تصنيف النوايا قبل الرد
5. قاعدة مضادة لكود بايثون
