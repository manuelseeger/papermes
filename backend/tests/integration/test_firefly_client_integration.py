#!/usr/bin/env python3
"""
Integration tests for the Firefly III API client.

This module contains pytest-based integration tests for the Firefly client.
These tests require a running Firefly III instance and proper environment setup.

⚠️  WARNING: Some tests create real transaction data in Firefly III!
Tests marked with @pytest.mark.creates_data will modify your Firefly III database.

Usage:
    # Run all integration tests (including data-creating ones)
    pytest tests/integration/test_firefly_client.py -v

    # Run only read-only tests (skip data-creating tests)
    pytest tests/integration/test_firefly_client.py -v -m "not creates_data"

    # Run only data-creating tests (if you want to test transaction creation)
    pytest tests/integration/test_firefly_client.py -v -m "creates_data"

    # Run a specific test
    pytest tests/integration/test_firefly_client.py::test_connection -v
"""

import os
from decimal import Decimal

import pytest
from lib.firefly_client import FireflyAPIError, FireflyClient


class TestFireflyClient:
    """Integration tests for Firefly III API client."""

    def test_environment_variables(self):
        """Test that required environment variables or config are set."""
        # Try config first, then environment variables
        try:
            from config import get_config

            config = get_config()
            host = config.firefly.host or os.getenv("PAPERMES_FIREFLY_HOST")
            token = config.firefly.access_token or os.getenv(
                "PAPERMES_FIREFLY_ACCESS_TOKEN"
            )
        except ImportError:
            host = os.getenv("PAPERMES_FIREFLY_HOST")
            token = os.getenv("PAPERMES_FIREFLY_ACCESS_TOKEN")

        assert host is not None, (
            "PAPERMES_FIREFLY_HOST environment variable or config.yml must be set"
        )
        assert token is not None, (
            "PAPERMES_FIREFLY_ACCESS_TOKEN environment variable or config.yml must be set"
        )
        assert len(token) > 10, "PAPERMES_FIREFLY_ACCESS_TOKEN appears to be too short"

    def test_client_initialization(self, firefly_client):
        """Test that client can be initialized with environment variables."""
        assert firefly_client.host is not None
        assert firefly_client.access_token is not None
        assert not firefly_client.host.endswith("/"), "Host should not end with slash"

    def test_client_initialization_explicit_params(self):
        """Test client initialization with explicit parameters."""
        test_host = "http://test.example.com"
        test_token = "test_token_123"

        client = FireflyClient(host=test_host, access_token=test_token)

        assert client.host == test_host
        assert client.access_token == test_token

    def test_client_initialization_missing_host(self):
        """Test that client raises error when host is missing."""
        with pytest.raises(ValueError, match="Firefly III host must be provided"):
            FireflyClient("", "test_token")

    def test_client_initialization_missing_token(self):
        """Test that client raises error when token is missing."""
        with pytest.raises(ValueError, match="Access token must be provided"):
            FireflyClient("http://test.com", "")

    def test_connection_and_accounts_retrieval(self, firefly_client):
        """Test connection to Firefly III and accounts retrieval."""
        # Test basic connection by fetching accounts
        accounts = firefly_client.get_accounts()

        assert accounts is not None
        assert hasattr(accounts, "data")
        assert isinstance(accounts.data, list)

        # Print account information for debugging
        print(f"\n✅ Found {len(accounts.data)} accounts:")
        for account in accounts.data[:5]:  # Show first 5 accounts
            balance = account.attributes.current_balance or "N/A"
            currency = account.attributes.currency_code or ""
            print(
                f"   - {account.attributes.name} ({account.attributes.type}): {balance} {currency}"
            )

        if len(accounts.data) > 5:
            print(f"   ... and {len(accounts.data) - 5} more accounts")

    def test_asset_accounts_filtering(self, firefly_client):
        """Test filtering accounts by type."""
        asset_accounts = firefly_client.get_accounts(type_filter="asset")

        assert asset_accounts is not None
        assert hasattr(asset_accounts, "data")
        assert isinstance(asset_accounts.data, list)

        # Verify all returned accounts are asset accounts
        for account in asset_accounts.data:
            assert account.attributes.type in [
                "asset",
                "Default account",
                "Cash account",
                "Savings account",
            ], f"Expected asset account, got {account.attributes.type}"

        print(f"\n💰 Found {len(asset_accounts.data)} asset accounts")

    def test_get_specific_account(self, firefly_client):
        """Test retrieving a specific account by ID."""
        # First get all accounts to find a valid ID
        accounts = firefly_client.get_accounts()

        if accounts.data:
            first_account_id = accounts.data[0].id

            # Test getting specific account
            account = firefly_client.get_account(first_account_id)

            assert account is not None
            assert account.id == first_account_id
            assert hasattr(account, "attributes")
            assert hasattr(account.attributes, "name")

            print(
                f"\n📋 Retrieved account: {account.attributes.name} (ID: {account.id})"
            )
        else:
            pytest.skip("No accounts available to test specific account retrieval")

    def test_pagination(self, firefly_client):
        """Test account pagination."""
        # Test with limit
        accounts_limited = firefly_client.get_accounts(limit=2)

        assert accounts_limited is not None
        assert len(accounts_limited.data) <= 2

        # Test pagination if we have more than 2 accounts
        all_accounts = firefly_client.get_accounts()
        if len(all_accounts.data) > 2:
            page_2 = firefly_client.get_accounts(page=2, limit=2)
            assert page_2 is not None

            # Accounts on page 2 should be different from page 1
            page_1_ids = {acc.id for acc in accounts_limited.data}
            page_2_ids = {acc.id for acc in page_2.data}
            assert page_1_ids.isdisjoint(page_2_ids), (
                "Page 1 and 2 should have different accounts"
            )

    @pytest.mark.parametrize(
        "account_type", ["asset", "expense", "revenue", "liability"]
    )
    def test_account_type_filtering(self, account_type, firefly_client):
        """Test filtering by different account types."""
        filtered_accounts = firefly_client.get_accounts(type_filter=account_type)

        assert filtered_accounts is not None
        assert isinstance(filtered_accounts.data, list)

        print(f"\n🔍 Found {len(filtered_accounts.data)} {account_type} accounts")

    def test_error_handling_invalid_account_id(self, firefly_client):
        """Test error handling for invalid account ID."""
        with pytest.raises(FireflyAPIError) as exc_info:
            firefly_client.get_account(999999)  # Presumably invalid ID

        assert exc_info.value.status_code is not None
        print(f"\n⚠️  Expected error for invalid account ID: {exc_info.value}")

    def test_client_headers(self, firefly_client):
        """Test that client sets correct headers."""
        expected_headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
        }

        for header, value in expected_headers.items():
            assert firefly_client.client.headers.get(header) == value

        # Authorization header should contain Bearer token
        auth_header = firefly_client.client.headers.get("Authorization")
        assert auth_header is not None
        assert auth_header.startswith("Bearer ")
        assert len(auth_header) > len("Bearer ")


class TestFireflyClientTransactionCreation:
    """Tests for transaction creation - THESE TESTS MODIFY REAL DATA!"""

    def setup_method(self):
        """Set up test tracking for cleanup."""
        self.created_transaction_ids = []

    def teardown_method(self):
        """Clean up any remaining transactions after each test."""
        if hasattr(self, "created_transaction_ids") and self.created_transaction_ids:
            print(
                f"\n🧹 WARNING: {len(self.created_transaction_ids)} test transactions were not cleaned up during the test"
            )
            print("   Please manually delete the following transaction IDs if needed:")
            for transaction_id in self.created_transaction_ids:
                print(f"   - {transaction_id}")
            self.created_transaction_ids.clear()

    @pytest.mark.creates_data
    def test_create_withdrawal_transaction(
        self,
        firefly_client: FireflyClient,
        default_account_id,
        sample_expense_account_id,
    ):
        """
        Test creating a withdrawal transaction.
        ⚠️  WARNING: This test creates real transaction data in Firefly III!
        """
        # Create a test withdrawal transaction
        transaction = firefly_client.create_withdrawal(
            amount=25.50,
            description="Test Withdrawal - Integration Test",
            source_account_id=default_account_id,
            destination_account_id=sample_expense_account_id,
            category_name="Testing",
            notes="Created by integration test - safe to delete",
            tags=["integration-test", "automated-test"],
            error_if_duplicate_hash=False,
        )

        assert transaction is not None
        assert hasattr(transaction, "data")
        assert transaction.data.type == "transactions"
        assert transaction.data.id is not None

        # Verify transaction attributes
        attrs = transaction.data.attributes
        assert attrs.group_title is None  # Single transaction, no group
        assert len(attrs.transactions) == 1

        split = attrs.transactions[0]
        assert split.type == "withdrawal"
        assert split.amount == Decimal("25.50")
        assert split.description == "Test Withdrawal - Integration Test"
        assert split.source_id == default_account_id
        assert split.destination_id == sample_expense_account_id
        assert split.category_name == "Testing"
        assert split.notes == "Created by integration test - safe to delete"
        assert "integration-test" in split.tags
        assert "automated-test" in split.tags

        # Track transaction for cleanup
        self.created_transaction_ids.append(transaction.data.id)

        print(f"\n💸 Created withdrawal transaction: {transaction.data.id}")
        print(f"   Amount: {split.amount} {split.currency_code or 'USD'}")
        print(f"   Description: {split.description}")
        print(f"   Category: {split.category_name}")

        # Clean up immediately after verification
        try:
            firefly_client.delete_transaction(transaction.data.id)
            print(f"   ✅ Successfully cleaned up transaction {transaction.data.id}")
            self.created_transaction_ids.remove(transaction.data.id)
        except Exception as e:
            print(
                f"   ⚠️  Failed to clean up transaction {transaction.data.id}: {e}"
            ) @ pytest.mark.creates_data

    def test_create_deposit_transaction(self, firefly_client, default_account_id):
        """
        Test creating a deposit transaction.
        ⚠️  WARNING: This test creates real transaction data in Firefly III!
        """  # Create a test deposit transaction
        transaction = firefly_client.create_deposit(
            amount=100.00,
            description="Test Deposit - Integration Test",
            source_account_name="Test Income Source",
            destination_account_id=default_account_id,  # Asset account for deposits
            category_name="Testing Income",
            notes="Created by integration test - safe to delete",
            tags=["integration-test", "deposit-test"],
            error_if_duplicate_hash=False,
        )

        assert transaction is not None
        assert hasattr(transaction, "data")
        assert transaction.data.type == "transactions"
        assert transaction.data.id is not None

        # Verify transaction attributes
        attrs = transaction.data.attributes
        assert len(attrs.transactions) == 1

        split = attrs.transactions[0]
        assert split.type == "deposit"
        assert split.amount == Decimal("100.00")
        assert split.description == "Test Deposit - Integration Test"
        assert split.source_name == "Test Income Source"
        assert split.destination_id == default_account_id
        assert split.category_name == "Testing Income"
        assert split.notes == "Created by integration test - safe to delete"
        assert "integration-test" in split.tags
        assert "deposit-test" in split.tags

        # Track transaction for cleanup
        self.created_transaction_ids.append(transaction.data.id)

        print(f"\n💰 Created deposit transaction: {transaction.data.id}")
        print(f"   Amount: {split.amount} {split.currency_code or 'USD'}")
        print(f"   Description: {split.description}")
        print(f"   Category: {split.category_name}")

        # Clean up immediately after verification
        try:
            firefly_client.delete_transaction(transaction.data.id)
            print(f"   ✅ Successfully cleaned up transaction {transaction.data.id}")
            self.created_transaction_ids.remove(transaction.data.id)
        except Exception as e:
            print(
                f"   ⚠️  Failed to clean up transaction {transaction.data.id}: {e}"
            ) @ pytest.mark.creates_data

    def test_create_transfer_transaction(self, firefly_client, default_account_id):
        """
        Test creating a transfer transaction between accounts.
        ⚠️  WARNING: This test creates real transaction data in Firefly III!
        """
        # Get another account for transfer destination
        accounts = firefly_client.get_accounts(type_filter="asset")
        if len(accounts.data) < 2:
            pytest.skip("Need at least 2 asset accounts for transfer test")

        # Find a different account than the default one
        destination_account_id = None
        for account in accounts.data:
            if account.id != default_account_id:
                destination_account_id = account.id
                break

        if not destination_account_id:
            pytest.skip(
                "Could not find a different asset account for transfer test"
            )  # Create a test transfer transaction
        transaction = firefly_client.create_transfer(
            amount=50.00,
            description="Test Transfer - Integration Test",
            source_account_id=default_account_id,
            destination_account_id=destination_account_id,
            notes="Created by integration test - safe to delete",
            tags=["integration-test", "transfer-test"],
            error_if_duplicate_hash=False,
        )

        assert transaction is not None
        assert hasattr(transaction, "data")
        assert transaction.data.type == "transactions"
        assert transaction.data.id is not None

        # Verify transaction attributes
        attrs = transaction.data.attributes
        assert len(attrs.transactions) == 1

        split = attrs.transactions[0]
        assert split.type == "transfer"
        assert split.amount == Decimal("50.00")
        assert split.description == "Test Transfer - Integration Test"
        assert split.source_id == default_account_id
        assert split.destination_id == destination_account_id
        assert split.notes == "Created by integration test - safe to delete"
        assert "integration-test" in split.tags
        assert "transfer-test" in split.tags

        # Track transaction for cleanup
        self.created_transaction_ids.append(transaction.data.id)

        print(f"\n🔄 Created transfer transaction: {transaction.data.id}")
        print(f"   Amount: {split.amount} {split.currency_code or 'USD'}")
        print(f"   Description: {split.description}")
        print(f"   From: {default_account_id} → To: {destination_account_id}")

        # Clean up immediately after verification
        try:
            firefly_client.delete_transaction(transaction.data.id)
            print(f"   ✅ Successfully cleaned up transaction {transaction.data.id}")
            self.created_transaction_ids.remove(transaction.data.id)
        except Exception as e:
            print(f"   ⚠️  Failed to clean up transaction {transaction.data.id}: {e}")

    @pytest.mark.creates_data
    def test_create_transaction_with_group(self, firefly_client, default_account_id):
        """
        Test creating multiple transactions with a group title.
        ⚠️  WARNING: This test creates real transaction data in Firefly III!
        """
        from datetime import datetime

        from lib.firefly_client import TransactionSplit

        # Create multiple transaction splits for a shopping trip
        transaction_splits = [
            TransactionSplit(
                type="withdrawal",
                date=datetime.now().date().isoformat(),
                amount="15.99",
                description="Groceries - Milk and Bread",
                source_id=default_account_id,
                destination_name="Groceries",
                category_name="Groceries",
                notes="Created by integration test - safe to delete",
                tags=["integration-test", "groceries"],
            ),
            TransactionSplit(
                type="withdrawal",
                date=datetime.now().date().isoformat(),
                amount="8.50",
                description="Groceries - Fresh Produce",
                source_id=default_account_id,
                destination_name="Groceries",
                category_name="Groceries",
                notes="Created by integration test - safe to delete",
                tags=["integration-test", "groceries"],
            ),
        ]  # Store the transaction group
        transaction = firefly_client.store_transaction(
            transactions=transaction_splits,
            group_title="Test Shopping Trip - Integration Test",
            error_if_duplicate_hash=False,
        )

        assert transaction is not None
        assert hasattr(transaction, "data")
        assert transaction.data.type == "transactions"
        assert transaction.data.id is not None

        # Verify transaction attributes
        attrs = transaction.data.attributes
        assert attrs.group_title == "Test Shopping Trip - Integration Test"
        assert len(attrs.transactions) == 2  # Verify both splits
        total_amount = Decimal("0")
        for split in attrs.transactions:
            assert split.type == "withdrawal"

            assert split.source_id == default_account_id
            assert split.destination_name == "Groceries"
            assert split.category_name == "Groceries"
            assert "integration-test" in split.tags
            assert "groceries" in split.tags
            total_amount += split.amount

        assert total_amount == Decimal("24.49")  # 15.99 + 8.50

        # Track transaction for cleanup
        self.created_transaction_ids.append(transaction.data.id)

        print(f"\n🛒 Created grouped transaction: {transaction.data.id}")
        print(f"   Group: {attrs.group_title}")
        print(f"   Total Amount: ${total_amount:.2f}")
        print(f"   Splits: {len(attrs.transactions)}")

        # Clean up immediately after verification
        try:
            firefly_client.delete_transaction(transaction.data.id)
            print(f"   ✅ Successfully cleaned up transaction {transaction.data.id}")
            self.created_transaction_ids.remove(transaction.data.id)
        except Exception as e:
            print(f"   ⚠️  Failed to clean up transaction {transaction.data.id}: {e}")

    @pytest.mark.creates_data
    def test_transaction_error_handling(self, firefly_client):
        """
        Test error handling for invalid transaction creation.
        This test should not create any data due to validation errors.
        """  # Test with invalid source account ID
        with pytest.raises(FireflyAPIError) as exc_info:
            firefly_client.create_withdrawal(
                amount=10.00,
                description="Invalid Test Transaction",
                source_account_id="999999",  # Invalid account ID
                destination_account_id="999999",  # Invalid account ID
            )

        assert exc_info.value.status_code is not None
        print(f"\n⚠️  Expected error for invalid source account: {exc_info.value}")

        # Test with negative amount
        accounts = firefly_client.get_accounts(type_filter="asset")
        if accounts.data:
            valid_account_id = accounts.data[0].id

            with pytest.raises(Exception):  # This might be caught earlier by validation
                firefly_client.create_withdrawal(
                    amount=-50.00,  # Negative amount should fail
                    description="Negative Amount Test",
                    source_account_id=valid_account_id,
                    destination_account_name="Test Expense",
                )

    @pytest.mark.creates_data
    def test_delete_transaction_functionality(
        self, firefly_client, sample_expense_account_id, default_account_id
    ):
        """
        Test the delete transaction functionality specifically.
        Creates a transaction and then deletes it to test the delete API.
        """  # Create a test transaction specifically for deletion testing
        transaction = firefly_client.create_withdrawal(
            amount=1.00,
            description="Test Delete Transaction - Will be deleted",
            source_account_id=default_account_id,  # Asset account
            destination_account_id=sample_expense_account_id,  # Expense account
            category_name="Testing Delete",
            notes="Created specifically to test deletion functionality",
            tags=["integration-test", "delete-test"],
            error_if_duplicate_hash=False,
        )

        assert transaction is not None
        assert transaction.data.id is not None
        transaction_id = transaction.data.id

        print(f"\n🗑️  Created transaction for deletion test: {transaction_id}")

        # Test deletion
        try:
            firefly_client.delete_transaction(transaction_id)
            print(f"   ✅ Successfully deleted transaction {transaction_id}")

            # Verify deletion by trying to retrieve the transaction (should fail)
            # Note: We can't easily test this without a get_transaction method,
            # but the fact that delete_transaction didn't raise an exception is good

        except Exception as e:
            # If deletion fails, we need to track it for cleanup
            self.created_transaction_ids.append(transaction_id)
            raise AssertionError(f"Failed to delete transaction {transaction_id}: {e}")


class TestFireflyClientWithoutEnvironment:
    """Tests that don't require actual Firefly III connection."""

    def test_host_slash_handling(self):
        """Test that trailing slash is removed from host."""
        host_with_slash = "http://example.com/"
        client = FireflyClient(host=host_with_slash, access_token="test_token")

        assert client.host == "http://example.com"
        assert not client.host.endswith("/")

    def test_convenience_function(self):
        """Test the create_client convenience function."""
        from lib.firefly_client import create_client

        client = create_client(host="http://test.com", access_token="test_token")

        assert isinstance(client, FireflyClient)
        assert client.host == "http://test.com"
        assert client.access_token == "test_token"


# Integration test markers
pytestmark = pytest.mark.integration


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__, "-v"])
