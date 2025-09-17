import os
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

from typing import Any
import httpx
import requests
from typing import Optional
import asyncio

# Create an MCP server
mcp = FastMCP("Restaurant Roulette")




# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")