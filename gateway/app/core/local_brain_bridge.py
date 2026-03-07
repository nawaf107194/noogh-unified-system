import logging
from typing import Any, Dict, Optional

from gateway.app.llm.brain_factory import get_brain_service
from neural_engine.module_interface import (
    ModuleInterface,
    ModuleMetadata,
    ModulePriority,
    ModuleStatus,
    ProcessingResult,
)

logger = logging.getLogger(__name__)


class LocalBrainBridge(ModuleInterface):
    """
    Bridge module for LocalBrainService to work with NeuralOrchestrator.
    This allows the Gateway's LLM to be part of the Neural Pipeline.
    """

    def __init__(self):
            super().__init__()
            self.brain = None
            module_name = "LocalBrainBridge"
            module_version = "1.0.0"
            module_description = "Bridge to LocalBrainService LLM"
            module_dependencies = ["gateway.app.llm.local_brain"]
            module_priority = ModulePriority.HIGH
            module_capabilities = ["reasoning", "generation", "chat"]

            def set_default(value, default_value, message):
                if not value:
                    logger.warning(message)
                    return default_value
                return value

            module_name = set_default(module_name, "Unnamed Module", "Module name is empty, setting to default 'Unnamed Module'")
            module_version = set_default(module_version, "0.0.0", "Module version is empty, setting to default '0.0.0'")
            module_description = set_default(module_description, "No description provided", "Module description is empty, setting to default 'No description provided'")
            module_dependencies = set_default(module_dependencies, [], "Module dependencies list is empty, setting to default empty list")
            module_capabilities = set_default(module_capabilities, [], "Module capabilities list is empty, setting to default empty list")

            self._metadata = ModuleMetadata(
                name=module_name,
                version=module_version,
                description=module_description,
                dependencies=module_dependencies,
                priority=module_priority,
                capabilities=module_capabilities,
            )

    def get_metadata(self) -> ModuleMetadata:
        return self._metadata

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.set_status(ModuleStatus.INITIALIZING)
        try:
            # Create LocalBrainService directly (NOT CloudClient)
            # This ensures we use Neural Engine proxy on localhost:8000
            from gateway.app.llm.local_brain import LocalBrainService
            import os
            
            secrets = {
                "LOCAL_MODEL_NAME": os.getenv("LOCAL_MODEL_NAME", "fallback"),
                "NOOGH_INTERNAL_TOKEN": os.getenv("NOOGH_INTERNAL_TOKEN", ""),
            }
            routing_mode = os.getenv("NOOGH_ROUTING_MODE", "auto")
            self.brain = LocalBrainService(secrets=secrets, backend=routing_mode)
            
            # If brain needs explicit init, do it here.
            if hasattr(self.brain, "wake_up"):
                await self.brain.wake_up()

            self.set_status(ModuleStatus.READY)
            logger.info(f"LocalBrainBridge ready: use_neural_proxy={getattr(self.brain, 'use_neural_proxy', False)}")
            return True
        except Exception as e:
            self.log_error("Failed to initialize LocalBrainBridge", e)
            return False

    async def validate_input(self, input_data: Any) -> tuple[bool, Optional[str]]:
        # Brain accepts strings or dicts with 'prompt'
        if isinstance(input_data, str) and input_data.strip():
            return True, None
        if isinstance(input_data, dict) and "messages" in input_data:
            return True, None
        if isinstance(input_data, dict) and "prompt" in input_data:
            return True, None

        return False, "Input must be a non-empty string or standard chat format dict"

    async def process(self, input_data: Any, context: Dict[str, Any]) -> ProcessingResult:
        if not self.is_ready():
            return ProcessingResult(False, None, {}, errors=["Module not ready"])

        try:
            prompt = ""
            if isinstance(input_data, str):
                prompt = input_data
            elif isinstance(input_data, dict):
                prompt = input_data.get("prompt", str(input_data))

            prompt_lower = prompt.lower().strip()
            
            # FAST PATH 1: Handle greetings directly without calling Neural Engine
            greeting_patterns = ['مرحبا', 'أهلا', 'السلام', 'صباح', 'مساء', 'hello', 'hi', 'hey']
            if len(prompt) < 50 and any(pattern in prompt_lower for pattern in greeting_patterns):
                import random
                responses = [
                    "أهلاً وسهلاً! أنا نووغ، كيف يمكنني مساعدتك اليوم؟ 😊",
                    "مرحباً! أنا جاهز لخدمتك. ماذا تريد أن نفعل؟",
                    "أهلاً بك! أنا نووغ - نظام الذكاء الاصطناعي. كيف أقدر أساعدك؟",
                ]
                return ProcessingResult(
                    success=True,
                    data=random.choice(responses),
                    metadata={"mode": "greeting", "path": "fast"},
                )
            
            # FAST PATH 2: Skip Knowledge Cache for general conceptual questions
            # These should be answered by LLM, not by finding random training examples
            general_concept_patterns = [
                "ما هو الذكاء الاصطناعي", "ما هو الذكاء", "what is ai", "what is artificial",
                "ما هو التعلم العميق", "ما هي الشبكات العصبية", "what is deep learning",
                "ما هو", "ما هي", "من هو", "من هي",  # General "what is" questions
                "اشرح لي", "explain to me", "tell me about",
                "عرّفني", "عرفني", "أخبرني عن", "حدثني عن"
            ]
            is_general_concept = any(pattern in prompt_lower for pattern in general_concept_patterns)
            
            # Direct answer for common AI-related questions (temporarily, until Neural Engine restart)
            if "الذكاء الاصطناعي" in prompt_lower or "artificial intelligence" in prompt_lower or "what is ai" in prompt_lower:
                ai_response = (
                    "🤖 **الذكاء الاصطناعي (AI)**\n\n"
                    "الذكاء الاصطناعي هو فرع من علوم الحاسوب يهدف لإنشاء أنظمة قادرة على:\n"
                    "- **التعلم:** اكتساب المعرفة من البيانات\n"
                    "- **التفكير:** التحليل واتخاذ القرارات\n"
                    "- **التكيف:** تحسين الأداء مع الوقت\n\n"
                    "**أنواعه الرئيسية:**\n"
                    "1. **الذكاء الضيق (Narrow AI):** متخصص في مهمة واحدة (مثلي أنا!)\n"
                    "2. **الذكاء العام (AGI):** قادر على كل ما يفعله الإنسان (لم يتحقق بعد)\n"
                    "3. **الذكاء الفائق (ASI):** يتجاوز القدرات البشرية (نظري)\n\n"
                    "أنا **نووغ** - مثال على الذكاء الضيق، متخصص في المحادثة والمساعدة! 🧠"
                )
                return ProcessingResult(
                    success=True,
                    data=ai_response,
                    metadata={"mode": "concept", "path": "fast", "topic": "ai"},
                )
            
            if is_general_concept:
                # Add flag to skip knowledge cache
                if isinstance(context, dict):
                    context["skip_knowledge_cache"] = True
                else:
                    context = {"skip_knowledge_cache": True}
                logger.info(f"🎯 General concept detected, skipping knowledge cache: {prompt[:50]}...")

            logger.info(f"DEBUG_BRIDGE: Generating for prompt: {prompt[:50]}...")
            
            # 🚀 CLEAN PASS: No local prompt injection? 
            # Actually, we NEED to inject XAI instructions for governance.
            xai_instruction = (
                "\n\n[SYSTEM: XAI_GOVERNANCE_ACTIVE]\n"
                "عندما تقرر تنفيذ أي أمر للنظام (ACT: tool_name)، يجب عليك أولاً تقديم تبرير تفصيلي "
                "في قسم (THINK:) يشرح بوضوح سبب الإجراء وعواقبه المتوقعة (15 كلمة على الأقل). "
                "بدون هذا التبرير، سيتم حظر العملية تلقائياً.\n"
            )
            
            full_prompt = xai_instruction + prompt
            
            # Use the brain service
            response = self.brain.generate(full_prompt)
            
            # Preserve full response for the pipeline (THINK/ACT/ANSWER)
            # Cleanup will be handled by the OUTPUT stage or the Frontend if needed.
            final_response = str(response)

            logger.info(f"DEBUG_BRIDGE: Processed response: {final_response[:50]}...")

            return ProcessingResult(
                success=True,
                data=final_response,
                metadata={
                    "model": self.brain.model_name,
                    "device": str(getattr(self.brain.model, "device", "unknown")),
                    "raw_length": len(str(response))
                },
            )

        except Exception as e:
            self.log_error("Processing failed", e)
            return ProcessingResult(False, None, {}, errors=[str(e)])

    async def get_status(self) -> Dict[str, Any]:
        brain_status = "unknown"
        if self.brain:
            brain_status = "hibernated" if self.brain.use_fallback and hasattr(self.brain, "hibernate") else "active"

        return {"status": self._status.value, "brain_state": brain_status}

    async def shutdown(self) -> bool:
        self.set_status(ModuleStatus.SHUTDOWN)
        # Maybe hibernate the brain on shutdown?
        if self.brain and hasattr(self.brain, "hibernate"):
            await self.brain.hibernate()
        return True
