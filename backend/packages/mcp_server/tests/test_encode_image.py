from mcp_server.client import encode_image_to_base64
import pytest
from pathlib import Path


class TestEncodeImageToBase64:
    
    def _get_receipt_path(self, testdata_dir: Path, filename: str) -> Path:
        """Helper to get receipt file path."""
        return testdata_dir / "photos" / "receipts" / filename    
    
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
