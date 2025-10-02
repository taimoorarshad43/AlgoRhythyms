import argparse
import json
import sys
import os
import asyncio
from typing import Dict, Any, Optional
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread
from azure.ai.agents.models import BingGroundingTool
from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class RestaurantMoodAI:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.deployment_name = os.getenv('AZURE_AI_DEPLOYMENT_NAME', 'gpt-4')
        
        # Set environment variables for the Azure AI Agent SDK
        os.environ["AZURE_AI_AGENT_ENDPOINT"] = endpoint
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = self.deployment_name
    
    
    async def list_agents(self) -> Dict[str, Any]:
        """List all available agents in the project."""
        try:
            print("🔍 Discovering available agents...")
            
            async with DefaultAzureCredential() as creds:
                async with AzureAIAgent.create_client(credential=creds) as client:
                    agent_list = []
                    async for agent in client.agents.list_agents():
                        agent_info = {
                            "name": agent.name,
                            "description": getattr(agent, 'description', 'No description'),
                            "id": agent.id
                        }
                        agent_list.append(agent_info)
                    
                    return {
                        "success": True,
                        "agents": agent_list,
                        "count": len(agent_list)
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list agents: {str(e)}",
                "hint": "Make sure you're authenticated with Azure (try 'az login')"
            }
    
    async def call_agent(self, agent_name: str, location: str, mood: str) -> Dict[str, Any]:
        """Call an Azure AI Agent for restaurant recommendations."""
        try:
            print(f"🍽️  Calling agent '{agent_name}' for {mood} restaurants in {location}...")
            
            # Prepare the message content
            message_content = f"Find restaurants in {location} that match the mood: {mood}. Please provide detailed recommendations including restaurant names, cuisines, ratings, and why they match the requested mood."
            
            async with DefaultAzureCredential() as creds:
                async with AzureAIAgent.create_client(credential=creds) as client:
                    # Find the agent by name
                    found_agent = None
                    async for agent in client.agents.list_agents():
                        if agent.name == agent_name:
                            found_agent = agent
                            break
                    
                    if not found_agent:
                        return {
                            "success": False,
                            "error": f"Agent '{agent_name}' not found",
                            "hint": "Use --list-agents to see available agents"
                        }
                    
                    # Get agent definition and create agent instance
                    agent_definition = await client.agents.get_agent(found_agent.id)
                    agent = AzureAIAgent(client=client, definition=agent_definition)
                    
                    # Create a new thread and get response
                    thread = AzureAIAgentThread(client=client)
                    
                    try:
                        response = await asyncio.wait_for(
                            agent.get_response(messages=message_content, thread=thread),
                            timeout=60
                        )
                        
                        return {
                            "success": True,
                            "response": response,
                            "agent_name": agent_name,
                            "location": location,
                            "mood": mood
                        }
                        
                    except asyncio.TimeoutError:
                        return {
                            "success": False,
                            "error": "Request timed out after 60 seconds",
                            "hint": "The agent might be processing a complex request"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to call agent: {str(e)}",
                "hint": "Make sure you're authenticated with Azure (try 'az login')"
            }
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """Format the response for display."""
        if not result["success"]:
            error_msg = f"❌ Error: {result['error']}"
            if "hint" in result:
                error_msg += f"\n💡 Hint: {result['hint']}"
            return error_msg
        
        response = result["response"]
        location = result.get("location", "Unknown")
        mood = result.get("mood", "Unknown")
        agent_name = result.get("agent_name", "Unknown")
        
        output = f"✅ Successfully called agent '{agent_name}'\n"
        output += f"📍 Location: {location}\n"
        output += f"😊 Mood: {mood}\n"
        output += f"🤖 Agent Response:\n"
        
        # Handle different response types from Azure AI Agents
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            # Extract the actual content from the response
            output += response.message.content
        elif hasattr(response, 'content'):
            output += response.content
        elif hasattr(response, 'text'):
            output += response.text
        elif hasattr(response, '__dict__'):
            # Try to extract useful information from the object
            try:
                response_dict = {}
                for key, value in response.__dict__.items():
                    if not key.startswith('_'):
                        if hasattr(value, 'content'):
                            response_dict[key] = value.content
                        elif hasattr(value, '__dict__'):
                            response_dict[key] = str(value)
                        else:
                            response_dict[key] = str(value)
                output += json.dumps(response_dict, indent=2)
            except:
                output += str(response)
        else:
            output += str(response)
        
        return output

async def main():
    parser = argparse.ArgumentParser(description="Restaurant Mood AI - Find restaurants based on location and mood")
    parser.add_argument("--location", "-l", help="Location to search for restaurants")
    parser.add_argument("--mood", "-m", help="Mood/atmosphere for restaurant search")
    parser.add_argument("--agent", "-a", help="Specific agent name to call (optional)")
    parser.add_argument("--list-agents", action="store_true", help="List all available agents")
    parser.add_argument("--endpoint", "-e", 
                       default=os.getenv('AZURE_AI_ENDPOINT', 'https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette'), 
                       help="Azure AI project endpoint")
    
    args = parser.parse_args()
    
    # Initialize the AI client
    ai_client = RestaurantMoodAI(args.endpoint)
    
    try:
        if args.list_agents:
            # List available agents
            result = await ai_client.list_agents()
            if result["success"]:
                print("🤖 Available Agents:")
                for i, agent in enumerate(result["agents"], 1):
                    print(f"  {i}. {agent['name']}")
                    if agent['description'] != 'No description':
                        print(f"     Description: {agent['description']}")
                print(f"\nTotal: {result['count']} agents found")
            else:
                print(ai_client.format_response(result))
                sys.exit(1)
        else:
            # Call agent for restaurant recommendations
            if not args.agent:
                print("❌ Error: Agent name is required. Use --list-agents to see available agents.")
                print("Usage: python restaurant_mood_azureai.py --location 'New York' --mood 'romantic' --agent 'agent-name'")
                sys.exit(1)
            
            if not args.location or not args.mood:
                print("❌ Error: Both location and mood are required when calling an agent.")
                print("Usage: python restaurant_mood_azureai.py --location 'New York' --mood 'romantic' --agent 'agent-name'")
                sys.exit(1)
            
            result = await ai_client.call_agent(args.agent, args.location, args.mood)
            print(ai_client.format_response(result))
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())