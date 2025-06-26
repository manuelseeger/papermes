import pytest
from fastmcp import Client
from mcp_server.server import mcp


@pytest.fixture
def mcp_server():
    return mcp


@pytest.mark.asyncio
async def test_tool_functionality(mcp_server):
    # Pass the server directly to the Client constructor
    async with Client(mcp_server) as client:
        result = await client.call_tool("greet", {"name": "World"})
        assert result[0].text == "Hello, World!"


@pytest.mark.asyncio
async def test_get_user_prompt(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.get_prompt("user_analyze_receipt")
        assert "Analyze this image" in result.messages[0].content
        assert "receipt" in result.messages[0].content
        assert "transaction type" in result.messages[0].content
        assert "source and destination accounts" in result.messages[0].content
        assert "Unknown" in result.messages[0].content


@pytest.mark.asyncio
async def test_get_resource_accounts(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.read_resource("firefly://accounts")
        assert isinstance(result, list)
        assert len(result) > 0
        for account in result:
            assert "id" in account
            assert "name" in account
            assert "type" in account
            assert isinstance(account["id"], str)
            assert isinstance(account["name"], str)
            assert isinstance(account["type"], str)
