# gateway/test_base.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from gateway.app.main import app
from gateway.app.db import get_db_session

class BaseTestCase:
    @pytest.fixture(scope="function")
    async def client(self):
        async with TestClient(app) as client:
            yield client

    @pytest.fixture(scope="function")
    async def db_session(self):
        session = AsyncSession(get_db_session())
        try:
            yield session
        finally:
            await session.close()

    async def setup_test_db(self, db_session):
        # Common DB setup logic
        pass

    async def teardown_test_db(self, db_session):
        # Common DB cleanup logic
        pass

    async def get_test_headers(self):
        # Common headers for authenticated requests
        return {}