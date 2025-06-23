import sys
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastmcp import FastMCP

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from firefly_client import FireflyClient, FireflyAPIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("papermes-server")


class Account(BaseModel):
    """Account model - define the structure of account data"""
    id: str
    name: str
    type: str
    notes: Optional[str] = ""
    currency_code: Optional[str] = "USD"



@mcp.tool()
async def get_accounts() -> List[Account]:
    """
    Get accounts from Firefly III.
    
    Returns:
        List[Account]: List of account objects with mapped fields
    """
    try:
        # Create Firefly client (will use environment variables)
        with FireflyClient() as client:
            # Fetch accounts from Firefly III
            firefly_accounts = client.get_accounts()
            
            # Map Firefly account data to MCP Account model
            accounts = []
            for firefly_account in firefly_accounts.data:
                account = Account(
                    id=firefly_account.id,
                    name=firefly_account.attributes.name,
                    type=firefly_account.attributes.type,
                    notes=firefly_account.attributes.notes or "",
                    currency_code=firefly_account.attributes.currency_code or "USD"
                )
                accounts.append(account)
            
            return accounts
            
    except FireflyAPIError as e:
        # Handle Firefly API errors gracefully
        print(f"Firefly API Error: {e}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
        # Return empty list on error
        return []
    
    except Exception as e:
        # Handle other errors (missing environment variables, etc.)
        print(f"Error connecting to Firefly III: {e}")
        # Return empty list on error
        return []


def main():
    """Main entry point for the server"""
    try:
        logger.info("Starting Papermes MCP Server...")
        # Use run() which is actually synchronous
        mcp.run()
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    # Use the main function directly
    main()