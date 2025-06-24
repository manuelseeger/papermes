"""
Unit tests for Firefly III client components that don't require external services.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from lib.firefly_client import (
    Account,
    AccountAttributes,
    FireflyAPIError,
    FireflyClient,
    TransactionSplit,
)


class TestFireflyClientUnit:
    """Unit tests for FireflyClient that don't require external connections."""

    def test_host_slash_handling(self):
        """Test that trailing slash is removed from host."""
        host_with_slash = "http://example.com/"
        client = FireflyClient(host=host_with_slash, access_token="test_token")

        assert client.host == "http://example.com"
        assert not client.host.endswith("/")

    def test_host_no_slash_unchanged(self):
        """Test that host without slash remains unchanged."""
        host_without_slash = "http://example.com"
        client = FireflyClient(host=host_without_slash, access_token="test_token")

        assert client.host == host_without_slash

    def test_initialization_with_parameters(self):
        """Test client initialization with explicit parameters."""
        host = "http://test.example.com"
        token = "test_token_123"
        timeout = 60.0

        client = FireflyClient(host=host, access_token=token, timeout=timeout)

        assert client.host == host
        assert client.access_token == token
        assert client.client.timeout.read == timeout

    def test_headers_are_set_correctly(self):
        """Test that HTTP client has correct headers."""
        client = FireflyClient(host="http://test.com", access_token="test_token")

        headers = client.client.headers
        assert headers["Accept"] == "application/vnd.api+json"
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_token"

    def test_convenience_function(self):
        """Test the create_client convenience function."""
        from lib.firefly_client import create_client

        client = create_client(host="http://test.com", access_token="test_token")

        assert isinstance(client, FireflyClient)
        assert client.host == "http://test.com"
        assert client.access_token == "test_token"


class TestTransactionSplit:
    """Unit tests for TransactionSplit model."""

    def test_amount_validation_string(self):
        """Test that string amounts are converted to Decimal."""
        split = TransactionSplit(
            type="withdrawal",
            date=date(2025, 6, 23),
            amount="123.45",
            description="Test transaction",
        )

        assert split.amount == Decimal("123.45")

    def test_amount_validation_float(self):
        """Test that float amounts are converted to Decimal."""
        split = TransactionSplit(
            type="withdrawal",
            date=date(2025, 6, 23),
            amount=123.45,
            description="Test transaction",
        )

        assert split.amount == Decimal("123.45")

    def test_amount_validation_decimal(self):
        """Test that Decimal amounts are preserved."""
        split = TransactionSplit(
            type="withdrawal",
            date=date(2025, 6, 23),
            amount=Decimal("123.45"),
            description="Test transaction",
        )

        assert split.amount == Decimal("123.45")

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        split = TransactionSplit(
            type="withdrawal",
            date=date(2025, 6, 23),
            amount="100.00",
            description="Test",
            category_name="Food",
            tags=["test", "food"],
            notes="Test notes",
        )

        assert split.category_name == "Food"
        assert split.tags == ["test", "food"]
        assert split.notes == "Test notes"

    def test_date_serialization(self):
        """Test that Date objects are properly serialized to ISO format."""
        test_date = date(2025, 6, 23)
        split = TransactionSplit(
            type="withdrawal",
            date=test_date,
            amount="100.00",
            description="Test transaction",
        )

        # Test serialization by calling model_dump
        serialized = split.model_dump()
        assert serialized["date"] == "2025-06-23"

    def test_optional_date_fields_serialization(self):
        """Test that optional date fields are properly serialized."""
        test_date = date(2025, 6, 23)
        split = TransactionSplit(
            type="withdrawal",
            date=test_date,
            amount="100.00",
            description="Test transaction",
            interest_date=test_date,
            book_date=None,  # This should remain None
        )

        serialized = split.model_dump()
        assert serialized["interest_date"] == "2025-06-23"
        assert serialized["book_date"] is None


class TestAccount:
    """Unit tests for Account model."""

    def test_account_creation(self):
        """Test creating an Account with attributes."""
        attributes = AccountAttributes(
            name="Test Account",
            type="asset",
            current_balance="1000.00",
            currency_code="USD",
        )

        account = Account(id=123, attributes=attributes)

        assert account.id == 123
        assert account.type == "accounts"  # Default value
        assert account.attributes.name == "Test Account"
        assert account.attributes.current_balance == "1000.00"


class TestFireflyAPIError:
    """Unit tests for FireflyAPIError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = FireflyAPIError("Test error")

        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data is None

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = FireflyAPIError("Not found", status_code=404)

        assert str(error) == "Not found"
        assert error.status_code == 404

    def test_error_with_response_data(self):
        """Test error with response data."""
        response_data = {"message": "Validation failed", "errors": ["Field required"]}
        error = FireflyAPIError(
            "Validation error", status_code=422, response_data=response_data
        )

        assert str(error) == "Validation error"
        assert error.status_code == 422
        assert error.response_data == response_data


class TestTransactionHelpers:
    """Unit tests for transaction helper methods."""

    def test_withdrawal_helper_with_date_object(self):
        """Test withdrawal helper with date object."""
        # Mock the client and its methods
        mock_client = Mock(spec=FireflyClient)
        mock_client.store_transaction.return_value = Mock()

        # Create a real client instance but replace the store_transaction method
        client = FireflyClient(host="http://test.com", access_token="test")
        client.store_transaction = mock_client.store_transaction

        test_date = date(2025, 6, 23)

        client.create_withdrawal(
            amount=Decimal("25.50"),
            description="Test withdrawal",
            source_account_id=1,
            destination_account_id=2,
            date=test_date,
        )

        # Check that store_transaction was called
        mock_client.store_transaction.assert_called_once()  # Get the transaction split that was passed
        call_args = mock_client.store_transaction.call_args
        splits = call_args[0][0]  # First positional argument
        assert len(splits) == 1
        split = splits[0]
        assert split.type == "withdrawal"
        assert split.date == date(2025, 6, 23)
        assert split.amount == Decimal("25.50")
        assert split.description == "Test withdrawal"

    def test_deposit_helper_defaults(self):
        """Test deposit helper with default date."""
        mock_client = Mock(spec=FireflyClient)
        mock_client.store_transaction.return_value = Mock()

        client = FireflyClient(host="http://test.com", access_token="test")
        client.store_transaction = mock_client.store_transaction

        with patch("lib.firefly_client.datetime") as mock_datetime:
            # Mock the date return properly - return a date object
            mock_datetime.now.return_value.date.return_value = date(2025, 6, 23)

            client.create_deposit(
                amount="1500.00",
                description="Salary",
                source_account_name="Employer",
                destination_account_id=1,
            )

        mock_client.store_transaction.assert_called_once()

        call_args = mock_client.store_transaction.call_args
        splits = call_args[0][0]
        split = splits[0]

        assert split.type == "deposit"
        assert split.date == date(2025, 6, 23)

    def test_transfer_helper(self):
        """Test transfer helper method."""
        mock_client = Mock(spec=FireflyClient)
        mock_client.store_transaction.return_value = Mock()

        client = FireflyClient(host="http://test.com", access_token="test")
        client.store_transaction = mock_client.store_transaction

        client.create_transfer(
            amount=100.00,
            description="Transfer between accounts",
            source_account_id=1,
            destination_account_id=2,
            date=date(2025, 6, 23),
        )

        mock_client.store_transaction.assert_called_once()

        call_args = mock_client.store_transaction.call_args
        splits = call_args[0][0]
        split = splits[0]

        assert split.type == "transfer"
        assert split.source_id == 1
        assert split.destination_id == 2

    def test_delete_transaction(self):
        """Test delete_transaction method."""
        mock_client = Mock(spec=FireflyClient)
        mock_client._make_request.return_value = None

        client = FireflyClient(host="http://test.com", access_token="test")
        client._make_request = mock_client._make_request

        client.delete_transaction(123)

        mock_client._make_request.assert_called_once_with("DELETE", "/transactions/123")

    def test_delete_transaction_journal(self):
        """Test delete_transaction_journal method."""
        mock_client = Mock(spec=FireflyClient)
        mock_client._make_request.return_value = None

        client = FireflyClient(host="http://test.com", access_token="test")
        client._make_request = mock_client._make_request

        client.delete_transaction_journal(456)

        mock_client._make_request.assert_called_once_with(
            "DELETE", "/transaction-journals/456"
        )
