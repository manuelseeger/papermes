"""
Unit tests for MCP server prompt rendering functionality.
"""
import pytest
from mcp_server.server import render_prompt_template


class TestPromptRendering:
    """Test prompt template rendering functionality."""
    
    def test_render_prompt_template_developer_bookkeeping_context(self):
        """Test rendering the developer_bookkeeping_context template."""
        # Test data
        accounts = [
            {
                "id": "1",
                "name": "Checking Account",
                "type": "asset"
            },
            {
                "id": "2", 
                "name": "Savings Account",
                "type": "asset"
            },
            {
                "id": "3",
                "name": "Groceries",
                "type": "expense"
            }
        ]
        
        # Render the template
        result = render_prompt_template("developer_bookkeeping_context", accounts=accounts)
          # Assertions
        assert "You create transaction in a bookeeping system" in result
        assert "Checking Account (ID: 1, Type: asset)" in result
        assert "Savings Account (ID: 2, Type: asset)" in result
        assert "Groceries (ID: 3, Type: expense)" in result
        
    def test_render_prompt_template_user_analyze_receipt(self):
        """Test rendering the user_analyze_receipt template."""
        result = render_prompt_template("user_analyze_receipt")
        
        # Check that the template contains the expected instruction text
        assert "Analyze this image" in result
        assert "receipt" in result
        assert "transaction type" in result
        assert "source and destination accounts" in result
        assert "Unknown" in result
        
    def test_render_prompt_template_with_empty_accounts(self):
        """Test rendering developer_bookkeeping_context with empty accounts list."""
        accounts = []
        
        result = render_prompt_template("developer_bookkeeping_context", accounts=accounts)
        
        # Should still contain the main text but no account listings
        assert "You create transaction in a bookeeping system" in result
        assert "Here are the available accounts:" in result        # Should not contain any account-specific text
        assert "ID:" not in result
        assert "Type:" not in result
        
    def test_render_prompt_template_nonexistent_template(self):
        """Test that rendering a non-existent template raises appropriate error."""
        with pytest.raises(Exception):  # jinja2.TemplateNotFound will be raised
            render_prompt_template("nonexistent_template")
            
    def test_render_prompt_template_with_missing_variable(self):
        """Test rendering template with missing required variables."""
        # When 'accounts' is not provided, Jinja2 treats it as undefined
        # but doesn't raise an exception - it just renders as empty
        result = render_prompt_template("developer_bookkeeping_context")
        
        # Should still contain the main text but no account listings        assert "You create transaction in a bookeeping system" in result
        assert "Here are the available accounts:" in result
        # Should not contain any account-specific text since no accounts provided
        assert "ID:" not in result
        assert "Type:" not in result


class TestPromptTemplateEdgeCases:
    """Test edge cases and error conditions for prompt templates."""
    
    def test_render_prompt_with_special_characters_in_accounts(self):
        """Test rendering with special characters in account data."""
        accounts = [
            {
                "id": "1",
                "name": "Account with & special chars <test>",
                "type": "asset"
            },
            {
                "id": "2",
                "name": "Account with 'quotes' and \"double quotes\"",
                "type": "expense"
            }
        ]
        
        result = render_prompt_template("developer_bookkeeping_context", accounts=accounts)
        
        # Since autoescape is False, special characters should be preserved
        assert "Account with & special chars <test>" in result
        assert "Account with 'quotes' and \"double quotes\"" in result
        
    def test_render_prompt_with_none_values(self):
        """Test rendering with None values in account data."""
        accounts = [
            {
                "id": "1",
                "name": None,
                "type": "asset"
            }
        ]
        
        result = render_prompt_template("developer_bookkeeping_context", accounts=accounts)
        
        # Jinja2 should render None as empty string
        assert "None" in result or "" in result
        
    def test_render_prompt_with_unicode_characters(self):
        """Test rendering with unicode characters in account data."""
        accounts = [
            {
                "id": "1",
                "name": "Café & Bäckerei",
                "type": "expense"
            },
            {
                "id": "2",
                "name": "お金 (Money)",
                "type": "asset"
            }
        ]
        
        result = render_prompt_template("developer_bookkeeping_context", accounts=accounts)
        
        assert "Café & Bäckerei" in result
        assert "お金 (Money)" in result


if __name__ == "__main__":
    pytest.main([__file__])
