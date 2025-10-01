import asyncio
import json
import os
from typing import Optional, Union, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

UNSUPPORTED_GEMINI_KEYWORDS = ["title", "additionalProperties", "default"]

def _clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively cleans a JSON schema to make it Gemini-compatible by
    removing unsupported fields and simplifying complex ones.
    """
    if isinstance(schema, dict):
        if "anyOf" in schema:
            return {"type": "object", "description": "This parameter has a union type."}

        cleaned_schema = {}
        for key, value in schema.items():
            if key in UNSUPPORTED_GEMINI_KEYWORDS:
                continue
            cleaned_schema[key] = _clean_schema_for_gemini(value)
        return cleaned_schema
    elif isinstance(schema, list):
        return [_clean_schema_for_gemini(item) for item in schema]
    else:
        return schema


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model_name = "gemini-2.5-flash"
        self.gemini_model = genai.GenerativeModel(self.model_name)
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

    async def get_mcp_tools(self) -> List[FunctionDeclaration]:
        if not self.session:
            return []
        tools_result = await self.session.list_tools()
        gemini_tools = []
        for tool in tools_result.tools:
            cleaned_parameters = _clean_schema_for_gemini(tool.inputSchema)
            gemini_tools.append(
                FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=cleaned_parameters,
                )
            )
        return gemini_tools

    async def get_mcp_prompts(self) -> List[FunctionDeclaration]:
        if not self.session:
            return []
        prompts_result = await self.session.list_prompts()
        gemini_prompts = []
        for prompt in prompts_result.prompts:
            parameters_schema = {
                "type": "object",
                "properties": self._convert_prompt_arguments(prompt.arguments) if hasattr(prompt, 'arguments') else {},
                "required": self._get_required_arguments(prompt.arguments) if hasattr(prompt, 'arguments') else []
            }
            cleaned_parameters_schema = _clean_schema_for_gemini(parameters_schema)
            
            gemini_prompts.append(
                FunctionDeclaration(
                    name=f"use_prompt_{prompt.name.lower().replace(' ', '_')}",
                    description=f"Use the '{prompt.name}' prompt template: {prompt.description}",
                    parameters=cleaned_parameters_schema,
                )
            )
        return gemini_prompts

    def _convert_prompt_arguments(self, arguments) -> Dict[str, Any]:
        if not arguments:
            return {}
        properties = {}
        for arg in arguments:
            if hasattr(arg, 'name') and hasattr(arg, 'type'):
                properties[arg.name] = {
                    "type": arg.type,
                    "description": getattr(arg, 'description', ''),
                }
        return properties

    def _get_required_arguments(self, arguments) -> List[str]:
        if not arguments:
            return []
        required = []
        for arg in arguments:
            if hasattr(arg, 'name') and getattr(arg, 'required', False):
                required.append(arg.name)
        return required

    async def get_mcp_tools_and_prompts(self) -> List[FunctionDeclaration]:
        tools = await self.get_mcp_tools()
        prompts = await self.get_mcp_prompts()
        return tools + prompts

    async def process_query(self, query: str, history: List[Dict]) -> str:
        """
        Process a query using Gemini with conversation history and available MCP tools.
        
        Args:
            query: The user's new message.
            history: The list of previous messages and responses from Gradio (as dicts).
        
        Returns:
            The response from Gemini.
        """
        available_tools = await self.get_mcp_tools_and_prompts()
        
        # --- MODIFIED SECTION START: Fix the history loop for dict format ---
        messages = []
        for turn in history:
            role = turn.get('role')
            content = turn.get('content')
            if role and content:
                # Gradio's history has 'user' and 'assistant', Gemini uses 'user' and 'model'
                gemini_role = "user" if role == "user" else "model"
                messages.append({"role": gemini_role, "parts": [content]})
            else:
                print(f"Warning: Skipping malformed history item: {turn}")
        
        # Append the new user query
        messages.append({"role": "user", "parts": [query]})
        # --- MODIFIED SECTION END ---

        response = await self.gemini_model.generate_content_async(
            messages,
            tools=available_tools,
            tool_config={"function_calling_config": "AUTO"}, 
        )

        if not response.candidates:
            return "No response from Gemini model."
        
        assistant_content_parts = response.candidates[0].content.parts
        tool_calls_detected = False
        tool_outputs = []
        for part in assistant_content_parts:
            if part.function_call:
                tool_calls_detected = True
                function_call = part.function_call
                
                print(f"Gemini requested tool call: {function_call.name} with args: {function_call.args}")

                tool_args = {k: v for k, v in function_call.args.items()}

                result = await self.session.call_tool(
                    function_call.name,
                    arguments=tool_args,
                )
                
                tool_output_content = result.content[0].text if result.content else "Tool executed successfully but returned no text content."
                tool_outputs.append({
                    "function_response": {
                        "name": function_call.name,
                        "response": {"content": tool_output_content}
                    }
                })
        
        if tool_calls_detected:
            messages.append({"role": "model", "parts": assistant_content_parts})
            messages.append({"role": "user", "parts": tool_outputs})
            
            print("Messages after tool call:", messages)

            final_response = await self.gemini_model.generate_content_async(
                messages,
                tools=available_tools,
                tool_config={"function_calling_config": "NONE"},
            )
            
            if final_response.candidates and final_response.candidates[0].content.parts:
                return final_response.candidates[0].content.parts[0].text
            else:
                return "Gemini did not provide a final text response after tool execution."

        if assistant_content_parts and assistant_content_parts[0].text:
            return assistant_content_parts[0].text
        else:
            return "Gemini provided a non-text response or no response directly."

    async def chat_loop(self):
        print("\nMCP Gemini Client Started!")
        print("Type your queries or 'quit' to exit.")

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
        print("Usage: python client_gemini.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())