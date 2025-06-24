#!/usr/bin/env python3
"""
Script to run the Papermes Host API server
"""

import sys
import uvicorn
from pathlib import Path

# Add backend directory to Python path for config import
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from config import get_config  # noqa: E402

# Get configuration
config = get_config()

if __name__ == "__main__":
    uvicorn.run(
        "src.host.host:app",
        host=config.host_api.host,
        port=config.host_api.port,
        reload=config.host_api.reload,
        log_level=config.host_api.log_level
    )
