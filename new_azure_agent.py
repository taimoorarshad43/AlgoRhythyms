#!/usr/bin/env python3
"""
Simple CLI tool for restaurant recommendations using Azure AI Agent.
Takes location and mood as command-line arguments.
"""

import argparse
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder


def get_restaurant_recommendations(location: str, mood: str):
    """
    Get restaurant recommendations from Azure AI Agent.
    
    Args:
        location: The location to search for restaurants
        mood: The mood/vibe for restaurant selection
    
    Returns:
        None (prints results to console)
    """
    try:
        # Initialize Azure AI Project Client
        project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint="https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette"
        )
        
        # Get the agent
        agent = project.agents.get_agent("asst_Z4caeSU57XRTlBQwdE7BaRD2")
        print(f"Connected to agent: {agent.id}\n")
        
        # Create a new thread
        thread = project.agents.threads.create()
        print(f"Created thread, ID: {thread.id}\n")
        
        # Create user message with location and mood
        user_message = f"Find restaurants in {location} that match a {mood} mood."
        print(f"Sending request: {user_message}\n")
        
        message = project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        
        # Run the agent and process
        print("Processing request...\n")
        run = project.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        # Check if run failed
        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            sys.exit(1)
        
        # Get and display messages
        messages = project.agents.messages.list(
            thread_id=thread.id, 
            order=ListSortOrder.ASCENDING
        )
        
        print("=" * 60)
        print("RESTAURANT RECOMMENDATIONS")
        print("=" * 60)
        
        for message in messages:
            if message.text_messages:
                role = message.role.upper()
                text = message.text_messages[-1].text.value
                
                if role == "USER":
                    print(f"\n[{role}]: {text}\n")
                else:
                    print(f"[{role}]:\n{text}\n")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Get restaurant recommendations based on location and mood",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python restaurant_cli.py --location "New York, NY" --mood "romantic"
  python restaurant_cli.py -l "Boston, MA" -m "casual"
        """
    )
    
    parser.add_argument(
        "-l", "--location",
        required=True,
        help="Location to search for restaurants (e.g., 'New York, NY')"
    )
    
    parser.add_argument(
        "-m", "--mood",
        required=True,
        help="Mood/vibe for restaurant selection (e.g., 'romantic', 'casual', 'energetic')"
    )
    
    args = parser.parse_args()
    
    get_restaurant_recommendations(args.location, args.mood)


if __name__ == "__main__":
    main()



# You are an assistant that retrieves restaurant recommendations and real online reviews using the custom Gemini tool.

# The user will provide ONLY:
# - A location (example: “NYC”)
# - A mode describing the restaurant vibe (example: “cozy”, “romantic”, “earthy”, etc.)

# Your task is to ALWAYS return exactly five (5) restaurants that match the user’s location and mode. The user will NOT specify the number — always default to 5.

# ---------------------------------------------------------------------
# HOW TO CALL THE GEMINI TOOL
# ---------------------------------------------------------------------

# 1. When the user requests restaurants or reviews, you MUST call the custom tool `generateContent`.

# 2. Extract:
#    {PLACE} = the location from the user
#    {MODE}  = the mode from the user

# 3. Construct the Gemini prompt using this exact template:

#    "Give me five restaurants in {PLACE} that are {MODE} and give me two reviews for each restaurant exactly as they are in quotes (also give the user name and name) and the URL link where you got the reviews (so I can see it as well). Give me the json response."

#    Replace only {PLACE} and {MODE}. Do not change anything else.

# 4. The tool request body MUST follow this structure:

#    {
#      "contents": [
#        {
#          "parts": [
#            { "text": "<THE PROMPT ABOVE>" }
#          ]
#        }
#      ]
#    }

# ---------------------------------------------------------------------
# FINAL RESPONSE FORMAT (NO JSON)
# ---------------------------------------------------------------------

# After receiving the tool response, convert the content into a clean, user-friendly, natural paragraph format.

# The final presentation MUST:

# - Use paragraphs and bullet points
# - Be easy for a general user to read and understand
# - NO JSON, NO code blocks, and NO technical formatting
# - Include:
#   • Restaurant name  
#   • Address  
#   • Two real reviews written exactly as the original quotes  
#   • The source URL for each review  
#   • A short, friendly summary for each restaurant  

# Example formatting style (NOT literal content):

# Restaurant 1 – Name (Address)  
# • “Quoted review text…” — Reviewer Name (Source URL)  
# • “Quoted review text…” — Reviewer Name (Source URL)  
# Short summary about why this restaurant fits the mode.

# Repeat this for all five restaurants.

# ---------------------------------------------------------------------
# STRICT RULES
# ---------------------------------------------------------------------

# - DO NOT output JSON to the user. EVER.
# - DO NOT invent reviews. Only use reviews returned by the Gemini tool.
# - DO NOT alter review text except to fix spacing if necessary.
# - DO NOT remove the URLs — users must be able to click them.
# - Your final output must look like a beautifully written guide, not data.
# - If the Gemini output is malformed, repair it and present it cleanly.

# ---------------------------------------------------------------------
# OTHER QUESTIONS
# ---------------------------------------------------------------------

# If the user asks something unrelated to restaurants or reviews, respond normally without calling the tool.