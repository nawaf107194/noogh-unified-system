"""
NOOGH Reasoning Engine v4.7 - Hybrid Sovereign Logic (Local + Cloud)
"""

import logging
import os
import re
# import torch  # Moved inside methods
import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from neural_engine.model_authority import get_model_authority, ModelState
from neural_engine.tools.tool_executor import get_tool_executor
from neural_engine.tools.tool_call_parser import ToolCallParser
from unified_core.auth import get_full_admin_auth
from neural_engine.cognitive_trace import get_trace_manager, TraceEventType

from .identity_v12_9 import SOVEREIGN_SYSTEM_PROMPT as SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# --- Configuration Management ---
class SystemConfig:
    # استخدام os.getcwd() كخيار افتراضي أكثر أماناً في البيئات المتغيرة
    PROJECT_ROOT = os.getenv("NOOGH_PROJECT_ROOT", os.getcwd())
    MAX_ITERATIONS = 4 # زيادة المحاولات لمنهجية ReAct v12.9
    MAX_CTX_LENGTH = 4096
    DEFAULT_MODEL = "google/gemma-3n-E4B-it"

class ReasoningResult(BaseModel):
    conclusion: str
    confidence: float
    reasoning_trace: List[str]
    suggested_actions: List[str]
    raw_response: Optional[str] = None
    iterations: int = 1
    tool_calls: List[Dict[str, Any]] = []

class ReasoningEngine:
    def __init__(self, backend: str = "auto", model_name: str = None, use_gpu: bool = True, api_key: Optional[str] = None, model: Any = None, tokenizer: Any = None):
        # تحديد الباكيند بذكاء
        self.model = model
        self.tokenizer = tokenizer
        
        # Explicit Detection from Model Object
        is_gguf = False
        try:
            from llama_cpp import Llama
            if isinstance(model, Llama):
                is_gguf = True
        except ImportError:
            pass

        if is_gguf:
            self.backend = "gguf"
        elif backend == "auto":
            import torch
            self.backend = "local-gpu" if torch.cuda.is_available() else "openai"
        else:
            self.backend = backend
            
        import torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        logger.info(f"🧠 ReasoningEngine v4.8 (Sovereign v12.9) initialized with [{self.backend.upper()}]")

    # --- ENHANCED SYSTEM PROMPT ---
    # مستمد من identity_v12_9.py
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def _prune_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        DYNAMIC CONTEXT PRUNING (v12.9 Efficiency Layer)
        Maintains context hygiene by keeping system prompt (Index 0)
        and recent history.
        """
        if len(messages) <= 5:
            return messages
            
        # نضمن دائماً الحفاظ على الرسالة الأولى (SYSTEM PROMPT المفروم والمسحوق)
        pruned = [messages[0]]
        
        # إضافة فاصل سياقي
        pruned.append({
            "role": "system", 
            "content": "... [سياق مقتطع للتحسين] ..."
        })
        
        # الاحتفاظ بآخر 4 رسائل لضمان ترابط الحوار
        pruned.extend(messages[-4:])
        
        return pruned

    async def process(self, messages: List[Dict[str, str]], pre_fill: str = "") -> str:
        """
        Main Dispatcher: يوزع الطلب بناءً على نوع الباكيند مع الحقن الصامت.
        """
        # التأكد من وجود برومبت النظام في البداية (Silent Injection)
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.SYSTEM_PROMPT})
        elif "نوقة" not in messages[0].get("content", ""):
            messages[0] = {"role": "system", "content": self.SYSTEM_PROMPT}

        # Apply Dynamic Context Pruning
        pruned_messages = self._prune_history(messages)
        
        # --- Core Dynamic Dispatcher (v12.9.3 Hybrid Layer) ---
        authority = get_model_authority()
        active_model = self.model or authority.loaded_model
        
        is_gguf_instance = False
        try:
            from llama_cpp import Llama
            if isinstance(active_model, Llama):
                is_gguf_instance = True
        except ImportError:
            pass

        # Priority 1: Direct Type Detection
        if is_gguf_instance or self.backend == "gguf":
            return await asyncio.to_thread(self._process_gguf, pruned_messages, pre_fill)
        
        # Priority 2: Configured Backend
        elif self.backend == "local-gpu":
            return await asyncio.to_thread(self._process_local_gpu, pruned_messages, pre_fill)
        elif self.backend == "openai":
            return await self._process_openai(pruned_messages, pre_fill)
            
        return "❌ Error: Backend not configured."

    async def raw_process(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """
        Direct LLM completion WITHOUT system prompt injection or response normalization.
        Used for code generation tasks where the caller provides their own system prompt.
        """
        authority = get_model_authority()
        active_model = self.model or authority.loaded_model

        is_gguf_instance = False
        try:
            from llama_cpp import Llama
            if isinstance(active_model, Llama):
                is_gguf_instance = True
        except ImportError:
            pass

        if is_gguf_instance or self.backend == "gguf":
            return await asyncio.to_thread(self._raw_process_gguf, messages, max_tokens)
        elif self.backend == "local-gpu":
            return await asyncio.to_thread(self._raw_process_local_gpu, messages, max_tokens)
        elif self.backend == "openai":
            return await self._process_openai(messages, "")

        return "❌ Error: Backend not configured."

    def _raw_process_local_gpu(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """
        Raw GPU completion for code generation - NO system prompt injection.
        Caller provides their own system prompt in messages.
        """
        import torch
        from transformers import LogitsProcessorList, LogitsProcessor
        
        # MINIMAL FIX: Only handle inf/nan, don't modify distribution
        class MinimalLogitsSafetyProcessor(LogitsProcessor):
            """Minimal processor - only replaces inf/nan without affecting distribution."""
            def __call__(self, input_ids, scores):
                # Only replace inf/nan with large negative value
                mask = torch.isinf(scores) | torch.isnan(scores)
                if mask.any():
                    logger.warning(f"⚠️ Found {mask.sum().item()} inf/nan logits, replacing...")
                    scores = torch.where(
                        mask, 
                        torch.tensor(-100.0, device=scores.device, dtype=scores.dtype), 
                        scores
                    )
                return scores
        
        authority = get_model_authority()
        if authority.state != ModelState.LOADED:
            authority.load_model(backend="local-gpu", model_name=os.getenv("NOOGH_MODEL", SystemConfig.DEFAULT_MODEL))
        
        model = authority.loaded_model
        tokenizer = authority.loaded_tokenizer
        
        # Copy messages to avoid modifying original
        msgs_copy = [m.copy() for m in messages]
        
        # Convert system messages to user context (Gemma 2 compatibility)
        system_content = ""
        filtered_msgs = []
        for msg in msgs_copy:
            if msg['role'] == 'system':
                system_content += msg['content'] + "\n"
            else:
                filtered_msgs.append(msg)
        
        # Ensure at least one user message
        if not filtered_msgs:
            filtered_msgs = [{"role": "user", "content": system_content or "Hi"}]
        elif system_content and filtered_msgs[0]['role'] == 'user':
            # Prepend system content to first user message
            filtered_msgs[0]['content'] = f"{system_content.strip()}\n\n{filtered_msgs[0]['content']}"
        
        # Convert 'assistant' to 'model' for Gemma
        for msg in filtered_msgs:
            if msg['role'] == 'assistant':
                msg['role'] = 'model'
        
        # Apply chat template
        try:
            prompt = tokenizer.apply_chat_template(filtered_msgs, tokenize=False, add_generation_prompt=True)
        except Exception as e:
            logger.error(f"Chat template error: {e}")
            # Fallback to manual Gemma format
            prompt = ""
            for msg in filtered_msgs:
                role = msg['role']
                content = msg['content']
                prompt += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
            prompt += "<start_of_turn>model\n"
        
        import torch
        
        # Tokenize with safety checks
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=SystemConfig.MAX_CTX_LENGTH)
        
        # CRITICAL: Validate token IDs before sending to GPU
        vocab_size = model.config.vocab_size if hasattr(model, 'config') else len(tokenizer)
        max_token_id = inputs['input_ids'].max().item()
        
        if max_token_id >= vocab_size:
            logger.error(f"🚨 CRITICAL: Token ID {max_token_id} >= vocab_size {vocab_size}!")
            logger.error(f"Prompt causing issue: {prompt[:200]}")
            # Clamp to safe range
            inputs['input_ids'] = inputs['input_ids'].clamp(max=vocab_size - 1)
            logger.warning(f"✅ Clamped token IDs to safe range")
        
        inputs = inputs.to(model.device)
        
        # Generate with error recovery
        generated_text = ""
        for attempt in range(2):
            try:
                # Create minimal logits processor
                logits_processor = LogitsProcessorList([MinimalLogitsSafetyProcessor()])
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=min(max_tokens, 512),
                        do_sample=True,
                        temperature=1.0,  # Default temperature
                        top_p=0.9,
                        top_k=50,
                        repetition_penalty=1.05,
                        logits_processor=logits_processor,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id,
                    )
                
                generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                logger.info(f"✅ Raw completion successful ({len(generated_text)} chars)")
                break
                
            except RuntimeError as cuda_err:
                if "CUDA" in str(cuda_err) or "device-side assert" in str(cuda_err):
                    logger.error(f"🔥 CUDA Error (attempt {attempt+1}/2): {cuda_err}")
                    torch.cuda.synchronize()
                    torch.cuda.empty_cache()
                    
                    if attempt == 0:
                        logger.info("🔄 Retrying with minimal tokens...")
                        try:
                            with torch.no_grad():
                                outputs = model.generate(
                                    **inputs,
                                    max_new_tokens=64,
                                    temperature=0.3,
                                    do_sample=False,
                                    pad_token_id=tokenizer.eos_token_id,
                                )
                            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                            logger.info(f"✅ Retry successful")
                            break
                        except Exception as retry_err:
                            logger.error(f"🔥 Retry failed: {retry_err}")
                            generated_text = "Error: GPU processing failed. Please try again."
                    else:
                        generated_text = "Error: GPU processing failed after retries."
                else:
                    raise
        
        return generated_text.strip()

    def _raw_process_gguf(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """Direct GGUF completion without normalization — preserves code blocks."""
        authority = get_model_authority()
        if authority.state != ModelState.LOADED:
            authority.load_model(backend="gguf", model_name=os.getenv("NOOGH_MODEL"))

        model = authority.loaded_model

        prompt = ""
        pre_fill_content = ""
        
        for i, msg in enumerate(messages):
            role = msg["role"]
            content = msg["content"]
            is_last = (i == len(messages) - 1)
            
            if role == "system":
                prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                if is_last:
                    # Last assistant message = pre-fill (don't close it)
                    pre_fill_content = content
                else:
                    prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"

        # Start assistant turn with pre-fill
        prompt += "<|im_start|>assistant\n" + pre_fill_content

        logger.info(f"RAW_COMPLETE prompt ({len(prompt)} chars), pre_fill: {len(pre_fill_content)} chars")

        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.9,
            repeat_penalty=1.15,
            stop=["<|im_end|>"]
        )

        generated = response["choices"][0]["text"]
        logger.info(f"RAW_COMPLETE output ({len(generated)} chars): {generated[:100]}")
        return generated.strip()

    def _normalize_response(self, generated_part: str, pre_fill: str = "") -> str:
        """
        Guardrail: Sovereign Normalization Layer (v12.9.2)
        Ensures consistent persona, language, and script safety.
        """
        # 1. Force Arabic Persona Markers
        generated_part = re.sub(r"نوقة\s*\([^)]+\):", "نوقة (تفكير):", generated_part)
        generated_part = re.sub(r"ノoque\s*\([^)]+\):", "نوقة (تفكير):", generated_part)
        generated_part = re.sub(r"القر[آا]ن\s*\(JSON\):", "القرار (JSON):", generated_part)
        
        # 2. Correct common english leaks
        generated_part = generated_part.replace("thinkable", "تفكير")
        generated_part = generated_part.replace("tinghaming", "تفكير")
        generated_part = generated_part.replace("thinking", "تفكير")
        
        # 3. Aggressive Script Scrubbing (Multi-Language Block)
        hallucination_pattern = r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u0590-\u05ff\u0400-\u04ff\uff00-\uffef\uac00-\ud7af]'
        if re.search(hallucination_pattern, generated_part):
            logger.warning("🚨 Hallucination scripts detected! Scrubbing...")
            generated_part = re.sub(hallucination_pattern, '', generated_part)
            
        return (pre_fill or "") + generated_part.strip()

    # ---------------------------------------------------------
    # 1. Local GPU Handler (HuggingFace / Unsloth)
    # ---------------------------------------------------------
    def _process_local_gpu(self, messages: List[Dict[str, str]], pre_fill: str = "") -> str:
        authority = get_model_authority()
        if authority.state != ModelState.LOADED:
            authority.load_model(backend="local-gpu", model_name=os.getenv("NOOGH_MODEL", SystemConfig.DEFAULT_MODEL))
        
        model = authority.loaded_model
        tokenizer = authority.loaded_tokenizer
        
        # نسخ الرسائل لتجنب تعديل الأصل
        msgs_copy = [m.copy() for m in messages]
        
        # CRITICAL FIX: Gemma 2 doesn't support 'system' role in chat template
        # Convert system messages: merge into first user message as context
        system_content = ""
        filtered_msgs = []
        for msg in msgs_copy:
            if msg['role'] == 'system':
                system_content += msg['content'] + "\n"
            else:
                filtered_msgs.append(msg)
        
        # If no system prompt was in messages, add the default one
        if not system_content:
            system_content = self.SYSTEM_PROMPT
        
        # Ensure there's at least one user message
        if not filtered_msgs:
            filtered_msgs = [{"role": "user", "content": "مرحبا"}]
        
        # Prepend system content to first user message
        if filtered_msgs[0]['role'] == 'user':
            filtered_msgs[0]['content'] = f"[System Instructions]\n{system_content.strip()}\n[End Instructions]\n\n{filtered_msgs[0]['content']}"
        else:
            # Insert a user message with system content before other messages
            filtered_msgs.insert(0, {"role": "user", "content": system_content.strip()})
            # Gemma requires alternating user/model turns, so add a model ack
            filtered_msgs.insert(1, {"role": "model", "content": "فهمت. أنا جاهز."})
        
        # Gemma uses 'model' instead of 'assistant'
        for msg in filtered_msgs:
            if msg['role'] == 'assistant':
                msg['role'] = 'model'
        
        try:
            prompt = tokenizer.apply_chat_template(filtered_msgs, tokenize=False, add_generation_prompt=True)
            logger.info(f"DEBUG_MODEL_PROMPT (first 200 chars): {prompt[:200]}")
        except Exception as e:
            logger.error(f"Templating Error: {e}")
            # Manual Gemma 2 format fallback
            prompt = ""
            for msg in filtered_msgs:
                role = msg['role']
                content = msg['content']
                prompt += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
            prompt += "<start_of_turn>model\n"
            logger.info(f"Using manual Gemma template fallback")

        # Smart Pre-fill Injection
        if pre_fill:
            for eos in ["<end_of_turn>", "<eos>", "<|im_end|>", "</s>", "<|endoftext|>"]:
                if prompt.strip().endswith(eos):
                    prompt = prompt.strip()[:-len(eos)]
            prompt += pre_fill
        
        import torch
        
        # Validate input token IDs are within vocab range
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=SystemConfig.MAX_CTX_LENGTH)
        vocab_size = model.config.vocab_size if hasattr(model, 'config') else len(tokenizer)
        max_token_id = inputs['input_ids'].max().item()
        if max_token_id >= vocab_size:
            logger.warning(f"⚠️ Token ID {max_token_id} >= vocab_size {vocab_size}! Clamping...")
            inputs['input_ids'] = inputs['input_ids'].clamp(max=vocab_size - 1)
        
        inputs = inputs.to(model.device)
        
        # Generate with CUDA error recovery
        generated_part = ""
        for attempt in range(2):
            try:
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs, 
                        max_new_tokens=512,
                        temperature=0.5,
                        top_p=0.9,
                        repetition_penalty=1.2,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id,
                        stop_strings=["Observation:", "User:", "<end_of_turn>", "<|im_end|>", "Assistant:"] if hasattr(tokenizer, 'decode') else None,
                        tokenizer=tokenizer
                    )
                
                generated_part = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                logger.info(f"DEBUG_MODEL_RAW: {generated_part}")
                break  # Success
                
            except RuntimeError as cuda_err:
                if "CUDA" in str(cuda_err) or "device-side assert" in str(cuda_err):
                    logger.error(f"🔥 CUDA Error (attempt {attempt+1}/2): {cuda_err}")
                    # Reset CUDA state
                    torch.cuda.synchronize()
                    torch.cuda.empty_cache()
                    if attempt == 0:
                        logger.info("🔄 Retrying with reduced max_tokens...")
                        # Retry with smaller output
                        try:
                            with torch.no_grad():
                                outputs = model.generate(
                                    **inputs,
                                    max_new_tokens=128,
                                    temperature=0.3,
                                    do_sample=True,
                                    pad_token_id=tokenizer.eos_token_id,
                                )
                            generated_part = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                            logger.info(f"DEBUG_MODEL_RAW (retry): {generated_part}")
                            break
                        except Exception as retry_err:
                            logger.error(f"🔥 Retry also failed: {retry_err}")
                            torch.cuda.synchronize()
                            torch.cuda.empty_cache()
                            generated_part = "عذراً، حدث خطأ في وحدة المعالجة الرسومية. يرجى المحاولة مرة أخرى بعد قليل."
                    else:
                        generated_part = "عذراً، حدث خطأ في وحدة المعالجة الرسومية. يرجى المحاولة مرة أخرى بعد قليل."
                else:
                    raise
        
        # Guardrail: Sovereign Normalization Layer (v12.9.2)
        # 1. Force Arabic Persona Markers
        generated_part = re.sub(r"نوقة\s*\([^)]+\):", "نوقة (تفكير):", generated_part)
        generated_part = re.sub(r"ノoque\s*\([^)]+\):", "نوقة (تفكير):", generated_part)
        generated_part = re.sub(r"القر[آا]ن\s*\(JSON\):", "القرار (JSON):", generated_part)
        
        # 2. Correct common english leaks
        generated_part = generated_part.replace("thinkable", "تفكير")
        generated_part = generated_part.replace("tinghaming", "تفكير")
        generated_part = generated_part.replace("thinking", "تفكير")
        
        # 3. Aggressive Script Scrubbing (Multi-Language Block)
        # Includes CJK, Japanese, Hebrew (\u0590-\u05ff), Cyrillic (\u0400-\u04ff)
        # Keep Arabic, Numbers, Punctuation, and essential Latin for code
        hallucination_pattern = r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u0590-\u05ff\u0400-\u04ff\uff00-\uffef\uac00-\ud7af]'
        if re.search(hallucination_pattern, generated_part):
            logger.warning("🚨 Hallucination scripts detected! Scrubbing...")
            generated_part = re.sub(hallucination_pattern, '', generated_part)
            
        return (pre_fill or "") + generated_part.strip()

    # ---------------------------------------------------------
    # 1.1 GGUF Handler (llama-cpp-python)
    # ---------------------------------------------------------
    def _process_gguf(self, messages: List[Dict[str, str]], pre_fill: str = "") -> str:
        authority = get_model_authority()
        if authority.state != ModelState.LOADED:
            authority.load_model(backend="gguf", model_name=os.getenv("NOOGH_MODEL"))
        
        model = authority.loaded_model # This is the Llama instance
        
        # Build prompt using chat template if available, or manual format
        # llama-cpp-python has its own internal template handling if requested, 
        # but here we can just use simple Qwen format or try to use their helper.
        
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        
        prompt += "<|im_start|>assistant\n"
        if pre_fill:
            prompt += pre_fill

        logger.info(f"DEBUG_GGUF_PROMPT: {prompt}")
        
        response = model(
            prompt,
            max_tokens=512,
            temperature=0.5,
            top_p=0.9,
            repeat_penalty=1.2,
            stop=["<|im_end|>", "Observation:", "User:", "Assistant:"]
        )
        
        generated_part = response["choices"][0]["text"]
        logger.info(f"DEBUG_GGUF_RAW: {generated_part}")
        
        return self._normalize_response(generated_part, pre_fill)

    # ---------------------------------------------------------
    # 2. OpenAI Cloud Handler (Simulation Mode)
    # ---------------------------------------------------------
    async def _process_openai(self, messages: List[Dict[str, str]], pre_fill: str = "") -> str:
        if not self.api_key:
            return "⚠️ Error: OpenAI API Key missing."

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            # تنظيف الرسائل
            clean_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
            
            # التأكد من وجود السيستم
            if not any(m['role'] == 'system' for m in clean_msgs):
                clean_msgs.insert(0, {"role": "system", "content": self.SYSTEM_PROMPT})

            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=clean_msgs,
                temperature=0.4, # More deterministic
                max_tokens=1000,
                stop=["Observation:", "User:"]
            )

            result_text = response.choices[0].message.content
            
            # محاكاة Pre-fill يدوياً
            if pre_fill and not result_text.startswith(str(pre_fill)):
                return f"{pre_fill}\n{result_text}"
            
            return result_text

        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            return f"⚠️ Cloud Inference Failed: {str(e)}"

    # ---------------------------------------------------------
    # Unified ReAct Loop
    # ---------------------------------------------------------
    async def reason(self, context: Dict[str, Any], query: str, pre_fill: str = "") -> ReasoningResult:
        logger.info(f"🎯 Reason Start ({self.backend}): {query[:50]}...")
        
        # Build prompt: Only include relevant context, or keep it simple for chat
        ctx_filtered = {k: v for k, v in context.items() if k not in ['use_reasoning'] and v}
        if ctx_filtered:
            ctx_str = "\n".join([f"- {k}: {v}" for k, v in ctx_filtered.items()])
            user_msg = f"البيانات المتاحة:\n{ctx_str}\n\nسؤالي هو: {query}"
        else:
            user_msg = query

        history = [{"role": "user", "content": user_msg}]
        
        # --- STRATEGIC ROADMAP v12.8: FORENSIC TRACING ---
        trace_manager = get_trace_manager()
        c_trace = trace_manager.create_trace(query)
        c_trace.set_backend(self.backend)
        
        last_response = ""
        all_tool_calls = []
        observations = []
        final_iterations = 0
        
        for i in range(SystemConfig.MAX_ITERATIONS):
            final_iterations = i + 1
            c_trace.start_iteration(i)
            
            raw_response = await self.process(history, pre_fill=pre_fill if i == 0 else "")
            last_response = raw_response
            c_trace.add_thought(raw_response)
            history.append({"role": "assistant", "content": raw_response})
            
            # محاولة استخراج JSON الأدوات
            calls, errors = ToolCallParser.extract_and_validate(raw_response)
            if not calls:
                c_trace.end_iteration(i, reason="no_tool_calls")
                break
                
            executor = get_tool_executor()
            
            observations = []
            for tool_name, args in calls:
                all_tool_calls.append({"tool": tool_name, "args": args})
                # Dynamic Path Resolution
                if "path" in args:
                    p = args["path"]
                    if not p.startswith("/") and not p.startswith("http"): 
                         args["path"] = os.path.join(SystemConfig.PROJECT_ROOT, "src", p)
                
                try:
                    logger.info(f"⚙️ EXECUTING TOOL: {tool_name} with {args}")
                    # Phase 1: Support Auth Propagation from context
                    auth = context.get('auth') or get_full_admin_auth()
                    
                    t_trace = c_trace.start_tool_call(tool_name, args)
                    result = await executor.registry.execute(tool_name, args, auth_context=auth)
                    
                    if isinstance(result, dict):
                        # Handle HITL (Human-in-the-loop) Approval Request
                        if result.get("approval_required"):
                            logger.info(f"🛑 HITL Pause: Approval needed for {tool_name}")
                            c_trace.end_tool_call(t_trace, success=False, error="HITL_APPROVAL_REQUIRED")
                            c_trace.set_termination("hitl_pause", f"Approval needed for {tool_name}", 1.0)
                            trace_manager.log_persistent(c_trace)
                            return ReasoningResult(
                                conclusion=f"نوقة (موافقة): يتطلب تنفيذ الأداة `{tool_name}` موافقة يدوية. \n\nالوصف: {result.get('description_ar', 'غير متوفر')}\nالأوامر: {result.get('args')}\n\nهل تؤكد التنفيذ؟ (نعم/لا)",
                                confidence=1.0,
                                reasoning_trace=c_trace.reasoning_trace, # Use unified trace
                                suggested_actions=["نعم", "لا"],
                                tool_calls=all_tool_calls
                            )

                        # Extract clean output
                        if not result.get('success'):
                            content = f"⚠️ Tool Error: {result.get('error', 'Execution failed')}"
                            c_trace.end_tool_call(t_trace, success=False, error=result.get('error'))
                        else:
                            # Use stdout/output but ensure it's a string for logging
                            content = result.get('output') or result.get('stdout') or str(result)
                            c_trace.end_tool_call(t_trace, success=True, result=str(content))
                    else:
                        content = str(result)
                        c_trace.end_tool_call(t_trace, success=True, result=content)
                except Exception as e:
                    # Phase 2: Context Hygiene - Clean error messages for the LLM
                    logger.error(f"Reasoning Core - Tool Execution Failure: {e}")
                    content = "⚠️ System Error: واجه النظام مشكلة داخلية أثناء تشغيل الأداة. يرجى المحاولة مرة أخرى أو استخدام وسيلة بديلة."

                content_str = str(content)
                if len(content_str) > 2000: content_str = content_str[:2000] + "... [Truncated]"
                logger.info(f"📥 OBSERVED: {content_str[:100]}...")
                observations.append(f"n> مخرجات الأداة ({tool_name}):\n{content_str}")
            
            c_trace.end_iteration(i, reason="completed")
            history.append({
                "role": "user", 
                "content": f"""تم تنفيذ الأدوات. النتائج:
{chr(10).join(observations)}

<post_tool_rules>
1. استخلص الإجابة النهائية بناءً على نتائج الأدوات فقط
2. لا تختلق معلومات غير موجودة في المخرجات
3. إذا كانت النتائج غير كافية، قل ذلك بوضوح
4. أجب بأسلوب نوقة (بالعربية، مباشر، بدون تمهيد)
5. لا تذكر أسماء الأدوات — وصف ما فعلته بلغة طبيعية
</post_tool_rules>"""
            })

        # تنظيف الرد النهائي
        conclusion = last_response
        conclusion = re.sub(r'```json.*?```', '', conclusion, flags=re.DOTALL)
        conclusion = re.sub(r'```\w*\n.*?```', '', conclusion, flags=re.DOTALL)
        conclusion = re.sub(r'\{"tool".*?\}', '', conclusion, flags=re.DOTALL).strip()
        
        # Strip model thinking/planning preambles that leak to user
        thinking_patterns = [
            r'نوقة\s*\(\s*(?:تفكير|THINKING|thinking)\s*\)\s*:.*?(?=\n\n|$)',  # نوقة (تفكير): or نوقة ( THINKING ):
            r'القرار(?:ات)?\s*\(\s*(?:JSON|json)\s*\)\s*:.*?(?=\n\n|$)',      # القرارات (JSON): with optional spaces
            r'القرار(?:ات)?\s*:?\s*---.*',               # القرارات: ---
            r"'decision'\s*:\s*'[^']*'",                   # 'decision': '...'
            r'\{\s*\'decision\'[^}]*\}',                   # {'decision': '...'}
            r'سأقوم\s+ب[^.]+\.',                          # سأقوم بتقييم الوضع.
            r'سأتحقق\s+[^.]+\.',                          # سأتحقق مما إذا...
            r'سأجيب\s+[^:]+:',                            # سأجيب على السؤال:
            r'دعني\s+[^.]+\.',                             # دعني أتحقق.
            r'و يجب أن يكون[^.]+\.',                       # و يجب أن يكون...
            r'يجب أن يكون لي[^.]+\.',                      # يجب أن يكون لي...
            r'هل هناك أي شيء[^?؟]+[?؟]',                   # هل هناك أي شيء...؟
            r'\*\*المساعد\*\*\s*:?\s*',                     # **المساعد**:
            r'(?m)^---+\s*$',                               # --- separator lines
            r'(?m)^#\s*(Default behavior|TODO|FIXME).*$',   # Code comments
            r'(?m)^def\s+\w+\(.*?\):.*$',                   # Python def
            r'(?m)^\s+(?:return|print|raise|import)\s+.*$', # Indented code
            r'(?m)^import\s+\w+.*$',                        # Top imports
            r"\[\s*\{[^]]*?['\"](?:decision|action)['\"][^]]*?\}\s*\]",  # Fake JSON arrays
        ]
        for pat in thinking_patterns:
            conclusion = re.sub(pat, '', conclusion, flags=re.DOTALL)
        
        conclusion = re.sub(r'\n{3,}', '\n\n', conclusion).strip()
        
        # If after cleanup nothing remains, the model only generated thinking text.
        # Try a follow-up prompt to get a direct answer.
        if not conclusion or len(conclusion.strip()) < 5:
            if observations:
                conclusion = '\n'.join(str(o) for o in observations[:3])
            else:
                # Re-prompt with a strong direct-answer instruction
                try:
                    followup_msgs = history + [
                        {"role": "user", "content": "أجب بإجابة مباشرة ومختصرة فقط، بدون تفكير أو تخطيط. أعطني الإجابة النهائية:"}
                    ]
                    direct_response = await self.process(followup_msgs)
                    # Quick cleanup of the follow-up
                    direct_response = re.sub(r'```json.*?```', '', direct_response, flags=re.DOTALL)
                    direct_response = re.sub(r'\{"tool".*?\}', '', direct_response, flags=re.DOTALL)
                    for pat in thinking_patterns:
                        direct_response = re.sub(pat, '', direct_response, flags=re.DOTALL)
                    direct_response = direct_response.strip()
                    if direct_response and len(direct_response) >= 5:
                        conclusion = direct_response
                    else:
                        conclusion = "أنا نوقة، المساعد الذكي لنظام NOOGH الموحد. أستطيع مساعدتك في إدارة النظام، تنفيذ الأوامر، وتحليل البيانات. كيف يمكنني مساعدتك؟"
                except Exception:
                    conclusion = "أنا نوقة، المساعد الذكي لنظام NOOGH الموحد. أستطيع مساعدتك في إدارة النظام، تنفيذ الأوامر، وتحليل البيانات. كيف يمكنني مساعدتك؟"
        
        # Final linguistic check (Fail-safe for CJK hallucinations)
        if re.search(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', conclusion):
             conclusion = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', conclusion).strip()
             if not conclusion:
                 conclusion = "عذراً، حدث خطأ في معالجة اللغة. يرجى المحاولة مرة أخرى."
        
        c_trace.set_termination("completed", conclusion, 0.96)
        trace_manager.log_persistent(c_trace)
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=0.96,
            reasoning_trace=c_trace.reasoning_trace,
            suggested_actions=[],
            raw_response=last_response,
            iterations=final_iterations,
            tool_calls=all_tool_calls
        )
