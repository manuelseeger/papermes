import sys
import logging
from pathlib import Path
from typing import List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel
from fastmcp import FastMCP
from datetime import datetime
import jinja2


# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from firefly_client import FireflyClient, FireflyAPIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("papermes-mcp-server", host="localhost", port=8100)

# Initialize Jinja2 environment for prompt templates
prompts_dir = Path(__file__).parent / "prompts"
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(prompts_dir),
    autoescape=False,  # We're working with text prompts, not HTML
    trim_blocks=True,
    lstrip_blocks=True
)

def render_prompt_template(template_name: str, **kwargs) -> str:
    """
    Render a Jinja2 template with the given parameters.
    
    Args:
        template_name: Name of the template file (with .jinja2 extension)
        **kwargs: Variables to pass to the template
        
    Returns:
        str: Rendered template string
    """
    try:
        template = jinja_env.get_template(f"{template_name}.jinja2")
        return template.render(**kwargs)
    except jinja2.TemplateNotFound:
        logger.error(f"Template not found: {template_name}")
        raise
    except jinja2.TemplateError as e:
        logger.error(f"Template rendering error: {e}")
        raise


class Account(BaseModel):
    """Account model"""
    id: str
    name: str
    type: str
    notes: Optional[str] = ""
    currency_code: Optional[str] = "USD"


class TransactionRequest(BaseModel):
    """Transaction request model for MCP tool"""
    type: str  # withdrawal, deposit, transfer
    source_account: Optional[str] = None  # account ID or name
    destination_account: Optional[str] = None  # account ID or name
    amount: Union[str, float, Decimal]
    currency_code: Optional[str] = "USD"
    description: str
    date: Optional[str] = None  # ISO date string, defaults to today
    category_name: Optional[str] = None
    budget_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@mcp.resource("firefly://accounts", mime_type="application/json")
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


@mcp.tool()
async def create_transactions(
    transactions: List[TransactionRequest],
    group_title: Optional[str] = None
) -> dict:
    """
    Create a transaction in Firefly III.
    
    Args:
        transactions: List of transaction splits to create
        group_title: Optional title for the transaction group
        
    Returns:
        dict: Success status and transaction details or error message
    """
    for tx_request in transactions:
        logger.info(f"Processing transaction request: {tx_request.model_dump()}")
    #return {
    #    "success": False,
    #    "error": "This tool is not implemented yet. Please implement the create_transaction function."
    #}
    try:
        # Create Firefly client (will use environment variables)
        with FireflyClient() as client:
            # Convert TransactionRequest objects to TransactionSplit objects
            transaction_splits = []
            
            for tx_request in transactions:
                # Determine source and destination based on transaction type
                source_id = None
                source_name = None
                destination_id = None
                destination_name = None
                
                if tx_request.type == "withdrawal":
                    # For withdrawals: source should be an account ID, destination should be an expense account name
                    source_name = tx_request.source_account
                    destination_name = tx_request.destination_account
                elif tx_request.type == "deposit":
                    # For deposits: source should be a revenue account name, destination should be an account ID
                    source_name = tx_request.source_account
                    destination_id = tx_request.destination_account
                elif tx_request.type == "transfer":
                    # For transfers: both should be account IDs
                    source_id = tx_request.source_account
                    destination_id = tx_request.destination_account
                else:
                    return {
                        "success": False,
                        "error": f"Invalid transaction type: {tx_request.type}. Must be 'withdrawal', 'deposit', or 'transfer'"
                    }
                
                # Create transaction split using the firefly_client's TransactionSplit model
                from firefly_client import TransactionSplit
                
                split = TransactionSplit(
                    type=tx_request.type,
                    date=tx_request.date or datetime.now().date().isoformat(),  # Will default to today in Firefly
                    amount=str(tx_request.amount),
                    description=tx_request.description,
                    source_id=source_id,
                    source_name=source_name,
                    destination_id=destination_id,
                    destination_name=destination_name,
                    currency_code=tx_request.currency_code,
                    category_name=tx_request.category_name,
                    budget_name=tx_request.budget_name,
                    notes=tx_request.notes,
                    tags=tx_request.tags
                )
                transaction_splits.append(split)
            
            # Create the transaction
            response = client.store_transaction(
                transactions=transaction_splits,
                group_title=group_title
            )
            
            return {
                "success": True,
                "transaction_id": response.data.id,
                "message": f"Transaction created successfully with {len(transaction_splits)} split(s)",
                "group_title": group_title
            }
            
    except FireflyAPIError as e:
        return {
            "success": False,
            "error": f"Firefly API Error: {e}",
            "status_code": e.status_code
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating transaction: {e}"
        }


@mcp.prompt()
async def developer_bookkeeping_context(accounts: List[dict]) -> str:
    """
    Generate the developer context prompt for bookkeeping system.
    
    Args:
        accounts: List of account dictionaries
        
    Returns:
        str: Rendered developer context prompt
    """
    return render_prompt_template(
        "developer_bookkeeping_context",
        accounts=accounts
    )


@mcp.prompt()
async def user_analyze_receipt() -> str:
    """
    Generate the user prompt for analyzing receipt images.
    
    Returns:
        str: Rendered user prompt for receipt analysis
    """
    return render_prompt_template("user_analyze_receipt")


def main():
    """Main entry point for the server"""
    try:
        logger.info("Starting Papermes MCP Server...")
        # Use run() which is actually synchronous
        mcp.run(transport="streamable-http")
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    # Use the main function directly
    main()