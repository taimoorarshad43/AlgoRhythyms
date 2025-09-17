import asyncio
import json
import os
import sys
from typing import Optional, Union, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import openai
from dotenv import load_dotenv

load_dotenv()

# Configure Perplexity API
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    raise ValueError("Please set your PERPLEXITY_API_KEY in the .env file")

# Initialize Perplexity client
perplexity_client = openai.OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

class MCPPerplexityClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model_name = "llama-3.1-sonar-large-128k-online"  # Perplexity's web search model
        self.available_prompts = []

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        if self.session:
            tools_response = await self.session.list_tools()
            prompts_response = await self.session.list_prompts()
            
            tools = tools_response.tools
            self.available_prompts = prompts_response.prompts
            
            print("\nConnected to server with tools:", [tool.name for tool in tools])
            print("Available prompts:", [prompt.name for prompt in self.available_prompts])

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        if not self.session:
            return []
        tools_result = await self.session.list_tools()
        return [{"name": tool.name, "description": tool.description, "parameters": tool.inputSchema} for tool in tools_result.tools]

    async def get_mcp_prompts(self) -> List[Dict[str, Any]]:
        if not self.session:
            return []
        prompts_result = await self.session.list_prompts()
        return [{"name": prompt.name, "description": prompt.description} for prompt in prompts_result.prompts]

    async def process_query(self, query: str, history: List[Dict]) -> str:
        """
        Process a query using Perplexity with conversation history and available MCP tools.
        
        Args:
            query: The user's new message.
            history: The list of previous messages and responses.
        
        Returns:
            The response from Perplexity.
        """
        available_tools = await self.get_mcp_tools()
        available_prompts = await self.get_mcp_prompts()
        
        # Build conversation history
        messages = []
        for turn in history:
            role = turn.get('role')
            content = turn.get('content')
            if role and content:
                # Convert to Perplexity format
                perplexity_role = "user" if role == "user" else "assistant"
                messages.append({"role": perplexity_role, "content": content})
            else:
                print(f"Warning: Skipping malformed history item: {turn}")
        
        # Add the new user query
        messages.append({"role": "user", "content": query})
        
        # Check if the query requires MCP tools
        tool_calls_needed = await self._check_for_tool_calls(query, available_tools)
        
        if tool_calls_needed:
            # Use MCP tools first
            tool_results = await self._execute_mcp_tools(query, available_tools)
            
            # Combine tool results with the original query
            enhanced_query = f"{query}\n\nTool Results:\n{tool_results}"
            messages.append({"role": "user", "content": enhanced_query})
        
        # Get response from Perplexity
        try:
            response = perplexity_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting response from Perplexity: {str(e)}"

    async def _check_for_tool_calls(self, query: str, available_tools: List[Dict[str, Any]]) -> bool:
        """Check if the query requires MCP tool calls."""
        tool_keywords = ["restaurant", "review", "location", "yelp", "food", "dining"]
        query_lower = query.lower()
        
        # Check if query mentions restaurants or reviews
        if any(keyword in query_lower for keyword in tool_keywords):
            return True
        
        # Check if any available tools are relevant
        for tool in available_tools:
            if any(keyword in tool["name"].lower() or keyword in tool["description"].lower() 
                   for keyword in tool_keywords):
                return True
        
        return False

    async def _execute_mcp_tools(self, query: str, available_tools: List[Dict[str, Any]]) -> str:
        """Execute relevant MCP tools and return results."""
        if not self.session:
            return "No MCP session available."
        
        results = []
        
        # Check for restaurant-related queries
        query_lower = query.lower()
        
        if "restaurant" in query_lower and "review" in query_lower:
            # Try to extract location from query
            location = self._extract_location_from_query(query)
            if location:
                try:
                    result = await self.session.call_tool(
                        "get_restaurant_reviews",
                        arguments={"location": location}
                    )
                    if result.content:
                        results.append(f"Restaurant Reviews for {location}:\n{result.content[0].text}")
                except Exception as e:
                    results.append(f"Error getting restaurant reviews: {str(e)}")
        
        elif "restaurant" in query_lower:
            # Try to extract location from query
            location = self._extract_location_from_query(query)
            if location:
                try:
                    result = await self.session.call_tool(
                        "get_restaurants_by_location",
                        arguments={"location": location}
                    )
                    if result.content:
                        results.append(f"Restaurants in {location}:\n{result.content[0].text}")
                except Exception as e:
                    results.append(f"Error getting restaurants: {str(e)}")
        
        return "\n\n".join(results) if results else "No relevant tools found."

    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """Extract location from user query."""
        # Simple location extraction - look for common patterns
        import re
        
        # Look for "in [location]" or "around [location]" patterns
        patterns = [
            r'in\s+([A-Za-z\s,]+?)(?:\?|$|\.)',
            r'around\s+([A-Za-z\s,]+?)(?:\?|$|\.)',
            r'near\s+([A-Za-z\s,]+?)(?:\?|$|\.)',
            r'for\s+([A-Za-z\s,]+?)(?:\?|$|\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common words
                location = re.sub(r'\b(restaurants?|food|dining|places?)\b', '', location, flags=re.IGNORECASE).strip()
                if location:
                    return location
        
        return None

    async def chat_loop(self):
        print("\nMCP Perplexity Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("This client can search the web for real-time information!")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query, history=[]) 
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client_perplexity.py <path_to_server_script>")
        sys.exit(1)

    client = MCPPerplexityClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
