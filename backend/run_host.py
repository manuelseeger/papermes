#!/usr/bin/env python3
"""
Script to run the Papermes Host API server
"""

import uvicorn
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    uvicorn.run(
        "src.host.host:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )
