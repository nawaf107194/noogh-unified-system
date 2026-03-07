#!/usr/bin/env python3
"""
NOOGH Dataset Expansion Script V2
===================================
Downloads diverse datasets from HuggingFace (Parquet-based, fast)
and merges with existing V6 dataset.

Target: 200K+ samples
"""

import os
import json
import random
import traceback
from pathlib import Path
from datasets import load_dataset

OUTPUT_DIR = Path(__file__).parent / "training_data"
EXISTING_DATASET = OUTPUT_DIR / "NOOGH_V6_DATASET.jsonl"
FINAL_OUTPUT = OUTPUT_DIR / "NOOGH_V7_EXPANDED.jsonl"

SYSTEM_PROMPT = "You are NOOGH, an advanced hybrid AI system. You excel at creative thinking, deep analysis, and solving complex problems."


def to_messages(system, user, assistant, category):
    """Helper to create standard messages format."""
    if not user or not assistant or len(assistant) < 10:
        return None
    return {
        "messages": [
            {"role": "system", "content": system or SYSTEM_PROMPT},
            {"role": "user", "content": user[:3000]},
            {"role": "assistant", "content": assistant[:4000]},
        ],
        "category": category,
    }


def download_and_convert(name, hf_id, max_samples, category, converter, split="train", config=None):
    """Download a dataset and convert to standard format."""
    print(f"\n📥 {name} ({hf_id}) — max {max_samples}")
    
    try:
        kwargs = {"split": split}
        if config:
            kwargs["name"] = config
        
        ds = load_dataset(hf_id, streaming=True, **kwargs)
        
        results = []
        errors = 0
        for i, sample in enumerate(ds):
            if len(results) >= max_samples:
                break
            try:
                result = converter(sample)
                if result:
                    results.append(result)
            except Exception:
                errors += 1
                if errors > 200:
                    break
        
        print(f"   ✅ {len(results):,} samples (skipped: {errors})")
        return results
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        traceback.print_exc()
        return []


# ============================================================================
# DATASET CONVERTERS
# ============================================================================

def conv_slimorca(s):
    """SlimOrca — high quality instruction following."""
    convs = s.get("conversations", [])
    if len(convs) < 2:
        return None
    system = SYSTEM_PROMPT
    user = assistant = ""
    for c in convs:
        r = c.get("from", "")
        v = c.get("value", "")
        if r == "system": system = v
        elif r == "human": user = v
        elif r == "gpt": assistant = v
    return to_messages(system, user, assistant, "general")


def conv_metamath(s):
    """MetaMathQA — math reasoning."""
    return to_messages(SYSTEM_PROMPT, s.get("query",""), s.get("response",""), "math")


def conv_code_alpaca(s):
    """CodeAlpaca — coding instructions."""
    inst = s.get("instruction", "")
    inp = s.get("input", "")
    out = s.get("output", "")
    user = f"{inst}\n{inp}".strip() if inp else inst
    return to_messages(SYSTEM_PROMPT, user, out, "code")


def conv_alpaca_ar(s):
    """Arabic Alpaca."""
    inst = s.get("instruction", "")
    inp = s.get("input", "")
    out = s.get("output", "")
    user = f"{inst}\n{inp}".strip() if inp else inst
    return to_messages(SYSTEM_PROMPT, user, out, "arabic")


def conv_sciq(s):
    """SciQ — science questions."""
    q = s.get("question", "")
    a = s.get("correct_answer", "")
    sup = s.get("support", "")
    answer = f"{a}\n\n{sup}" if sup else a
    return to_messages(SYSTEM_PROMPT, q, answer, "science")


def conv_ultrachat(s):
    """UltraChat — multi-turn conversations."""
    msgs = s.get("messages", [])
    if len(msgs) < 2:
        return None
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in msgs[:6]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:2000]})
    
    if len(messages) < 3:
        return None
    return {"messages": messages, "category": "conversation"}


def conv_dolly(s):
    """Dolly 15K — diverse instructions."""
    inst = s.get("instruction", "")
    ctx = s.get("context", "")
    resp = s.get("response", "")
    user = f"{inst}\n\nContext: {ctx}" if ctx else inst
    cat = s.get("category", "general")
    return to_messages(SYSTEM_PROMPT, user, resp, cat)


def conv_no_robots(s):
    """No Robots — human-written high quality."""
    msgs = s.get("messages", [])
    if len(msgs) < 2:
        return None
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in msgs:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    
    if len(messages) < 3:
        return None
    cat = s.get("category", "general")
    return {"messages": messages, "category": cat}


def conv_oasst(s):
    """OpenAssistant — community conversations."""
    text = s.get("text", "")
    role = s.get("role", "")
    
    # OASST is tree-structured, we need parent context
    # Simplified: treat as instruction
    if role == "prompter":
        return None  # Skip prompter-only entries
    return None  # Complex format, skip


def conv_orca_math(s):
    """Orca Math — math word problems."""
    q = s.get("question", "")
    a = s.get("answer", "")
    return to_messages(SYSTEM_PROMPT, q, a, "math")


def conv_magicoder(s):
    """Magicoder — code generation."""
    problem = s.get("problem", s.get("instruction", ""))
    solution = s.get("solution", s.get("response", ""))
    return to_messages(SYSTEM_PROMPT, problem, solution, "code")


def conv_evol_instruct(s):
    """Evol Instruct — evolved instructions."""
    inst = s.get("instruction", "")
    out = s.get("output", "")
    return to_messages(SYSTEM_PROMPT, inst, out, "reasoning")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("🚀 NOOGH Dataset Expansion V2 — Target: 200K+")
    print("=" * 60)
    
    all_samples = []
    
    # 1. Load existing V6
    if EXISTING_DATASET.exists():
        print(f"\n📂 Loading V6: {EXISTING_DATASET}")
        with open(EXISTING_DATASET, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_samples.append(json.loads(line))
                    except:
                        continue
        print(f"   ✅ {len(all_samples):,} existing samples")
    
    # 2. Download datasets
    datasets_to_download = [
        # (name, hf_id, max, category, converter, split, config)
        ("SlimOrca", "Open-Orca/SlimOrca", 30000, "general", conv_slimorca, "train", None),
        ("MetaMathQA", "meta-math/MetaMathQA", 20000, "math", conv_metamath, "train", None),
        ("CodeAlpaca 20K", "sahil2801/CodeAlpaca-20k", 18000, "code", conv_code_alpaca, "train", None),
        ("Dolly 15K", "databricks/databricks-dolly-15k", 15000, "general", conv_dolly, "train", None),
        ("UltraChat 200K", "HuggingFaceH4/ultrachat_200k", 25000, "conversation", conv_ultrachat, "train_sft", None),
        ("No Robots", "HuggingFaceH4/no_robots", 9000, "general", conv_no_robots, "train", None),
        ("SciQ", "allenai/sciq", 12000, "science", conv_sciq, "train", None),
        ("Orca Math", "microsoft/orca-math-word-problems-200k", 20000, "math", conv_orca_math, "train", None),
        ("Magicoder Evol", "ise-uiuc/Magicoder-Evol-Instruct-110K", 20000, "code", conv_magicoder, "train", None),
        ("Evol Instruct", "WizardLMTeam/WizardLM_evol_instruct_V2_196k", 20000, "reasoning", conv_evol_instruct, "train", None),
    ]
    
    for name, hf_id, max_s, cat, converter, split, config in datasets_to_download:
        results = download_and_convert(name, hf_id, max_s, cat, converter, split, config)
        all_samples.extend(results)
        print(f"   📊 Running total: {len(all_samples):,}")
    
    # 3. Stats
    print(f"\n{'=' * 60}")
    print(f"📊 Total: {len(all_samples):,} samples")
    
    categories = {}
    for s in all_samples:
        cat = s.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📁 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(all_samples)
        print(f"   {cat:25s}: {count:>7,}  ({pct:.1f}%)")
    
    # 4. Shuffle & save
    random.seed(42)
    random.shuffle(all_samples)
    
    print(f"\n💾 Saving: {FINAL_OUTPUT}")
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    size_mb = FINAL_OUTPUT.stat().st_size / 1e6
    print(f"   ✅ {len(all_samples):,} samples — {size_mb:.1f} MB")
    print(f"\n🎯 NOOGH V7 Dataset ready for cloud training!")


if __name__ == "__main__":
    main()
