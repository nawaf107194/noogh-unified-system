# tests/abstract_base_test.py
import abc
from typing import Any
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

class AbstractBaseTest(abc.ABC):
    """
    Abstract base class for test cases to centralize setup and teardown logic.
    Implements async setup and teardown for database connections.
    """

    def __init__(self):
        self.session = None

    async def asyncSetUp(self):
        """
        Asynchronous setup method executed before each test.
        Creates a new database session.
        """
        from src.db import SessionLocal
        self.session = AsyncSession(SessionLocal())
        await self.session.__aenter__()

    async def asyncTearDown(self):
        """
        Asynchronous teardown method executed after each test.
        Closes the database session.
        """
        if self.session:
            await self.session.__aexit__(None, None, None)

    @pytest.fixture(autouse=True)
    async def setup(self):
        """
        Pytest fixture to automatically set up and tear down the test environment.
        """
        await self.asyncSetUp()
        yield
        await self.asyncTearDown()

    @abc.abstractmethod
    def get_test_data(self) -> dict[str, Any]:
        """
        Abstract method to provide test data specific to each test case.
        """
        pass

    def helper_method(self):
        """
        Example helper method for common test operations.
        """
        pass