"""
Firefly III API Client Library

A Python client library for interacting with the Firefly III personal finance API.
Supports account management and transaction creation using Personal Access Tokens.
"""

import logging
from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_serializer

# Default values
DEFAULT_TIMEOUT = 30.0
DEFAULT_CURRENCY = "USD"


logger = logging.getLogger(__name__)


class AccountType(str, Enum):
    """Firefly III Account Types based on API specification."""

    ASSET = "asset"
    EXPENSE = "expense"
    IMPORT = "import"
    REVENUE = "revenue"
    CASH = "cash"
    LIABILITY = "liability"
    LIABILITIES = "liabilities"
    INITIAL_BALANCE = "initial-balance"
    RECONCILIATION = "reconciliation"


class TransactionType(str, Enum):
    """Firefly III Transaction Types."""

    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    RECONCILIATION = "reconciliation"
    OPENING_BALANCE = "opening balance"


class FireflyAPIError(Exception):
    """Base exception for Firefly III API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AccountAttributes(BaseModel):
    """Account attributes from Firefly III API."""

    model_config = ConfigDict(extra="allow")

    name: str
    type: AccountType
    account_role: Optional[str] = None
    currency_id: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_decimal_places: Optional[int] = None
    current_balance: Optional[str] = None
    current_balance_date: Optional[str] = None
    notes: Optional[str] = None
    monthly_payment_date: Optional[str] = None
    credit_card_type: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    virtual_balance: Optional[str] = None
    opening_balance: Optional[str] = None
    opening_balance_date: Optional[str] = None
    liability_type: Optional[str] = None
    liability_direction: Optional[str] = None
    interest: Optional[str] = None
    interest_period: Optional[str] = None
    active: Optional[bool] = None
    include_net_worth: Optional[bool] = None


class Account(BaseModel):
    """Firefly III Account model."""

    model_config = ConfigDict(extra="allow")

    id: int
    type: str = Field(default="accounts")
    attributes: AccountAttributes


class AccountsList(BaseModel):
    """Response model for accounts list."""

    data: List[Account]
    meta: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None


class TransactionSplit(BaseModel):
    """Individual transaction split within a transaction."""

    model_config = ConfigDict(extra="allow")

    type: TransactionType
    date: Date
    amount: Decimal
    description: str
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    destination_id: Optional[int] = None
    destination_name: Optional[str] = None
    currency_id: Optional[int] = None
    currency_code: Optional[str] = None
    foreign_amount: Optional[str] = None
    foreign_currency_id: Optional[int] = None
    foreign_currency_code: Optional[str] = None
    budget_id: Optional[int] = None
    budget_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    bill_id: Optional[int] = None
    bill_name: Optional[str] = None
    reconciled: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    internal_reference: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    original_source: Optional[str] = None
    recurrence_id: Optional[int] = None
    bunq_payment_id: Optional[str] = None
    import_hash_v2: Optional[str] = None
    sepa_cc: Optional[str] = None
    sepa_ct_op: Optional[str] = None
    sepa_ct_id: Optional[str] = None
    sepa_db: Optional[str] = None
    sepa_country: Optional[str] = None
    sepa_ep: Optional[str] = None
    sepa_ci: Optional[str] = None
    sepa_batch_id: Optional[str] = None
    interest_date: Optional[Date] = None
    book_date: Optional[Date] = None
    process_date: Optional[Date] = None
    due_date: Optional[Date] = None
    payment_date: Optional[Date] = None
    invoice_date: Optional[Date] = None

    @field_serializer("amount")
    def serialize_amount(self, amount: Decimal) -> str:
        """Convert Decimal amount to string for JSON serialization."""
        return str(amount)

    @field_serializer(
        "date",
        "interest_date",
        "book_date",
        "process_date",
        "due_date",
        "payment_date",
        "invoice_date",
    )
    def serialize_date(self, date_value: Optional[Date]) -> Optional[str]:
        """Convert Date objects to ISO format strings for JSON serialization."""
        if date_value is None:
            return None
        return date_value.isoformat()


class TransactionAttributes(BaseModel):
    """Transaction attributes."""

    model_config = ConfigDict(extra="allow")

    group_title: Optional[str] = None
    transactions: List[TransactionSplit]


class TransactionStore(BaseModel):
    """Request model for storing a new transaction."""

    model_config = ConfigDict(extra="allow")

    error_if_duplicate_hash: Optional[bool] = None
    apply_rules: Optional[bool] = None
    fire_webhooks: Optional[bool] = None
    group_title: Optional[str] = None
    transactions: List[TransactionSplit]


class Transaction(BaseModel):
    """Firefly III Transaction model."""

    model_config = ConfigDict(extra="allow")

    id: int
    type: str = Field(default="transactions")
    attributes: TransactionAttributes


class TransactionResponse(BaseModel):
    """Response model for transaction creation."""

    data: Transaction
    meta: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None


class FireflyClient:
    """
    Firefly III API Client

    A client for interacting with the Firefly III REST API using Personal Access Tokens.
    """

    def __init__(
        self,
        host: str,
        access_token: str,
        timeout: float = DEFAULT_TIMEOUT,
        httpx_client: Optional[httpx.Client] = None,
    ):
        """
        Initialize the Firefly III client.

        Args:
            host: Firefly III host URL.
            access_token: Personal Access Token.
            timeout: HTTP request timeout in seconds.
            httpx_client: Optional pre-configured httpx.Client instance.
        """
        self.host = host
        self.access_token = access_token

        if not self.host:
            raise ValueError("Firefly III host must be provided")

        if not self.access_token:
            raise ValueError("Access token must be provided")

        # Ensure host doesn't end with slash
        self.host = self.host.rstrip("/")

        # Set up HTTP client with default headers
        if httpx_client is not None:
            self.client = httpx_client
            # Update the base URL and headers for the provided client
            self.client.base_url = f"{self.host}/api/v1"
            self.client.headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/json",
                }
            )
        else:
            self.client = httpx.Client(
                timeout=timeout,
                base_url=f"{self.host}/api/v1",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/json",
                },
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP request to the Firefly III API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data for POST/PUT requests
            params: Query parameters

        Returns:
            JSON response data, or None for successful responses with no content

        Raises:
            FireflyAPIError: If the API returns an error
        """
        url = f"{self.host}/api/v1{endpoint}"

        try:
            response = self.client.request(
                method=method, url=url, json=data, params=params
            )

            # Log request details for debugging
            logger.debug(f"{method} {url} -> {response.status_code}")

            if response.status_code >= 400:
                error_message = f"HTTP {response.status_code}"
                error_data = None

                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    elif "error" in error_data:
                        error_message = error_data["error"]
                except Exception:
                    error_message = response.text or error_message

                raise FireflyAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=error_data,
                )

            # Handle successful responses that may have empty content (e.g., DELETE operations)
            if response.content.strip():
                try:
                    return response.json()
                except Exception:
                    # If JSON parsing fails but status is successful, return None
                    return None
            else:
                # Empty response body - return None for successful operations
                return None

        except httpx.RequestError as e:
            raise FireflyAPIError(f"Request failed: {str(e)}")
        except httpx.TimeoutException:
            raise FireflyAPIError("Request timed out")

    def get_accounts(
        self,
        type_filter: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> AccountsList:
        """
        Retrieve all accounts from Firefly III.

        Args:
            type_filter: Filter by account type (asset, expense, revenue, liability, etc.)
            page: Page number for pagination
            limit: Number of accounts per page

        Returns:
            AccountsList object containing account data
        """
        params = {}
        if type_filter:
            params["type"] = type_filter
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        response_data = self._make_request("GET", "/accounts", params=params)
        return AccountsList(**response_data)

    def get_account(self, account_id: int) -> Account:
        """
        Retrieve a specific account by ID.

        Args:
            account_id: The account ID

        Returns:
            Account object
        """
        response_data = self._make_request("GET", f"/accounts/{account_id}")
        return Account(**response_data["data"])

    def store_transaction(
        self,
        transactions: List[TransactionSplit],
        group_title: Optional[str] = None,
        error_if_duplicate_hash: bool = True,
        apply_rules: bool = True,
        fire_webhooks: bool = True,
    ) -> TransactionResponse:
        """
        Store a new transaction in Firefly III.

        Args:
            transactions: List of transaction splits
            group_title: Optional title for the transaction group
            error_if_duplicate_hash: Whether to error if duplicate hash detected
            apply_rules: Whether to apply rules to the transaction
            fire_webhooks: Whether to fire webhooks for the transaction        Returns:
            TransactionResponse object containing the created transaction
        """
        transaction_data = TransactionStore(
            error_if_duplicate_hash=error_if_duplicate_hash,
            apply_rules=apply_rules,
            fire_webhooks=fire_webhooks,
            group_title=group_title,
            transactions=transactions,
        )

        response_data = self._make_request(
            "POST", "/transactions", data=transaction_data.model_dump(exclude_none=True)
        )
        return TransactionResponse(**response_data)

    def create_withdrawal(
        self,
        amount: Union[str, float, Decimal],
        description: str,
        source_account_id: int,
        destination_account_id: int,
        date: Optional[Date] = None,
        category_name: Optional[str] = None,
        budget_name: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> TransactionResponse:
        """
        Create a withdrawal transaction (expense).

        Args:
            amount: Transaction amount (positive number)
            description: Transaction description
            source_account_id: ID of the source account (where money comes from)
            destination_account_id: ID of the destination account (where money goes to)
            date: Transaction date (defaults to today)
            category_name: Optional category name
            budget_name: Optional budget name
            notes: Optional notes
            tags: Optional list of tags
            **kwargs: Additional transaction split fields

        Returns:
            TransactionResponse object
        """
        if date is None:
            date = datetime.now().date()

        transaction_split = TransactionSplit(
            type=TransactionType.WITHDRAWAL,
            date=date,
            amount=amount,
            description=description,
            source_id=source_account_id,
            destination_id=destination_account_id,
            category_name=category_name,
            budget_name=budget_name,
            notes=notes,
            tags=tags,
        )

        return self.store_transaction([transaction_split], **kwargs)

    def create_deposit(
        self,
        amount: Union[str, float, Decimal],
        description: str,
        source_account_name: str,
        destination_account_id: int,
        date: Optional[Date] = None,
        category_name: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> TransactionResponse:
        """
        Create a deposit transaction (income).

        Args:
            amount: Transaction amount (positive number)
            description: Transaction description
            source_account_name: Name of the source account (where money comes from)
            destination_account_id: ID of the destination account (where money goes to)
            date: Transaction date (defaults to today)
            category_name: Optional category name
            notes: Optional notes
            tags: Optional list of tags
            **kwargs: Additional transaction split fields

        Returns:
            TransactionResponse object
        """
        if date is None:
            date = datetime.now().date()

        transaction_split = TransactionSplit(
            type=TransactionType.DEPOSIT,
            date=date,
            amount=amount,
            description=description,
            source_name=source_account_name,
            destination_id=destination_account_id,
            category_name=category_name,
            notes=notes,
            tags=tags,
            **kwargs,
        )

        return self.store_transaction([transaction_split], **kwargs)

    def create_transfer(
        self,
        amount: Union[str, float, Decimal],
        description: str,
        source_account_id: int,
        destination_account_id: int,
        date: Optional[Date] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> TransactionResponse:
        """
        Create a transfer transaction between accounts.

        Args:
            amount: Transaction amount (positive number)
            description: Transaction description
            source_account_id: ID of the source account (where money comes from)
            destination_account_id: ID of the destination account (where money goes to)
            date: Transaction date (defaults to today)
            notes: Optional notes
            tags: Optional list of tags
            **kwargs: Additional transaction split fields

        Returns:
            TransactionResponse object
        """
        if date is None:
            date = datetime.now().date()

        transaction_split = TransactionSplit(
            type=TransactionType.TRANSFER,
            date=date,
            amount=amount,
            description=description,
            source_id=source_account_id,
            destination_id=destination_account_id,
            notes=notes,
            tags=tags,
            **kwargs,
        )

        return self.store_transaction([transaction_split], **kwargs)

    def delete_transaction(self, transaction_group_id: int) -> None:
        """
        Delete a transaction group by ID.

        Args:
            transaction_group_id: The ID of the transaction group to delete

        Raises:
            FireflyAPIError: If the API returns an error
        """
        self._make_request("DELETE", f"/transactions/{transaction_group_id}")

    def delete_transaction_journal(self, transaction_journal_id: int) -> None:
        """
        Delete a specific transaction journal by ID.

        Args:
            transaction_journal_id: The ID of the transaction journal to delete

        Raises:
            FireflyAPIError: If the API returns an error
        """
        self._make_request("DELETE", f"/transaction-journals/{transaction_journal_id}")


# Convenience function for creating a client
def create_client(
    host: str, access_token: str, httpx_client: Optional[httpx.Client] = None
) -> FireflyClient:
    """
    Create a Firefly III client instance.

    Args:
        host: Firefly III host URL.
        access_token: Personal Access Token.
        httpx_client: Optional pre-configured httpx.Client instance.

    Returns:
        FireflyClient instance
    """
    return FireflyClient(
        host=host, access_token=access_token, httpx_client=httpx_client
    )
