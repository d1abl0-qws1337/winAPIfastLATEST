import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "secure_password_123",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data for tests."""
    return {
        "account_id": 1,
        "amount": "100.00",
        "currency": "USD",
        "payment_method": "card"
    }


@pytest.fixture
def sample_account_data():
    """Sample account data for tests."""
    return {
        "user_id": 1,
        "account_number": "ACC00000001",
        "balance": "1000.0000",
        "currency": "USD",
        "is_active": True
    }
