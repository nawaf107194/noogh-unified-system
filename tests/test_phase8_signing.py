import os
import unittest
from gateway.app.core.jobs import JobRecord, JobRequest, JobBudget, sign_job_record, verify_job_record, compute_job_signature
import time

class TestJobSigning(unittest.TestCase):
    def setUp(self):
        self.secret = "test_secret_123"
        self.job = JobRecord(
            job_id="job-1",
            request=JobRequest(
                task="Do something",
                mode="execute",
                budgets=JobBudget(1000, 10, 0, 0, 0)
            ),
            status="QUEUED",
            created_at=time.time(),
            updated_at=time.time()
        )

    def test_signing_verification_success(self):
        # 1. Sign
        sign_job_record(self.job, self.secret)
        self.assertIsNotNone(self.job.signature)
        
        # 2. Verify
        valid = verify_job_record(self.job, self.secret)
        self.assertTrue(valid)

    def test_tampering_fails_verification(self):
        # 1. Sign
        sign_job_record(self.job, self.secret)
        
        # 2. Tamper with payload (Task)
        self.job.request.task = "Do something evil"
        
        # 3. Verify
        valid = verify_job_record(self.job, self.secret)
        self.assertFalse(valid)

    def test_tampering_mode_fails(self):
        sign_job_record(self.job, self.secret)
        self.job.request.mode = "god_mode"
        valid = verify_job_record(self.job, self.secret)
        self.assertFalse(valid)

    def test_wrong_secret_fails(self):
        sign_job_record(self.job, self.secret)
        valid = verify_job_record(self.job, "wrong_secret")
        self.assertFalse(valid)

if __name__ == '__main__':
    unittest.main()
