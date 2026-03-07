#!/bin/bash
# NOOGH Autonomous Learner Wrapper
# يضمن التشغيل دائماً من البيئة الافتراضية الصحيحة

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV="$PROJECT_ROOT/.venv"

# تفعيل البيئة الافتراضية
if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
else
    echo "❌ Virtual environment not found at: $VENV"
    exit 1
fi

# تشغيل السكريبت مع جميع المعاملات
python3 "$SCRIPT_DIR/autonomous_learner_agent.py" "$@"
