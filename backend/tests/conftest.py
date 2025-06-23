"""
Pytest configuration and shared fixtures for papermes backend tests.
"""

import os
import sys
from pathlib import Path
import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def firefly_env_check():
    """
    Session-scoped fixture to check if Firefly III environment is properly configured.
    This runs once per test session and can be used to skip integration tests if not configured.
    """
    host = os.getenv("PAPERMES_FIREFLY_HOST")
    token = os.getenv("PAPERMES_FIREFLY_ACCESS_TOKEN")
    
    if not host or not token:
        pytest.skip(
            "Firefly III environment not configured. Set PAPERMES_FIREFLY_HOST and PAPERMES_FIREFLY_ACCESS_TOKEN"
        )
    
    return {"host": host, "token": token}


@pytest.fixture
def firefly_client():
    """
    Fixture that provides a Firefly client for tests.
    Automatically skips if environment is not configured.
    """
    try:
        from lib.firefly_client import FireflyClient
        
        with FireflyClient() as client:
            yield client
    except ImportError:
        pytest.skip("firefly_client module not available")
    except ValueError as e:
        if "environment variable" in str(e):
            pytest.skip(f"Firefly III not configured: {e}")
        raise


@pytest.fixture
def sample_account_id(firefly_client):
    """
    Fixture that provides a sample account ID for testing.
    Uses the first available account from the Firefly III instance.
    """
    accounts = firefly_client.get_accounts()
    if accounts.data:
        return accounts.data[0].id
    else:
        pytest.skip("No accounts available for testing")


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test requiring external services"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on file location.
    Automatically mark integration tests.
    """
    for item in items:
        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to tests in unit directory  
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
