# client.py
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import asyncio
import mcp.types as types
from mcp.shared.session import RequestResponder
import httpx
import logging
import json

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import ssl

import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

http_client = httpx.Client(verify=ssl_context)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key, http_client=http_client)

gpt_prompt_pricing = 0.0000020
# Cost per completion token
gpt_completion_pricing = 0.000008

def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mcp_client')


port = 8100

class LoggingCollector:
    def __init__(self):
        self.log_messages: list[types.LoggingMessageNotificationParams] = []
    async def __call__(self, params: types.LoggingMessageNotificationParams) -> None:
        self.log_messages.append(params)
        logger.info("MCP Log: %s - %s", params.level, params.data)

logging_collector = LoggingCollector()

async def message_handler(
    message: RequestResponder[types.ServerRequest, types.ClientResult]
    | types.ServerNotification
    | Exception,
) -> None:
    logger.info("Received message: %s", message)
    if isinstance(message, Exception):
        logger.error("Exception received!")
        raise message
    elif isinstance(message, types.ServerNotification):
        logger.info("NOTIFICATION: %s", message)
    elif isinstance(message, RequestResponder):
        logger.info("REQUEST_RESPONDER: %s", message)
    else:
        logger.info("SERVER_MESSAGE: %s", message)

def analyze_receipt(base64_image: str, accounts: list[str], tools):

    model_name = "gpt-4.1"
    
    functions = [convert_to_llm_tool(tool) for tool in tools]

    print("CALLING LLM")
    response = client.responses.create(
        model=model_name,
        instructions="",
        input=[
            {
                "role": "developer",
                "content": f"You create transaction in a bookeeping system. You can use the tools provided to you to create transactions. Here are the available accounts:\n\n{json.dumps(accounts, indent=2)}\n\n",
            },
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": "Analyze this image. If you find this is a receipt, determine transaction type, source and destination accounts, and create new transactions. If you can't find a suitable destiation account, use account 'Unknown'" },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
        tools=functions,
    )
    usage = response.usage.output_tokens * gpt_completion_pricing + response.usage.input_tokens * gpt_prompt_pricing

    print(f"Total USD burned: ${usage}")
    
    functions_to_call = []

    for tool_call in response.output:
        if tool_call.type != "function_call":
            continue

        name = tool_call.name
        args = json.loads(tool_call.arguments)

        if args['transactions']:
            # append type to all transactions:
            for transaction in args['transactions']:
                transaction['type'] = "withdrawal"

        functions_to_call.append({ "name": name, "args": args })

    return functions_to_call


def convert_to_llm_tool(tool: types.Tool):
    tool_schema = {
        "name": tool.name,
        "description": tool.description,
        "type": "function",
        "parameters": {
            "type": "object",
            "properties": tool.inputSchema["properties"]
        }
    }

    return tool_schema

async def main():
    logger.info("Starting client...")
    async with streamablehttp_client(f"http://localhost:{port}/mcp") as (
        read_stream,
        write_stream,
        session_callback,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
            logging_callback=logging_collector,
            message_handler=message_handler,
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available resources
            resources = await session.list_resources()
            print("LISTING RESOURCES")
            for resource in resources:
                print("Resource: ", resource)

            # List available tools
            tools = await session.list_tools()
            print("LISTING TOOLS")
            
            for tool in tools.tools:
                print("Tool: ", tool.name)
                print("Tool", tool.inputSchema["properties"])

            # Get accounts from Firefly III
            account_resource = await session.read_resource("firefly://accounts")
            accounts = []
            print("ACCOUNTS:")
            for account in account_resource.contents:
                if account.mimeType != "application/json":
                    logger.error(f"Unexpected MIME type: {account.mimeType}")
                    continue
                accounts = json.loads(account.text)
            
            # Analyze a receipt image
            # Find the testdata directory relative to this script
            script_dir = Path(__file__).parent
            testdata_dir = script_dir.parent.parent.parent / "testdata"

            image_path = testdata_dir / "photos" / "receipts" / "Shopping Aldi.jpg"
            if not image_path.exists():
                logger.error(f"Image file not found at {image_path}")
                return
              # Encode image to base64
            base64_image = encode_image_to_base64(image_path)
            logger.info(f"Analyzing image: {image_path.name}")

            available_accounts = [account['name'] for account in accounts]

            functions_to_call = analyze_receipt(base64_image, available_accounts, tools.tools)

            for function in functions_to_call:
                result = await session.call_tool(function["name"], arguments=function["args"])
                print("TOOLS result: ", result.content)
               

if __name__ == "__main__":
    # MCP client mode
    logger.info("Running MCP client...")
    asyncio.run(main())
