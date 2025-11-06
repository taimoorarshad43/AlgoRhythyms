import argparse
import json
import sys
import os
import asyncio
from typing import Dict, Any, Optional, List
from azure.identity.aio import DefaultAzureCredential
from azure.identity import DefaultAzureCredential as SyncDefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread
from azure.ai.agents.models import BingGroundingTool, ListSortOrder
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv
import re

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
    
    def get_restaurant_reviews(self, restaurant_name: str, review_agent_id: str = "asst_yWj099Xl57apJnbE6wciCp8Y") -> Dict[str, Any]:
        """Get 3-5 reviews for a specific restaurant using the RestaurantReviewFinder agent."""
        try:
            print(f"  📝 Fetching reviews for: {restaurant_name}...")
            
            # Create synchronous project client for the review agent
            project = AIProjectClient(
                credential=SyncDefaultAzureCredential(),
                endpoint=self.endpoint
            )
            
            # Get the review agent
            agent = project.agents.get_agent(review_agent_id)
            
            # Create a thread for this conversation
            thread = project.agents.threads.create()
            
            # Create a message asking for reviews
            message = project.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Please provide exactly 1 detailed review for the restaurant: {restaurant_name}. Include the rating, date, and reviewer name if available."
            )
            
            # Run the agent
            run = project.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            if run.status == "failed":
                return {
                    "success": False,
                    "restaurant": restaurant_name,
                    "error": f"Review agent run failed: {run.last_error}"
                }
            
            # Get the messages from the thread
            messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
            
            # Extract the assistant's response
            reviews = []
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    reviews.append(msg.text_messages[-1].text.value)
            
            return {
                "success": True,
                "restaurant": restaurant_name,
                "reviews": reviews
            }
            
        except Exception as e:
            return {
                "success": False,
                "restaurant": restaurant_name,
                "error": f"Failed to get reviews: {str(e)}"
            }
    
    def extract_restaurant_names(self, agent_response: str) -> List[str]:
        """Extract restaurant names from the agent's response."""
        # Try to parse restaurant names from various formats
        restaurants = []
        
        # Pattern 1: Look for numbered lists like "1. Restaurant Name" or "1) Restaurant Name"
        pattern1 = r'^\s*\d+[\.\)]\s*\*?\*?([^:\n\-]+?)(?:\*\*)?(?:\s*[-–—:]|$)'
        matches1 = re.findall(pattern1, agent_response, re.MULTILINE)
        
        # Pattern 2: Look for restaurant names in bold **Restaurant Name**
        pattern2 = r'\*\*([^*\n]+?)\*\*'
        matches2 = re.findall(pattern2, agent_response)
        
        # Use pattern 1 if found, otherwise use pattern 2
        if matches1:
            restaurants = [name.strip() for name in matches1]
        elif matches2:
            restaurants = [name.strip() for name in matches2]
        
        # Clean up and limit to 10 restaurants
        restaurants = [r for r in restaurants if len(r) > 2 and len(r) < 100][:10]
        
        return restaurants
    
    async def call_agent_with_reviews(self, agent_name: str, location: str, mood: str, 
                                     get_reviews: bool = False, review_agent_id: str = "asst_yWj099Xl57apJnbE6wciCp8Y") -> Dict[str, Any]:
        """Call the restaurant agent and optionally get reviews for each restaurant."""
        # First, get the restaurant recommendations
        result = await self.call_agent(agent_name, location, mood)
        
        if not result["success"]:
            return result
        
        # If reviews are not requested, return the original result
        if not get_reviews:
            return result
        
        # Extract response content
        response = result["response"]
        response_text = ""
        
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            response_text = response.message.content
        elif hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        # Extract restaurant names from the response
        print("\n🔍 Extracting restaurant names from recommendations...")
        restaurants = self.extract_restaurant_names(response_text)
        
        if not restaurants:
            print("⚠️  Could not extract restaurant names from response")
            return result
        
        print(f"✅ Found {len(restaurants)} restaurants\n")
        
        # Get reviews for each restaurant IN PARALLEL (much faster!)
        print("📝 Fetching 1 review for each restaurant in parallel...\n")
        
        # Create all review tasks at once
        review_tasks = [
            asyncio.to_thread(self.get_restaurant_reviews, restaurant, review_agent_id)
            for restaurant in restaurants
        ]
        
        # Run all tasks concurrently
        restaurant_reviews = await asyncio.gather(*review_tasks)
        
        # Add reviews to the result
        result["restaurants"] = restaurants
        result["restaurant_reviews"] = restaurant_reviews
        
        return result
    
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
        
        # Add reviews if available
        if "restaurant_reviews" in result:
            output += "\n\n" + "="*80 + "\n"
            output += "📝 RESTAURANT REVIEWS\n"
            output += "="*80 + "\n\n"
            
            for review_data in result["restaurant_reviews"]:
                restaurant = review_data.get("restaurant", "Unknown")
                output += f"🍽️  {restaurant}\n"
                output += "-" * 80 + "\n"
                
                if review_data.get("success"):
                    reviews = review_data.get("reviews", [])
                    if reviews:
                        for i, review in enumerate(reviews, 1):
                            output += f"{review}\n"
                            if i < len(reviews):
                                output += "\n"
                    else:
                        output += "No reviews found.\n"
                else:
                    output += f"❌ Error: {review_data.get('error', 'Unknown error')}\n"
                
                output += "\n"
        
        return output

async def main():
    parser = argparse.ArgumentParser(
        description="Restaurant Mood AI - Find restaurants with reviews based on location and mood",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python restaurant_mood_azureai.py --location "New York" --mood "romantic"
  python restaurant_mood_azureai.py -l "Boston" -m "casual"
  python restaurant_mood_azureai.py --location "San Francisco" --mood "upscale" --no-reviews
        """
    )
    
    # Arguments
    parser.add_argument("--location", "-l", 
                       help="Location to search for restaurants (e.g., 'New York', 'Boston')")
    parser.add_argument("--mood", "-m",
                       help="Mood/atmosphere for restaurant search (e.g., 'romantic', 'casual', 'upscale')")
    
    # Optional arguments with defaults
    parser.add_argument("--agent", "-a", 
                       default=os.getenv('AZURE_AI_AGENT_NAME', 'RestaurantMoodFinder'),
                       help="Agent name to use (default: RestaurantMoodFinder or AZURE_AI_AGENT_NAME env var)")
    parser.add_argument("--no-reviews", action="store_true",
                       help="Skip fetching reviews (only show restaurant recommendations)")
    parser.add_argument("--review-agent-id", 
                       default=os.getenv('AZURE_AI_REVIEW_AGENT_ID', 'asst_yWj099Xl57apJnbE6wciCp8Y'),
                       help="ID of the review agent (default: asst_yWj099Xl57apJnbE6wciCp8Y)")
    parser.add_argument("--endpoint", "-e", 
                       default=os.getenv('AZURE_AI_ENDPOINT', 'https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette'), 
                       help="Azure AI project endpoint")
    parser.add_argument("--list-agents", action="store_true", 
                       help="List all available agents and exit")
    
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
            # Call agent for restaurant recommendations with reviews (by default)
            if not args.location or not args.mood:
                print("❌ Error: Both --location and --mood are required.")
                print("Usage: python restaurant_mood_azureai.py --location 'New York' --mood 'romantic'")
                print("Use --list-agents to see available agents")
                sys.exit(1)
            
            print(f"🔍 Searching for {args.mood} restaurants in {args.location}...")
            if not args.no_reviews:
                print("📝 Reviews will be fetched for each restaurant\n")
            
            result = await ai_client.call_agent_with_reviews(
                args.agent, 
                args.location, 
                args.mood,
                get_reviews=not args.no_reviews,  # Reviews enabled by default
                review_agent_id=args.review_agent_id
            )
            print(ai_client.format_response(result))
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())