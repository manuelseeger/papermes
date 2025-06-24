import asyncio
import sys
from pathlib import Path
from pyfirefly import Firefly

# Add backend directory to path for config import
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from config import get_config  # noqa: E402

# Get configuration
config = get_config()

async def main() -> None:
    """Run the example."""
    async with Firefly(
        api_url=config.firefly.host or "http://localhost:8080",
        api_key=config.firefly.access_token,
    ) as firefly:
        accounts = await firefly.get_accounts()

        
        print("Firefly accounts:", accounts)


if __name__ == "__main__":
    asyncio.run(main())