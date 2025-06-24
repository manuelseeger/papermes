"""
Pytest configuration and shared fixtures for papermes backend tests.
"""

import os
import sys
from pathlib import Path
import pytest

# Add backend directory to Python path for config import
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from config import get_config  # noqa: E402

# Get configuration
config = get_config()


@pytest.fixture(scope="session")
def firefly_env_check():
    """
    Session-scoped fixture to check if Firefly III environment is properly configured.
    This runs once per test session and can be used to skip integration tests if not configured.
    """
    host = config.firefly.host or os.getenv("PAPERMES_FIREFLY_HOST")
    token = config.firefly.access_token or os.getenv("PAPERMES_FIREFLY_ACCESS_TOKEN")
    
    if not host or not token:
        pytest.skip(
            "Firefly III environment not configured. Set PAPERMES_FIREFLY_HOST and PAPERMES_FIREFLY_ACCESS_TOKEN or configure in config.yml"
        )
    
    return {"host": host, "token": token}



# Pytest fixtures and utilities
@pytest.fixture
def default_account_id(firefly_client):
    """Fixture that provides the default account ID for testing."""
    accounts = firefly_client.get_accounts(type_filter="asset")
    if accounts.data:
        return accounts.data[0].id
    else:
        pytest.skip("No accounts available for testing")

@pytest.fixture
def sample_account_id(firefly_client):
    """Fixture that provides a sample account ID for testing."""
    accounts = firefly_client.get_accounts()
    if accounts.data:
        return accounts.data[0].id
    else:
        pytest.skip("No accounts available for testing")

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


@pytest.fixture
def testdata_dir() -> Path:
    """Get the testdata directory path."""
    return config.testdata_dir_path

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
