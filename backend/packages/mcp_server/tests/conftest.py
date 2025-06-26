"""
Pytest configuration and fixtures for MCP server tests.
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)


@pytest.fixture
def testdata_dir():
    """Fixture that provides the path to test data directory."""
    # The testdata directory is in the project root
    testdata_path = project_root / ".." / "testdata"
    if not testdata_path.exists():
        pytest.skip(f"Test data directory not found: {testdata_path}")
    return testdata_path


@pytest.fixture
def receipt_files(testdata_dir):
    """Fixture that provides available receipt files for testing."""
    receipts_dir = testdata_dir / "photos" / "receipts"
    if not receipts_dir.exists():
        pytest.skip(f"Receipts directory not found: {receipts_dir}")

    receipt_files = list(receipts_dir.glob("*.jpg")) + list(receipts_dir.glob("*.png"))
    if not receipt_files:
        pytest.skip("No receipt files found for testing")

    return receipt_files
