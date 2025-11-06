#!/usr/bin/env python3
"""
Flask app for serving restaurant recommendations with mood-based search.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our restaurant recommendation function
from food_restaurant_vibe import get_restaurants_by_mood
import asyncio
from restaurant_mood_azureai import RestaurantMoodAI
from services.session_generator import generate_room_id

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')

# Enable CORS for all routes
CORS(app)

# In-memory store for existing rooms (in production, use a database)
existing_rooms = set()

def convert_azure_to_ui_format(azure_result):
    """Convert Azure AI result to UI-compatible format."""
    if not azure_result.get("success"):
        return {
            "success": False,
            "error": azure_result.get("error", "Unknown error")
        }
    
    restaurants = []
    location = azure_result.get("location", "Unknown")
    mood = azure_result.get("mood", "Unknown")
    
    # Get restaurant names and reviews
    restaurant_names = azure_result.get("restaurants", [])
    restaurant_reviews = azure_result.get("restaurant_reviews", [])
    
    for i, name in enumerate(restaurant_names):
        review_data = restaurant_reviews[i] if i < len(restaurant_reviews) else {}
        
        # Extract review text
        review_text = "No review available"
        if review_data.get("success") and review_data.get("reviews"):
            # Take the first review and clean it up
            raw_review = review_data["reviews"][0]
            # Extract just the review text, removing metadata
            lines = raw_review.split('\n')
            review_lines = []
            for line in lines:
                if not line.startswith('**Rating:**') and not line.startswith('**Date:**') and not line.startswith('**Reviewer') and not line.startswith('![Image]') and not line.startswith('[View'):
                    if line.strip() and not line.startswith('Here') and not line.startswith('Feel free'):
                        review_lines.append(line.strip())
            if review_lines:
                review_text = ' '.join(review_lines[:3])  # Take first 3 lines
        
        # Create restaurant object
        restaurant = {
            "id": f"azure_{i}",
            "name": name,
            "cuisine": "Various",  # Azure doesn't provide cuisine info
            "price_range": "$$",   # Default
            "rating": 4.0,         # Default
            "review_count": 1,
            "address": f"{location}",  # Use location as address
            "phone": "N/A",
            "url": "https://google.com",
            "image_url": "https://via.placeholder.com/300x200?text=Restaurant",
            "coordinates": {"latitude": 40.5, "longitude": -74.4},  # Default NJ coordinates
            "categories": ["Restaurant"],
            "mood_match": f"This restaurant matches your '{mood}' mood perfectly.",
            "reviews": [
                {
                    "user_name": "Customer Review",
                    "rating": 4,
                    "text": review_text,
                    "source": "Restaurant Review",
                    "url": "https://google.com",
                    "time_created": "2025-01-18"
                }
            ]
        }
        restaurants.append(restaurant)
    
    return {
        "success": True,
        "location": location,
        "mood": mood,
        "total_restaurants": len(restaurants),
        "restaurants": restaurants,
        "timestamp": "2025-01-18T00:30:00"
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
        
        # Use Azure AI service to get restaurant recommendations
        async def get_azure_restaurants():
            endpoint = os.getenv('AZURE_AI_ENDPOINT', 'https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette')
            ai_client = RestaurantMoodAI(endpoint)
            
            result = await ai_client.call_agent_with_reviews(
                agent_name='RestaurantMoodFinder',
                location=location,
                mood=mood,
                get_reviews=True,
                review_agent_id='asst_yWj099Xl57apJnbE6wciCp8Y'
            )
            return result
        
        # Run the async function
        azure_result = asyncio.run(get_azure_restaurants())
        
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
