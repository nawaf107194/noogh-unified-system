"""
Neural Orchestrator for Noug Neural OS
Coordinates all system components and manages execution pipeline
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

from .context_manager import ContextManager
from .feedback_loop import FeedbackLoop
from .module_interface import ModuleInterface
from .validation_layer import RiskLevel, ValidationLayer

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Stages in the processing pipeline"""

    INPUT = "input"
    SENSORY = "sensory"
    REASONING = "reasoning"
    DECISION = "decision"
    VALIDATION = "validation"
    EXECUTION = "execution"
    FEEDBACK = "feedback"
    OUTPUT = "output"


@dataclass
class PipelineResult:
    """Result of pipeline execution"""

    success: bool
    output: Any
    stages_completed: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "stages_completed": self.stages_completed,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "errors": self.errors,
        }


class NeuralOrchestrator:
    """
    Main orchestrator that coordinates all Noug Neural OS components
    Manages the complete processing pipeline from input to output
    """

    def __init__(self):
            # Core integration components
            self.context_manager = ContextManager()
            self.validation_layer = ValidationLayer()
            self.feedback_loop = FeedbackLoop()

            # Registered modules
            self.modules = {}

            # Pipeline configuration
            self.pipeline_stages = {
                PipelineStage.INPUT: [],
                PipelineStage.SENSORY: [],
                PipelineStage.REASONING: [],
                PipelineStage.DECISION: [],
                PipelineStage.VALIDATION: [],
                PipelineStage.EXECUTION: [],
                PipelineStage.FEEDBACK: [],
                PipelineStage.OUTPUT: [],
            }

            # Execution state
            self.is_running = False
            self._lock = asyncio.Lock()

            logger.info("NeuralOrchestrator initialized")

    async def register_module(self, module_name: str, module: ModuleInterface, stage: PipelineStage):
        """Register a module for a specific pipeline stage"""
        async with self._lock:
            self.modules[module_name] = module
            if module_name not in self.pipeline_stages[stage]:
                self.pipeline_stages[stage].append(module_name)
            logger.info(f"Registered module '{module_name}' for stage '{stage.value}'")

    async def unregister_module(self, module_name: str):
        """Unregister a module"""
        async with self._lock:
            if module_name in self.modules:
                del self.modules[module_name]
                # Remove from all stages
                for stage in self.pipeline_stages.values():
                    if module_name in stage:
                        stage.remove(module_name)
                logger.info(f"Unregistered module '{module_name}'")

    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize the orchestrator and all modules"""
        config = config or {}

        logger.info("Initializing NeuralOrchestrator...")

        # Initialize all registered modules
        for module_name, module in self.modules.items():
            try:
                module_config = config.get(module_name, {})
                success = await module.initialize(module_config)
                if success:
                    logger.info(f"Initialized module: {module_name}")
                else:
                    logger.error(f"Failed to initialize module: {module_name}")
            except Exception as e:
                logger.error(f"Error initializing module {module_name}: {e}", exc_info=True)

        self.is_running = True
        logger.info("NeuralOrchestrator initialization complete")

    async def process(
        self, 
        input_data: Any, 
        user_intent: str = "", 
        require_validation: bool = True, 
        require_permission: bool = False,
        prompt_context: Dict[str, Any] = None
    ) -> PipelineResult:
        """
        Process input through the complete pipeline

        Args:
            input_data: Input to process
            user_intent: User's intent/goal
            require_validation: Whether to validate before execution
            require_permission: Whether to require user permission
            context: Optional dictionary with additional context/parameters

        Returns:
            PipelineResult with output and metadata
        """
        start_time = datetime.now()
        session_id = str(uuid.uuid4())
        stages_completed = []
        errors = []
        stage_metadata = {}

        try:
            # Start session
            await self.context_manager.start_session(session_id)

            # Prepare parameters by merging input and passed context
            parameters = {"input": input_data}
            if prompt_context:
                parameters.update(prompt_context)

            # Set immediate context
            await self.context_manager.set_immediate_context(
                user_intent=user_intent, entities={}, parameters=parameters
            )

            # Get full context
            context = await self.context_manager.get_full_context()

            # Stage 1: Input Processing
            logger.info(f"[{session_id}] Starting INPUT stage")
            input_result, input_meta = await self._execute_stage_with_meta(PipelineStage.INPUT, input_data, context)
            stages_completed.append(PipelineStage.INPUT.value)
            if input_meta: stage_metadata.update(input_meta)

            # Stage 2: Sensory Processing
            logger.info(f"[{session_id}] Starting SENSORY stage")
            sensory_result, sensory_meta = await self._execute_stage_with_meta(PipelineStage.SENSORY, input_result, context)
            stages_completed.append(PipelineStage.SENSORY.value)
            if sensory_meta: stage_metadata.update(sensory_meta)

            # Stage 3: Reasoning
            logger.info(f"[{session_id}] Starting REASONING stage")
            reasoning_result, reasoning_meta = await self._execute_stage_with_meta(PipelineStage.REASONING, sensory_result, context)
            stages_completed.append(PipelineStage.REASONING.value)
            if reasoning_meta: stage_metadata.update(reasoning_meta)

            # Stage 4: Decision Making
            logger.info(f"[{session_id}] Starting DECISION stage")
            decision_result, decision_meta = await self._execute_stage_with_meta(PipelineStage.DECISION, reasoning_result, context)
            stages_completed.append(PipelineStage.DECISION.value)
            if decision_meta: stage_metadata.update(decision_meta)

            # Stage 5: Validation (if required)
            if require_validation:
                logger.info(f"[{session_id}] Starting VALIDATION stage")
                validation_result = await self._validate_decision(decision_result, context, require_permission)

                if not validation_result.is_valid:
                    errors.extend(validation_result.issues)
                    raise ValueError(f"Validation failed: {validation_result.issues}")

                stages_completed.append(PipelineStage.VALIDATION.value)

            # Stage 6: Execution
            logger.info(f"[{session_id}] Starting EXECUTION stage")
            execution_start = datetime.now()
            execution_result, execution_meta = await self._execute_stage_with_meta(PipelineStage.EXECUTION, decision_result, context)
            execution_duration = (datetime.now() - execution_start).total_seconds()
            stages_completed.append(PipelineStage.EXECUTION.value)
            if execution_meta: stage_metadata.update(execution_meta)

            # Stage 7: Feedback
            logger.info(f"[{session_id}] Starting FEEDBACK stage")
            await self.feedback_loop.record_action(
                action=user_intent or "process",
                success=True,
                duration=execution_duration,
                resource_usage={"cpu": 0.0, "memory": 0.0},
                context=context,
            )
            stages_completed.append(PipelineStage.FEEDBACK.value)

            # Stage 8: Output Processing
            logger.info(f"[{session_id}] Starting OUTPUT stage")
            output_result, output_meta = await self._execute_stage_with_meta(PipelineStage.OUTPUT, execution_result, context)
            stages_completed.append(PipelineStage.OUTPUT.value)
            if output_meta: stage_metadata.update(output_meta)

            # Record success in context
            await self.context_manager.add_historical_context(
                action=user_intent or "process", result=output_result, success=True, metadata={"session_id": session_id}
            )

            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()

            final_metadata = {"session_id": session_id, "stages": len(stages_completed)}
            final_metadata.update(stage_metadata)

            return PipelineResult(
                success=True,
                output=output_result,
                stages_completed=stages_completed,
                execution_time=total_time,
                metadata=final_metadata,
                errors=[],
            )

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            errors.append(str(e))

            # Record failure
            await self.feedback_loop.record_action(
                action=user_intent or "process",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                resource_usage={"cpu": 0.0, "memory": 0.0},
                context=context if "context" in locals() else {},
                error=e,
            )

            await self.context_manager.add_historical_context(
                action=user_intent or "process", result=str(e), success=False, metadata={"session_id": session_id}
            )

            return PipelineResult(
                success=False,
                output=None,
                stages_completed=stages_completed,
                execution_time=(datetime.now() - start_time).total_seconds(),
                metadata={"session_id": session_id},
                errors=errors,
            )

    async def _execute_stage(self, stage: PipelineStage, input_data: Any, context: Dict[str, Any]) -> Any:
        # Compatibility wrapper
        res, _ = await self._execute_stage_with_meta(stage, input_data, context)
        return res

    async def _execute_stage_with_meta(self, stage: PipelineStage, input_data: Any, context: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Execute all modules in a pipeline stage and return output + merged metadata"""

        module_names = self.pipeline_stages.get(stage, [])
        stage_meta = {}

        if not module_names:
            return input_data, {}

        result = input_data

        for module_name in module_names:
            module = self.modules.get(module_name)
            if not module or not module.is_ready():
                continue

            try:
                processing_result = await module.process(result, context)
                if processing_result.success:
                    result = processing_result.data
                    if processing_result.metadata:
                        stage_meta.update(processing_result.metadata)
                else:
                    logger.error(f"Module '{module_name}' failed: {processing_result.errors}")
            except Exception as e:
                logger.error(f"Error in module '{module_name}': {e}", exc_info=True)

        return result, stage_meta

    async def _validate_decision(self, decision: Any, context: Dict[str, Any], require_permission: bool):
        """Validate a decision before execution"""

        # Determine action type and data from decision
        action_type = "command"  # Default
        action_data = {"command": str(decision)}

        # Validate
        validation_result = await self.validation_layer.validate_action(action_type, action_data, context)

        # Check if permission required
        if require_permission and validation_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.warning(f"Action requires user permission: {validation_result.risk_level.name}")
            # In real implementation, would request user permission here

        return validation_result

    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        module_statuses = {}
        for name, module in self.modules.items():
            try:
                module_statuses[name] = await module.get_status()
            except Exception as e:
                module_statuses[name] = {"error": str(e)}

        return {
            "is_running": self.is_running,
            "registered_modules": len(self.modules),
            "pipeline_stages": {stage.value: len(modules) for stage, modules in self.pipeline_stages.items()},
            "modules": module_statuses,
            "context_summary": await self.context_manager.get_context_summary(),
            "performance_report": await self.feedback_loop.get_performance_report(),
        }

    async def shutdown(self):
        """Shutdown orchestrator and all modules"""
        logger.info("Shutting down NeuralOrchestrator...")

        for module_name, module in self.modules.items():
            try:
                await module.shutdown()
                logger.info(f"Shutdown module: {module_name}")
            except Exception as e:
                logger.error(f"Error shutting down module {module_name}: {e}")

        self.is_running = False
        logger.info("NeuralOrchestrator shutdown complete")
