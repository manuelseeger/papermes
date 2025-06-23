"""
Integration tests for LLM-based receipt analysis functionality.
These tests call the real OpenAI API to test actual LLM responses.
"""

import pytest
import os
from pathlib import Path
from mcp import types

# Import the functions we want to test
from mcp_server.client import analyze_receipt, encode_image_to_base64


class TestAnalyzeReceiptIntegration:
    """Integration test cases for the analyze_receipt function using real OpenAI API."""
    
    @pytest.fixture
    def sample_accounts(self):
        """Sample accounts list for testing."""
        return [
            "Checking Account",
            "Cash",
            "Groceries",
            "Pharmacy",
            "Food & Dining", 
            "Shopping",
            "Healthcare",
            "Household",
            "Entertainment",
            "Transportation",
            "Unknown"
        ]
    
    @pytest.fixture
    def sample_tools(self):
        """Sample MCP tools for testing."""
        return [
            types.Tool(
                name="create_transaction",
                description="Create a new transaction in Firefly III",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "amount": {"type": "number"},
                                    "source_name": {"type": "string"},
                                    "destination_name": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["transactions"]
                }
            )
        ]
    
    @pytest.fixture
    def testdata_dir(self):
        """Get the testdata directory path."""
        return Path(__file__).parent.parent.parent.parent / "testdata"
    
    def _get_receipt_path(self, testdata_dir: Path, filename: str) -> Path:
        """Helper to get receipt file path."""
        return testdata_dir / "photos" / "receipts" / filename

    @pytest.mark.parametrize("receipt_filename,expected_line_items", [
        ("Aldi Groceries and Ski Gear.jpg", [19.99, 9.99, 19.99, 5.99, 3.29, 0.69, 4.99]),
        ("Apotheke Elotrans.jpg", [8.45]),
        ("Coop Wine and non-food.jpg", [15.20, 1.20]),
        ("Letzimarkt Meat and Chips.jpg", [3.95, 18.40 ,20.10]),
    ])
    def test_analyze_receipt_real_llm(self, receipt_filename, expected_line_items, sample_accounts, sample_tools, testdata_dir):
        """
        Test analysis of receipts using real OpenAI API.
        
        This test verifies that:
        1. The analyze_receipt function successfully calls OpenAI
        2. Returns properly structured results
        3. Categorizes receipts appropriately
        4. Adds the required 'type' field to transactions
        
        Args:
            receipt_filename: The receipt image file to analyze
            expected_category: The expected category/account for this type of receipt
            sample_accounts: List of available accounts
            sample_tools: MCP tools for transaction creation
            testdata_dir: Path to test data directory
        """
        # Skip if OpenAI API key is not available
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        # Arrange
        receipt_path = self._get_receipt_path(testdata_dir, receipt_filename)
        
        if not receipt_path.exists():
            pytest.skip(f"Receipt file not found: {receipt_path}")
        
        base64_image = encode_image_to_base64(receipt_path)
        
        # Act
        result = analyze_receipt(base64_image, sample_accounts, sample_tools)
        
        # Assert basic structure
        assert isinstance(result, list), "Result should be a list"
        
        if len(result) > 0:
            # Verify the first result has expected structure
            first_result = result[0]
            assert 'name' in first_result, "Result should have 'name' field"
            assert 'args' in first_result, "Result should have 'args' field"
            assert first_result['name'] == 'create_transaction', "Should call create_transaction function"
              # Verify transactions structure
            if 'transactions' in first_result['args']:
                transactions = first_result['args']['transactions']
                assert isinstance(transactions, list), "Transactions should be a list"
                
                # Extract actual amounts from transactions
                actual_amounts = []
                
                for transaction in transactions:
                    # Verify required fields are present
                    assert 'type' in transaction, "Transaction should have 'type' field"
                    assert transaction['type'] == 'withdrawal', "Type should be set to 'withdrawal'"
                    
                    # Verify transaction has basic required fields
                    assert 'description' in transaction, "Transaction should have description"
                    assert 'amount' in transaction, "Transaction should have amount"
                    assert 'source_name' in transaction, "Transaction should have source_name"
                    assert 'destination_name' in transaction, "Transaction should have destination_name"
                    
                    # Verify amount is a number and positive
                    assert isinstance(transaction['amount'], (int, float)), "Amount should be numeric"
                    assert transaction['amount'] > 0, "Amount should be positive"
                    
                    # Collect actual amounts for comparison
                    actual_amounts.append(float(transaction['amount']))
                    
                    # Verify description is not empty
                    assert len(transaction['description'].strip()) > 0, "Description should not be empty"
                    
                    # Verify accounts are from the provided list or 'Unknown'
                    valid_accounts = sample_accounts + ['Unknown']
                    assert transaction['source_name'] in valid_accounts, f"Source account '{transaction['source_name']}' should be from available accounts"
                    assert transaction['destination_name'] in valid_accounts, f"Destination account '{transaction['destination_name']}' should be from available accounts"
                
                # Verify that the extracted amounts match the expected line items
                # Sort both lists to allow for different ordering
                actual_amounts_sorted = sorted(actual_amounts)
                expected_amounts_sorted = sorted(expected_line_items)
                
                assert len(actual_amounts) == len(expected_line_items), f"Expected {len(expected_line_items)} transactions, but got {len(actual_amounts)}"
                
                # Check if amounts match with a small tolerance for floating point precision
                for i, (actual, expected) in enumerate(zip(actual_amounts_sorted, expected_amounts_sorted)):
                    assert abs(actual - expected) < 0.01, f"Transaction amount {actual} does not match expected amount {expected} (difference: {abs(actual - expected)})"
        
        # Print results for manual verification
        print(f"\n=== Analysis Results for {receipt_filename} ===")
        print(f"Number of function calls: {len(result)}")
        
        for i, func_call in enumerate(result):
            print(f"\nFunction Call {i+1}:")
            print(f"Name: {func_call['name']}")
            
            if 'transactions' in func_call['args']:
                transactions = func_call['args']['transactions']
                print(f"Number of transactions: {len(transactions)}")
                
                for j, transaction in enumerate(transactions):
                    print(f"\nTransaction {j+1}:")
                    print(f"  Description: {transaction.get('description', 'N/A')}")
                    print(f"  Amount: {transaction.get('amount', 'N/A')}")
                    print(f"  Source: {transaction.get('source_name', 'N/A')}")
                    print(f"  Destination: {transaction.get('destination_name', 'N/A')}")
                    print(f"  Type: {transaction.get('type', 'N/A')}")
                    if 'date' in transaction:
                        print(f"  Date: {transaction['date']}")
        
        print(f"=== End Results for {receipt_filename} ===\n")

    def test_analyze_receipt_with_empty_accounts(self, sample_tools, testdata_dir):
        """Test analyze_receipt with empty accounts list."""
        # Skip if OpenAI API key is not available
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        # Arrange
        receipt_path = self._get_receipt_path(testdata_dir, "Aldi Groceries and Ski Gear.jpg")
        
        if not receipt_path.exists():
            pytest.skip(f"Receipt file not found: {receipt_path}")
        
        base64_image = encode_image_to_base64(receipt_path)
        empty_accounts = []
        
        # Act
        result = analyze_receipt(base64_image, empty_accounts, sample_tools)
        
        # Assert
        assert isinstance(result, list), "Result should be a list"
          # The LLM should still be able to process the receipt even without predefined accounts
        # It might use 'Unknown' or create its own account names
        print("\n=== Results with empty accounts ===")
        print(f"Number of function calls: {len(result)}")
        
        if len(result) > 0 and 'transactions' in result[0]['args']:
            for transaction in result[0]['args']['transactions']:
                print(f"Transaction: {transaction.get('description')} -> {transaction.get('destination_name')}")

    def test_encode_image_to_base64_helper(self, testdata_dir):
        """Test the encode_image_to_base64 helper function."""
        # Arrange
        receipt_path = self._get_receipt_path(testdata_dir, "Aldi Groceries and Ski Gear.jpg")
        
        if not receipt_path.exists():
            pytest.skip(f"Receipt file not found: {receipt_path}")
        
        # Act
        result = encode_image_to_base64(receipt_path)
        
        # Assert
        assert isinstance(result, str), "Should return a string"
        assert len(result) > 0, "Should not be empty"
        
        # Verify it looks like base64 (basic check)
        import base64
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0, "Decoded content should not be empty"
        except Exception as e:
            pytest.fail(f"Result does not appear to be valid base64: {e}")

    def test_encode_image_to_base64_nonexistent_file(self):
        """Test encode_image_to_base64 with non-existent file."""
        # Arrange
        nonexistent_path = Path("nonexistent_file.jpg")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64(nonexistent_path)
