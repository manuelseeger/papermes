"""
Pytest configuration and shared fixtures for papermes backend tests.
"""

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


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test requiring external services",
    )
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


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
