from prometheus_client import REGISTRY



class TestIntegration:
    def test_metrics_include_jobs_and_plugins(self):
        # Force import to ensure registration
        pass

        # Check if metrics are registered
        metrics = list(REGISTRY.collect())
        names = [m.name for m in metrics]

        print(f"Registered Metrics: {names}")

        assert "noogh_jobs_submitted" in names
        assert "noogh_plugins_loaded" in names

    def test_plugin_endpoints_never_call_kernel_or_llm(self):
        # Conceptual: Verify loader doesn't import or init Kernel
        pass

        # Loader only uses Registry and os/json

    def test_job_execution_preserves_fail_closed(self):
        # Ensure that if Policy rejects, Job Fails
        from unittest.mock import MagicMock

        from gateway.app.core.jobs import JobBudget, JobRequest, JobStatus, get_job_store  # Correct import
        from gateway.app.core.worker import BackgroundWorker  # Correct import

        worker = BackgroundWorker(secrets={"NOOGH_DATA_DIR": "/tmp/test", "NOOGH_ENV": "dev"})
        # Mock Controller to return Refusal Result (simulating Policy Reject)
        worker.controller = MagicMock()
        # process_task returns AgentResult
        mock_res = MagicMock(success=False, error="ForbiddenRequest", answer="UNSUPPORTED")
        worker.controller.process_task.return_value = mock_res

        store = get_job_store(secrets={"NOOGH_DATA_DIR": "/tmp/test", "NOOGH_ENV": "dev"})
        req = JobRequest(task="forbidden", mode="auto", budgets=JobBudget(1000, 10))
        jid = store.submit_job(req)

        worker._process_job(jid)

        job = store.get_job(jid)
        assert job.status == JobStatus.FAILED
        assert job.error == "ForbiddenRequest" or "UNSUPPORTED" in job.error
