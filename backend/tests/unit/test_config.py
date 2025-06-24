"""
Test configuration loading and validation.
"""

import os
import sys
import pytest
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from config import get_config, Config  # noqa: E402


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_config_loads_successfully(self):
        """Test that configuration loads without errors."""
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = get_config()
        
        # Test server defaults
        assert config.host_api.host == "0.0.0.0"
        assert config.host_api.port == 8090
        assert config.mcp_server.name == "papermes-mcp-server"
        assert config.mcp_server.host == "localhost"
        assert config.mcp_server.port == 8100
        
        # Test app defaults
        assert config.app.default_currency == "USD"
        assert config.app.log_level == "INFO"
        
        # Test http defaults
        assert config.http.timeout == 30.0
        assert config.http.ssl_verify is True
    
    def test_environment_variable_substitution(self):
        """Test that environment variables are substituted in config."""
        # Set a test environment variable
        test_host = "http://test-firefly.example.com"
        os.environ["PAPERMES_FIREFLY__HOST"] = test_host
        
        try:
            # Reload config to pick up the new environment variable
            from config import reload_config
            config = reload_config()
              # Check that the environment variable was substituted
            assert config.firefly.host == test_host
        finally:
            # Clean up
            if "PAPERMES_FIREFLY__HOST" in os.environ:
                del os.environ["PAPERMES_FIREFLY__HOST"]
    
    def test_path_utilities(self):
        """Test path utility methods."""
        config = get_config()
        
        # Test prompts directory path
        prompts_path = config.prompts_dir_path
        assert prompts_path.is_absolute()
        assert prompts_path.name == "prompts"
        
        # Test lib directory path
        lib_path = config.lib_dir_path
        assert lib_path.is_absolute()
        assert lib_path.name == "lib"
    
    def test_pydantic_settings_override(self):
        """Test that pydantic-settings environment override works."""
        # Test with nested environment variable
        test_port = "9999"
        os.environ["PAPERMES_MCP_SERVER__PORT"] = test_port
        
        try:
            # Reload config to pick up the new environment variable
            from config import reload_config
            config = reload_config()
              # Check that the nested environment variable was applied
            assert config.mcp_server.port == int(test_port)
        finally:
            # Clean up            if "PAPERMES_MCP_SERVER__PORT" in os.environ:
                del os.environ["PAPERMES_MCP_SERVER__PORT"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
