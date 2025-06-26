import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")


# Pytest fixtures and utilities
@pytest.fixture
def default_account_id(firefly_client):
    """Fixture that provides the default account ID for testing."""
    accounts = firefly_client.get_accounts(type_filter="asset")
    accounts = [a for a in accounts.data if a.attributes.active]
    if accounts:
        return accounts[0].id
    else:
        pytest.skip("No accounts available for testing")


@pytest.fixture
def sample_expense_account_id(firefly_client):
    """Fixture that provides a sample expense account ID for testing."""
    accounts = firefly_client.get_accounts(type_filter="expense")
    accounts = [a for a in accounts.data if a.attributes.active]
    if accounts:
        return accounts[0].id
    else:
        pytest.skip("No accounts available for testing")


@pytest.fixture
def firefly_client():
    """
    Fixture that provides a Firefly client for tests.
    Automatically skips if environment is not configured.

    Configuration options:
    1. Environment variables:
       - FIREFLY_HOST: Firefly III server URL
       - FIREFLY_ACCESS_TOKEN: Personal access token
       - FIREFLY_TIMEOUT: Request timeout (optional, defaults to 30.0)

    2. .env file in package root with the same variables
    """
    try:
        from firefly_client import FireflyClient

        # Get configuration from environment variables
        host = os.getenv("FIREFLY_HOST")
        access_token = os.getenv("FIREFLY_ACCESS_TOKEN")
        timeout = float(os.getenv("FIREFLY_TIMEOUT", "30.0"))

        # Check if required environment variables are set
        if not host or not access_token:
            pytest.skip(
                "Firefly III not configured. Set FIREFLY_HOST and FIREFLY_ACCESS_TOKEN environment variables."
            )

        with FireflyClient(
            host=host,
            access_token=access_token,
            timeout=timeout,
        ) as client:
            yield client
    except ImportError:
        pytest.skip("firefly_client module not available")
    except ValueError as e:
        if "environment variable" in str(e):
            pytest.skip(f"Firefly III not configured: {e}")
        raise
