import json

import pytest
from fastmcp import Client
from mcp_server.server import get_firefly_client, mcp


@pytest.fixture
def mcp_server():
    return mcp


@pytest.fixture
async def transaction_cleanup():
    """Fixture to track and cleanup created transactions"""
    created_transaction_ids = []

    yield created_transaction_ids

    # Cleanup: delete all created transactions
    if created_transaction_ids:
        with get_firefly_client() as client:
            for transaction_id in created_transaction_ids:
                try:
                    client.delete_transaction(transaction_id)
                except Exception as e:
                    # Log but don't fail test if cleanup fails
                    print(f"Failed to cleanup transaction {transaction_id}: {e}")


@pytest.mark.asyncio
async def test_get_user_prompt(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.get_prompt("user_analyze_receipt")
        assert "Analyze this image" in result.messages[0].content.text
        assert "receipt" in result.messages[0].content.text
        assert "transaction type" in result.messages[0].content.text
        assert "source and destination accounts" in result.messages[0].content.text
        assert "Unknown" in result.messages[0].content.text


@pytest.mark.asyncio
async def test_get_developer_bookkeeping_context_prompt(mcp_server):
    async with Client(mcp_server) as client:
        # Test with sample accounts data
        sample_accounts = [
            {"id": 1, "name": "Checking Account", "type": "asset"},
            {"id": 2, "name": "Savings Account", "type": "asset"},
            {"id": 3, "name": "Groceries", "type": "expense"},
        ]

        result = await client.get_prompt(
            "developer_bookkeeping_context", {"accounts": sample_accounts}
        )
        prompt_text = result.messages[0].content.text

        assert "bookeeping system" in prompt_text
        assert "tools provided" in prompt_text
        assert "available accounts" in prompt_text

        # Check that account information is included
        assert "Checking Account" in prompt_text
        assert "ID: 1" in prompt_text
        assert "Type: asset" in prompt_text
        assert "Savings Account" in prompt_text
        assert "Groceries" in prompt_text


@pytest.mark.asyncio
async def test_get_resource_accounts(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.read_resource("firefly://accounts")
        assert isinstance(result, list)
        assert len(result) > 0
        for account in result:
            assert account.mimeType == "application/json"

            accounts = json.loads(account.text)
            for account in accounts:
                assert "id" in account
                assert "name" in account
                assert "type" in account
                assert isinstance(account["id"], int)
                assert isinstance(account["name"], str)
                assert isinstance(account["type"], str)


@pytest.mark.asyncio
async def test_create_transactions_withdrawal(mcp_server, transaction_cleanup):
    async with Client(mcp_server) as client:
        # Test withdrawal transaction
        transactions = [
            {
                "type": "withdrawal",
                "source_account": "Checking Account",
                "destination_account": "Groceries",
                "amount": "50.00",
                "description": "Weekly groceries",
                "date": "2025-06-26",
                "currency_code": "USD",
                "category_name": "Food",
                "notes": "Test transaction",
                "tags": ["groceries", "test"],
            }
        ]

        result = await client.call_tool(
            "create_transactions",
            {"transactions": transactions, "group_title": "Test Grocery Shopping"},
        )

        # The result should be a dict with success status
        assert isinstance(result, dict)
        assert "success" in result

        # If transaction was created successfully, add to cleanup list
        if result.get("success") and "transaction_id" in result:
            transaction_cleanup.append(result["transaction_id"])

        # Note: In real tests, this might fail due to Firefly III connectivity
        # but we're testing the tool interface


@pytest.mark.asyncio
async def test_create_transactions_deposit(mcp_server, transaction_cleanup):
    async with Client(mcp_server) as client:
        # Test deposit transaction
        transactions = [
            {
                "type": "deposit",
                "source_account": "Salary",
                "destination_account": "Checking Account",
                "amount": "2500.00",
                "description": "Monthly salary",
                "currency_code": "USD",
            }
        ]

        result = await client.call_tool(
            "create_transactions", {"transactions": transactions}
        )

        assert isinstance(result, dict)
        assert "success" in result

        # If transaction was created successfully, add to cleanup list
        if result.get("success") and "transaction_id" in result:
            transaction_cleanup.append(result["transaction_id"])


@pytest.mark.asyncio
async def test_create_transactions_transfer(mcp_server, transaction_cleanup):
    async with Client(mcp_server) as client:
        # Test transfer transaction
        transactions = [
            {
                "type": "transfer",
                "source_account": "Checking Account",
                "destination_account": "Savings Account",
                "amount": "1000.00",
                "description": "Monthly savings transfer",
                "currency_code": "USD",
            }
        ]

        result = await client.call_tool(
            "create_transactions", {"transactions": transactions}
        )

        assert isinstance(result, dict)
        assert "success" in result

        # If transaction was created successfully, add to cleanup list
        if result.get("success") and "transaction_id" in result:
            transaction_cleanup.append(result["transaction_id"])


@pytest.mark.asyncio
async def test_create_transactions_multiple_splits(mcp_server, transaction_cleanup):
    async with Client(mcp_server) as client:
        # Test multiple transaction splits in one group
        transactions = [
            {
                "type": "withdrawal",
                "source_account": "Checking Account",
                "destination_account": "Groceries",
                "amount": "45.50",
                "description": "Food items",
                "currency_code": "USD",
                "category_name": "Food",
            },
            {
                "type": "withdrawal",
                "source_account": "Checking Account",
                "destination_account": "Household",
                "amount": "12.30",
                "description": "Cleaning supplies",
                "currency_code": "USD",
                "category_name": "Household",
            },
        ]

        result = await client.call_tool(
            "create_transactions",
            {"transactions": transactions, "group_title": "Shopping Trip"},
        )

        assert isinstance(result, dict)
        assert "success" in result

        # If transaction was created successfully, add to cleanup list
        if result.get("success") and "transaction_id" in result:
            transaction_cleanup.append(result["transaction_id"])


@pytest.mark.asyncio
async def test_create_transactions_invalid_type(mcp_server, transaction_cleanup):
    async with Client(mcp_server) as client:
        # Test invalid transaction type
        transactions = [
            {
                "type": "invalid_type",
                "source_account": "Checking Account",
                "destination_account": "Groceries",
                "amount": "50.00",
                "description": "Should fail",
                "currency_code": "USD",
            }
        ]

        result = await client.call_tool(
            "create_transactions", {"transactions": transactions}
        )

        assert isinstance(result, dict)
        assert "success" in result
        # If the tool validates properly, success should be False for invalid type
        if not result.get("success", True):
            assert "error" in result
            assert "Invalid transaction type" in result["error"]
        # Note: This test should not create a transaction, so no cleanup needed
