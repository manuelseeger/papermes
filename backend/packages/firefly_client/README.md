# Firefly III Client

A Python client library for interacting with the Firefly III personal finance API.

## Installation

```bash
pip install -e .
```

## Usage

```python
from firefly_client import FireflyClient

with FireflyClient(
    host="https://your-firefly-instance.com",
    access_token="your-personal-access-token",
    timeout=30.0
) as client:
    # Get accounts
    accounts = client.get_accounts(type_filter="asset")
    
    # Create a transaction
    transaction = client.create_transaction(
        # transaction details...
    )
```

## Testing

The package includes pytest fixtures for testing. You can configure the test environment in two ways:

### Option 1: Environment Variables
```bash
export FIREFLY_HOST="https://your-firefly-instance.com"
export FIREFLY_ACCESS_TOKEN="your-personal-access-token"
export FIREFLY_TIMEOUT="30.0"  # optional, defaults to 30.0
```

### Option 2: .env File (Recommended)
Copy the example file and fill in your values:
```bash
cp .env.example .env
# Edit .env with your Firefly III credentials
```

Then run tests:

```bash
pytest
```

## Environment Variables

- `FIREFLY_HOST`: Your Firefly III server URL
- `FIREFLY_ACCESS_TOKEN`: Your personal access token from Firefly III
- `FIREFLY_TIMEOUT`: Request timeout in seconds (optional, defaults to 30.0)
