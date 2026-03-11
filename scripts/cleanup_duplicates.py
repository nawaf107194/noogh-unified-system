#!/usr/bin/env python3
"""
تنظيف الملفات المكررة من الـ root:
- ملفات timestamp مثل: strategies_1771443770.py
- ملفات .bak و .backup في root
يطبع قائمة الملفات التي سيتم حذفها (dry-run افتراضياً).

الاستخدام:
    python scripts/cleanup_duplicates.py          # dry-run
    python scripts/cleanup_duplicates.py --delete  # حذف فعلي
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

TIMESTAMP_PATTERN = re.compile(r"_(\d{9,10})\.py$")
BACKUP_PATTERNS = ["*.bak", "*.backup", "*.backup_*"]


def find_duplicates(root: Path):
    found = []
    for f in root.iterdir():
        if not f.is_file():
            continue
        if TIMESTAMP_PATTERN.search(f.name):
            found.append(f)
        for pat in BACKUP_PATTERNS:
            if f.match(pat):
                found.append(f)
                break
    return found


def main():
    dry_run = "--delete" not in sys.argv
    duplicates = find_duplicates(ROOT)

    if not duplicates:
        print("✅ لا توجد ملفات مكررة في الـ root.")
        return

    print(f"{'🔍 DRY-RUN' if dry_run else '🗑  حذف'} — {len(duplicates)} ملف(ات):")
    for f in sorted(duplicates):
        print(f"  {f.name}")
        if not dry_run:
            f.unlink()
            print(f"    ✓ حُذف")

    if dry_run:
        print("\nلتنفيذ الحذف الفعلي: python scripts/cleanup_duplicates.py --delete")


if __name__ == "__main__":
    main()
