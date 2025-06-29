import asyncio
import base64
import json
import logging
from pathlib import Path

import mcp.types as types
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.session import RequestResponder
from openai import OpenAI
from papermes_shared.shared import http_client

# Import dependencies - these will be handled by the package system
from .config import config

client = OpenAI(api_key=config.openai.api_key, http_client=http_client)

# Use pricing from config
gpt_prompt_pricing = config.openai.prompt_token_cost
gpt_completion_pricing = config.openai.completion_token_cost


def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Configure logging using config
logging.basicConfig(
    level=getattr(logging, config.app.log_level),
    format=config.app.log_format,
    datefmt=config.app.log_date_format,
)
logger = logging.getLogger("mcp_client")


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


async def analyze_receipt(
    base64_image: str, accounts: list[dict], tools, session: ClientSession
):
    """Analyze receipt using MCP prompts"""

    # Use model from config
    model_name = config.services.openai.model

    functions = [convert_to_llm_tool(tool) for tool in tools]

    # Get developer context prompt
    developer_prompt_result = await session.get_prompt(
        "developer_bookkeeping_context", arguments={"accounts": accounts}
    )
    developer_content = developer_prompt_result.messages[0].content

    # Get user analysis prompt
    user_prompt_result = await session.get_prompt("user_analyze_receipt")
    user_text = user_prompt_result.messages[0].content

    print("CALLING LLM")
    response = client.responses.create(
        model=model_name,
        instructions="",
        input=[
            {
                "role": "developer",
                "content": developer_content,
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_text},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            },
        ],
        tools=functions,
    )
    usage = (
        response.usage.output_tokens * gpt_completion_pricing
        + response.usage.input_tokens * gpt_prompt_pricing
    )

    print(f"Total USD burned: ${usage}")

    functions_to_call = []

    for tool_call in response.output:
        if tool_call.type != "function_call":
            continue

        name = tool_call.name
        args = json.loads(tool_call.arguments)

        if args["transactions"]:
            # append type to all transactions:
            for transaction in args["transactions"]:
                transaction["type"] = "withdrawal"

        functions_to_call.append({"name": name, "args": args})

    return functions_to_call


def convert_to_llm_tool(tool: types.Tool):
    tool_schema = {
        "name": tool.name,
        "description": tool.description,
        "type": "function",
        "parameters": {"type": "object", "properties": tool.inputSchema["properties"]},
    }

    return tool_schema


async def main():
    logger.info("Starting client...")
    async with streamablehttp_client(
        f"http://{config.mcp_server.host}:{config.mcp_server.port}/mcp"
    ) as (
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
                print("Resource: ", resource)  # List available tools
            tools = await session.list_tools()
            print("LISTING TOOLS")

            for tool in tools.tools:
                print("Tool: ", tool.name)
                print("Tool", tool.inputSchema["properties"])

            # List available prompts
            prompts = await session.list_prompts()
            print("LISTING PROMPTS")
            for prompt in prompts.prompts:
                print("Prompt: ", prompt.name)

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

            # Use the new prompt-based analysis
            functions_to_call = await analyze_receipt(
                base64_image, accounts, tools.tools, session
            )

            for function in functions_to_call:
                result = await session.call_tool(
                    function["name"], arguments=function["args"]
                )
                print("TOOLS result: ", result.content)


if __name__ == "__main__":
    # MCP client mode
    logger.info("Running MCP client...")
    asyncio.run(main())
