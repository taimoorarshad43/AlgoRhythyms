#!/usr/bin/env python3
"""
Flask app for serving restaurant recommendations with mood-based search.
"""

import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

# Load environment variables
load_dotenv()

# Import our restaurant recommendation function
from food_restaurant_vibe import get_restaurants_by_mood
import asyncio
from services.session_generator import generate_room_id

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')

# Enable CORS for all routes
CORS(app)

# In-memory store for existing rooms (in production, use a database)
existing_rooms = set()

def extract_json_from_text(text: str):
    """
    Extract JSON from text response. Handles JSON that might be embedded in markdown code blocks or plain text.
    Supports both JSON objects and arrays.
    
    Args:
        text: The text response that may contain JSON
    
    Returns:
        Parsed JSON object/array or None if extraction fails
    """
    # Try to find JSON in code blocks first (both objects and arrays)
    json_patterns = [
        r'```json\s*(\[.*?\])\s*```',  # JSON array in ```json``` blocks
        r'```json\s*(\{.*?\})\s*```',  # JSON object in ```json``` blocks
        r'```\s*(\[.*?\])\s*```',      # JSON array in ``` blocks
        r'```\s*(\{.*?\})\s*```',      # JSON object in ``` blocks
        r'(\[.*\])',                    # Any JSON array
        r'(\{.*\})',                    # Any JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # Try parsing the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    return None

def call_new_azure_agent(location: str, mood: str):
    """
    Call the new simplified Azure AI Agent and get restaurant recommendations.
    
    Args:
        location: The location to search for restaurants
        mood: The mood/vibe for restaurant selection
    
    Returns:
        Dictionary with success status and parsed JSON data or error message
    """
    try:
        # Initialize Azure AI Project Client
        project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint="https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette"
        )
        
        # Get the agent
        agent = project.agents.get_agent("asst_Z4caeSU57XRTlBQwdE7BaRD2")
        
        # Create a new thread
        thread = project.agents.threads.create()
        
        # Create user message with location and mood
        user_message = f"Find restaurants in {location} that match a {mood} mood."
        
        message = project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        
        # Run the agent and process
        run = project.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        # Check if run failed
        if run.status == "failed":
            return {
                "success": False,
                "error": f"Run failed: {run.last_error}"
            }
        
        # Get messages and extract assistant response
        messages = project.agents.messages.list(
            thread_id=thread.id, 
            order=ListSortOrder.ASCENDING
        )
        
        # Find the assistant's response (last non-user message)
        assistant_response = None
        for message in reversed(list(messages)):
            if message.role == "assistant" and message.text_messages:
                assistant_response = message.text_messages[-1].text.value
                break
        
        if not assistant_response:
            return {
                "success": False,
                "error": "No response from agent"
            }
        
        # Extract JSON from the response
        json_data = extract_json_from_text(assistant_response)
        
        if json_data:
            return {
                "success": True,
                "location": location,
                "mood": mood,
                "json_data": json_data,
                "raw_response": assistant_response
            }
        else:
            # If JSON extraction failed, return the raw response
            return {
                "success": False,
                "error": "Could not parse JSON from agent response",
                "raw_response": assistant_response
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error calling Azure agent: {str(e)}"
        }

def convert_azure_to_ui_format(azure_result):
    """Convert Azure AI result (with JSON data) to UI-compatible format."""
    if not azure_result.get("success"):
        return {
            "success": False,
            "error": azure_result.get("error", "Unknown error")
        }
    
    json_data = azure_result.get("json_data", {})
    location = azure_result.get("location", "Unknown")
    mood = azure_result.get("mood", "Unknown")
    
    restaurants = []
    
    # Handle different possible JSON structures from the agent
    # The agent might return a list of restaurants or an object with a restaurants key
    restaurant_list = []
    if isinstance(json_data, list):
        restaurant_list = json_data
    elif isinstance(json_data, dict):
        # Try common keys
        restaurant_list = json_data.get("restaurants", json_data.get("restaurant_list", []))
        # If it's a single restaurant object, wrap it in a list
        if not restaurant_list and "name" in json_data:
            restaurant_list = [json_data]
    
    # Process each restaurant from the JSON
    for i, restaurant_data in enumerate(restaurant_list):
        if not isinstance(restaurant_data, dict):
            continue
        
        # Extract restaurant information
        name = restaurant_data.get("name", restaurant_data.get("restaurant_name", f"Restaurant {i+1}"))
        address = restaurant_data.get("address", restaurant_data.get("location", location))
        cuisine = restaurant_data.get("cuisine", restaurant_data.get("cuisine_type", "Various"))
        price_range = restaurant_data.get("price_range", restaurant_data.get("price", "$$"))
        rating = restaurant_data.get("rating", restaurant_data.get("rating_score", 4.0))
        description = restaurant_data.get("description", restaurant_data.get("summary", ""))
        
        # Extract reviews - handle different possible structures
        reviews = []
        reviews_data = restaurant_data.get("reviews", [])
        
        if isinstance(reviews_data, list):
            for review_item in reviews_data:
                if isinstance(review_item, dict):
                    review_text = review_item.get("text", review_item.get("review", review_item.get("content", "")))
                    reviewer_name = review_item.get("user_name", review_item.get("reviewer", review_item.get("name", "Anonymous")))
                    review_url = review_item.get("url", review_item.get("source_url", "https://google.com"))
                    review_rating = review_item.get("rating", 4)
                    
                    if review_text:
                        reviews.append({
                            "user_name": reviewer_name,
                            "rating": review_rating,
                            "text": review_text,
                            "source": "Restaurant Review",
                            "url": review_url,
                            "time_created": review_item.get("date", review_item.get("time_created", datetime.now().strftime("%Y-%m-%d")))
                        })
                elif isinstance(review_item, str):
                    # If review is just a string
                    reviews.append({
                        "user_name": "Customer Review",
                        "rating": 4,
                        "text": review_item,
                        "source": "Restaurant Review",
                        "url": restaurant_data.get("url", "https://google.com"),
                        "time_created": datetime.now().strftime("%Y-%m-%d")
                    })
        
        # If no reviews found, add a default one
        if not reviews:
            reviews.append({
                "user_name": "Customer Review",
                "rating": 4,
                "text": description or f"This restaurant matches your '{mood}' mood perfectly.",
                "source": "Restaurant Review",
                "url": restaurant_data.get("url", "https://google.com"),
                "time_created": datetime.now().strftime("%Y-%m-%d")
            })
        
        # Create restaurant object
        restaurant = {
            "id": f"azure_{i}",
            "name": name,
            "cuisine": cuisine,
            "price_range": price_range if price_range in ["$", "$$", "$$$", "$$$$"] else "$$",
            "rating": float(rating) if rating else 4.0,
            "review_count": len(reviews),
            "address": address,
            "phone": restaurant_data.get("phone", restaurant_data.get("phone_number", "N/A")),
            "url": restaurant_data.get("url", restaurant_data.get("website", "https://google.com")),
            "image_url": restaurant_data.get("image_url", restaurant_data.get("image", "https://via.placeholder.com/300x200?text=Restaurant")),
            "coordinates": restaurant_data.get("coordinates", {
                "latitude": restaurant_data.get("latitude", 40.5),
                "longitude": restaurant_data.get("longitude", -74.4)
            }),
            "categories": restaurant_data.get("categories", [cuisine] if cuisine != "Various" else ["Restaurant"]),
            "mood_match": description or f"This restaurant matches your '{mood}' mood perfectly.",
            "reviews": reviews
        }
        restaurants.append(restaurant)
    
    return {
        "success": True,
        "location": location,
        "mood": mood,
        "total_restaurants": len(restaurants),
        "restaurants": restaurants,
        "timestamp": datetime.now().isoformat()
    }

@app.route('/')
def index():
    """Serve React app."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/search', methods=['POST'])
def search_restaurants():
    """API endpoint: Search for restaurants based on location and mood using Azure AI."""
    try:
        data = request.get_json()
        location = data.get('location', '').strip()
        mood = data.get('mood', '').strip()
        
        if not location or not mood:
            return jsonify({
                'success': False,
                'error': 'Both location and mood are required'
            }), 400
        
        # Use new simplified Azure AI agent to get restaurant recommendations
        azure_result = call_new_azure_agent(location, mood)
        
        # Convert Azure result to UI format
        restaurant_data = convert_azure_to_ui_format(azure_result)
        
        return jsonify(restaurant_data)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

# Catch-all route to serve React app for client-side routing
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for client-side routing."""
    # Check if the path is a file that exists
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Otherwise, serve index.html for client-side routing
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
