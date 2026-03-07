import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.analytics import get_analytics
from gateway.app.core.auth import AuthContext
from gateway.app.core.jobs import JobRecord, JobStatus, get_job_store, verify_job_record
from gateway.app.core.planning import ExecutionPlan
from gateway.app.core.resilience import CircuitBreaker, PlanStateRecovery
from gateway.app.core.sandbox import get_sandbox_service
from gateway.app.llm.remote_brain import RemoteBrainService

logger = logging.getLogger("worker")


class BackgroundWorker:
    """
    Consumer for the JobStore queue.
    Executes tasks using AgentKernel in a background thread.
    """

    def __init__(self, secrets: Dict[str, str], brain: RemoteBrainService = None):
        self.secrets = secrets
        self.job_store = get_job_store(secrets=secrets)
        self.brain = brain
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="noogh_worker")
        self._kernel_instance: Optional[AgentKernel] = None

        # Resilience Components
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60)
        self.recovery_manager = PlanStateRecovery()

    def get_kernel(self) -> AgentKernel:
        """Lazy load or reuse kernel."""
        if not self._kernel_instance:
            if not self.brain:
                from gateway.app.llm.brain_factory import create_brain

                self.brain = create_brain(secrets=self.secrets)

            sandbox_url = self.secrets.get("NOOGH_SANDBOX_URL", "http://sandbox_service:8000")
            sandbox = get_sandbox_service(service_url=sandbox_url)
            self._kernel_instance = AgentKernel(
                brain=self.brain,
                strict_protocol=True,
                sandbox_service=sandbox,
                enable_learning=True,
                enable_dream_mode=True,
                enable_router=True,
            )
            logger.info(f"Worker Kernel initialized (Sandbox={'ENABLED' if sandbox else 'DISABLED'})")
        return self._kernel_instance

    async def start(self):
        """Main asyncio loop."""
        self.running = True
        logger.info("BackgroundWorker started. Polling queue...")

        while self.running:
            try:
                job_id = self._find_next_job()
                if job_id:
                    await self._process_job(job_id)
                else:
                    await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5.0)

    def stop(self):
        self.running = False
        self.executor.shutdown(wait=False)

    def _find_next_job(self):
        if hasattr(self.job_store, "pop_job_blocking"):
            return self.job_store.pop_job_blocking(timeout=2)
        if hasattr(self.job_store, "pop_job"):
            return self.job_store.pop_job()
        queued_ids = self.job_store.list_queued_jobs()
        if queued_ids:
            return queued_ids[0]
        return None

    async def _process_job(self, job_id: str):
        job = self.job_store.get_job(job_id)
        if not job or job.status != JobStatus.QUEUED:
            return

        logger.info(f"Claiming job {job_id}: {job.request.task[:50]}...")
        job.status = JobStatus.RUNNING
        self.job_store.save_job(job)

        try:
            secret = self.secrets.get("NOOGH_JOB_SIGNING_SECRET")
            if secret:
                if not verify_job_record(job, secret):
                    logger.critical(f"SECURITY ALERT: Job {job_id} failed signature verification!")
                    job.status = JobStatus.FAILED
                    job.error = "SECURITY: Job Signature Verification Failed"
                    return

            loop = asyncio.get_running_loop()
            exec_func = self.orchestrate_plan if job.request.job_type == "plan_execution" else self._execute_sync

            result = await loop.run_in_executor(self.executor, exec_func, job)

            job.status = JobStatus.SUCCEEDED if result["success"] else JobStatus.FAILED
            job.result = result["answer"]
            job.error = result["error"]
            job.metrics = {"steps": result.get("steps", 0), "duration_ms": result.get("execution_time_ms", 0)}
        except Exception as e:
            logger.error(f"Job execution crashed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self.job_store.save_job(job)

    def _execute_sync(self, job: JobRecord) -> dict:
        kernel = self.get_kernel()
        kernel.max_iterations = job.request.budgets.max_steps
        system_auth = AuthContext(token="worker", scopes={"*"})
        start_t = time.time()
        result = kernel.process(job.request.task, auth=system_auth)
        duration = (time.time() - start_t) * 1000
        return {
            "success": result.success,
            "answer": result.answer,
            "error": result.error,
            "steps": result.steps,
            "execution_time_ms": duration,
        }

    def orchestrate_plan(self, job: JobRecord) -> dict:
        start_t = time.time()
        try:
            plan_id = job.request.task.replace("Execute Plan ", "").strip()
        except Exception:
            return {"success": False, "error": "Invalid task format.", "answer": None}

        data_dir = self.secrets.get("NOOGH_DATA_DIR", ".")
        plan_path = os.path.join(data_dir, f"PLAN_{plan_id}.json")
        if not os.path.exists(plan_path):
            return {"success": False, "error": f"Plan {plan_id} not found.", "answer": None}

        try:
            with open(plan_path, "r") as f:
                plan_data = json.load(f)
            plan = ExecutionPlan(**plan_data)
        except Exception as e:
            return {"success": False, "error": f"Failed to load plan: {e}", "answer": None}

        plan.status = "executing"
        self.recovery_manager.save_checkpoint(plan)
        kernel = self.get_kernel()
        system_auth = AuthContext(token="worker", scopes={"*"})
        total_steps_executed = 0

        while True:
            next_step = plan.get_next_step()
            if not next_step:
                if all(s.status == "completed" for s in plan.steps):
                    plan.status = "completed"
                    self.recovery_manager.save_checkpoint(plan)
                    duration = (time.time() - start_t) * 1000

                    duration = (time.time() - start_t) * 1000
                    
                    # Log Experience & Analytics
                    # Memory logging disabled due to decoupling
                    
                    get_analytics(data_dir=data_dir).log_job(
                        job.job_id, "plan_execution", total_steps_executed, duration, "SUCCEEDED"
                    )

                    return {
                        "success": True,
                        "answer": "Plan completed.",
                        "steps": total_steps_executed,
                        "execution_time_ms": duration,
                    }
                else:
                    plan.status = "failed"
                    self.recovery_manager.save_checkpoint(plan)
                    get_analytics(data_dir=data_dir).log_job(
                        job.job_id, "plan_execution", total_steps_executed, (time.time() - start_t) * 1000, "FAILED"
                    )
                    return {"success": False, "error": "Plan failed."}

            next_step.status = "running"
            next_step.attempt_count += 1
            self.recovery_manager.save_checkpoint(plan)

            try:
                result = self.circuit_breaker.execute(lambda: kernel.process(next_step.description, auth=system_auth))
                total_steps_executed += result.steps
                if result.success:
                    next_step.status = "completed"
                    next_step.result = result.answer
                    self.circuit_breaker.record_success()
                else:
                    next_step.error_history.append(result.error or "Unknown error")
                    if next_step.attempt_count < next_step.max_retries:
                        next_step.status = "pending"
                    else:
                        next_step.status = "failed"
                        self.circuit_breaker.record_failure()
            except Exception:
                next_step.status = "failed"
                self.circuit_breaker.record_failure()
            self.recovery_manager.save_checkpoint(plan)
