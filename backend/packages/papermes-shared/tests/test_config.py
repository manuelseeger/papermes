"""
Test configuration loading and validation.
"""

import pytest
from papermes_shared.config import BaseConfig as Config
from papermes_shared.config import get_config


class TestConfig:
    """Test configuration loading and validation."""

    def test_config_loads_successfully(self):
        """Test that configuration loads without errors."""
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
