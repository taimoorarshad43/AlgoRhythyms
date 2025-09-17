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
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Create an MCP server
mcp = FastMCP("Restaurant Roulette")

@mcp.tool()
def get_restaurants_by_location(location: str) -> str:
    """
    Get 10 restaurant suggestions for a given location using AI.
    
    Args:
        location: The city or area to find restaurants in (e.g., "Raleigh, NC", "New York City", "San Francisco")
    
    Returns:
        A JSON string containing 10 restaurant suggestions with details like name, cuisine type, price range, and brief description
    """
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create prompt for restaurant suggestions
        prompt = f"""
        You are a restaurant recommendation expert. Provide exactly 10 restaurant suggestions for {location}.
        
        For each restaurant, include:
        - Restaurant name
        - Cuisine type
        - Price range ($, $$, $$$, or $$$$)
        - Brief description (1-2 sentences about the atmosphere, specialty, or what makes it unique)
        - Neighborhood/area within the city
        
        IMPORTANT: Return ONLY a valid JSON array. Do not include any additional text, explanations, or disclaimers.
        
        Format the response as a JSON array with this exact structure:
        [
            {{
                "name": "Restaurant Name",
                "cuisine": "Cuisine Type",
                "price_range": "$",
                "description": "Brief description",
                "neighborhood": "Area/Neighborhood"
            }}
        ]
        
        Make sure the restaurants are realistic and well-known establishments that would actually exist in {location}.
        Return only the JSON array, nothing else.
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Return the generated content
        return response.text
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to generate restaurant suggestions: {str(e)}"
        })


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")