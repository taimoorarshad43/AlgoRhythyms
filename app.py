#!/usr/bin/env python3
"""
Flask app for serving restaurant recommendations with mood-based search.
"""

# IMPORTANT: Use gevent for WebSocket support
# Gevent requires monkey-patching but is more compatible than eventlet
from gevent import monkey
monkey.patch_all()

import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

# Load environment variables
load_dotenv()

# Import our restaurant recommendation function
from food_restaurant_vibe import get_restaurants_by_mood
# Note: asyncio may conflict with eventlet, only import if needed
# import asyncio
from services.session_generator import generate_room_id
from services.lobby_manager import lobby_manager

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO with gevent (supports WebSockets)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

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
        
        # Create user message with location and mood - explicitly request reviews
        user_message = f"Find 6 restaurants in {location} that match a {mood} mood. Include 2 real reviews for each restaurant with reviewer names and source URLs."
        
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
        
        # Debug logging to help diagnose review issues
        if json_data:
            print(f"[DEBUG] Successfully extracted JSON with {len(json_data) if isinstance(json_data, list) else 'object'} items")
            if isinstance(json_data, list) and len(json_data) > 0:
                first_restaurant = json_data[0]
                has_reviews = "reviews" in first_restaurant if isinstance(first_restaurant, dict) else False
                print(f"[DEBUG] First restaurant has reviews field: {has_reviews}")
                if has_reviews and isinstance(first_restaurant, dict):
                    reviews_count = len(first_restaurant.get("reviews", []))
                    print(f"[DEBUG] First restaurant has {reviews_count} reviews")
        
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
        
        # Try multiple possible keys for reviews
        if not reviews_data:
            reviews_data = restaurant_data.get("review", restaurant_data.get("review_list", []))
        
        if isinstance(reviews_data, list):
            for review_item in reviews_data:
                if isinstance(review_item, dict):
                    # Try multiple possible keys for review text
                    review_text = (review_item.get("text") or 
                                 review_item.get("review") or 
                                 review_item.get("content") or 
                                 review_item.get("review_text") or
                                 review_item.get("snippet") or "")
                    
                    # Try multiple possible keys for reviewer name
                    reviewer_name = (review_item.get("user_name") or 
                                    review_item.get("reviewer") or 
                                    review_item.get("name") or 
                                    review_item.get("author") or
                                    review_item.get("reviewer_name") or
                                    "Anonymous")
                    
                    # Try multiple possible keys for URL
                    review_url = (review_item.get("url") or 
                                review_item.get("source_url") or 
                                review_item.get("link") or
                                review_item.get("source") or
                                restaurant_data.get("url", "https://google.com"))
                    
                    review_rating = review_item.get("rating", review_item.get("review_rating", 4))
                    
                    if review_text and len(review_text.strip()) > 0:
                        reviews.append({
                            "user_name": reviewer_name,
                            "rating": float(review_rating) if review_rating else 4,
                            "text": review_text.strip(),
                            "source": "Restaurant Review",
                            "url": review_url,
                            "time_created": (review_item.get("date") or 
                                           review_item.get("time_created") or 
                                           review_item.get("created_at") or
                                           datetime.now().strftime("%Y-%m-%d"))
                        })
                elif isinstance(review_item, str) and len(review_item.strip()) > 0:
                    # If review is just a string
                    reviews.append({
                        "user_name": "Customer Review",
                        "rating": 4,
                        "text": review_item.strip(),
                        "source": "Restaurant Review",
                        "url": restaurant_data.get("url", "https://google.com"),
                        "time_created": datetime.now().strftime("%Y-%m-%d")
                    })
        
        # If no reviews found, add a default one (but log it for debugging)
        if not reviews:
            print(f"[WARNING] No reviews found for restaurant: {name}")
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

@app.route('/api/lobby/create', methods=['POST'])
def create_lobby():
    """Create a new lobby and return the lobby ID."""
    try:
        data = request.get_json()
        host_id = data.get('host_id')
        
        if not host_id:
            return jsonify({
                'success': False,
                'error': 'host_id is required'
            }), 400
        
        # Generate unique lobby ID
        lobby_id = generate_room_id(existing_rooms)
        existing_rooms.add(lobby_id)
        
        # Create lobby
        lobby = lobby_manager.create_lobby(lobby_id, host_id)
        
        return jsonify({
            'success': True,
            'lobby_id': lobby_id,
            'host_id': host_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error creating lobby: {str(e)}'
        }), 500

@app.route('/api/lobby/join', methods=['POST'])
def join_lobby():
    """Join an existing lobby."""
    try:
        print(f"[DEBUG] Join lobby request received")
        data = request.get_json()
        print(f"[DEBUG] Request data: {data}")
        
        lobby_id = data.get('lobby_id', '').strip().upper()
        player_id = data.get('player_id')
        
        if not lobby_id:
            print(f"[DEBUG] Missing lobby_id")
            return jsonify({
                'success': False,
                'error': 'Lobby ID is required'
            }), 400
        
        if not player_id:
            print(f"[DEBUG] Missing player_id")
            return jsonify({
                'success': False,
                'error': 'player_id is required'
            }), 400
        
        print(f"[DEBUG] Attempting to join lobby {lobby_id} with player {player_id}")
        success, lobby, error = lobby_manager.join_lobby(lobby_id, player_id)
        print(f"[DEBUG] Join result: success={success}, error={error}")
        
        if success:
            print(f"[DEBUG] Successfully joined lobby, returning response")
            return jsonify({
                'success': True,
                'lobby_id': lobby_id,
                'is_host': lobby.host_id == player_id,
                'player_count': len(lobby.players),
                'restaurants': lobby.restaurants,
                'selected_restaurant': lobby.selected_restaurant,
                'location': lobby.location,
                'mood': lobby.mood
            })
        else:
            print(f"[DEBUG] Failed to join: {error}")
            return jsonify({
                'success': False,
                'error': error or 'Failed to join lobby'
            }), 400
    except Exception as e:
        print(f"[DEBUG] Exception in join_lobby: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error joining lobby: {str(e)}'
        }), 500

@app.route('/api/lobby/<lobby_id>/info', methods=['GET'])
def get_lobby_info(lobby_id):
    """Get lobby information."""
    try:
        info = lobby_manager.get_lobby_info(lobby_id.upper())
        if info:
            return jsonify({
                'success': True,
                **info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Lobby not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting lobby info: {str(e)}'
        }), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass

@socketio.on('join_lobby')
def handle_join_lobby(data):
    """Handle client joining a lobby room."""
    lobby_id = data.get('lobby_id', '').upper()
    player_id = data.get('player_id', request.sid)
    
    if not lobby_id:
        emit('error', {'message': 'Lobby ID required'})
        return
    
    lobby = lobby_manager.get_lobby(lobby_id)
    if not lobby:
        emit('error', {'message': 'Lobby not found'})
        return
    
    # Join the SocketIO room
    join_room(lobby_id)
    
    # Add player to lobby if not already there
    if player_id not in lobby.players:
        success, lobby, error = lobby_manager.join_lobby(lobby_id, player_id)
        if not success:
            emit('error', {'message': error or 'Failed to join lobby'})
            return
    
    # Notify others in the lobby
    emit('player_joined', {
        'player_id': player_id,
        'player_count': len(lobby.players)
    }, room=lobby_id, include_self=False)
    
    # Send current lobby state to the joining player
    emit('lobby_state', {
        'restaurants': lobby.restaurants,
        'selected_restaurant': lobby.selected_restaurant,
        'location': lobby.location,
        'mood': lobby.mood,
        'is_host': lobby.host_id == player_id
    })

@socketio.on('leave_lobby')
def handle_leave_lobby(data):
    """Handle client leaving a lobby room."""
    lobby_id = data.get('lobby_id', '').upper()
    player_id = data.get('player_id', request.sid)
    
    if lobby_id:
        leave_room(lobby_id)
        lobby_manager.leave_lobby(lobby_id, player_id)
        
        lobby = lobby_manager.get_lobby(lobby_id)
        if lobby:
            emit('player_left', {
                'player_id': player_id,
                'player_count': len(lobby.players)
            }, room=lobby_id)

@socketio.on('host_spin')
def handle_host_spin(data):
    """Handle host spinning the roulette."""
    lobby_id = data.get('lobby_id', '').upper()
    host_id = data.get('host_id', request.sid)
    restaurants = data.get('restaurants', [])
    selected_restaurant = data.get('selected_restaurant')
    location = data.get('location', '')
    mood = data.get('mood', '')
    
    if not lobby_id:
        emit('error', {'message': 'Lobby ID required'})
        return
    
    # Verify this is the host
    lobby = lobby_manager.get_lobby(lobby_id)
    if not lobby:
        emit('error', {'message': 'Lobby not found'})
        return
    
    if lobby.host_id != host_id:
        emit('error', {'message': 'Only the host can spin'})
        return
    
    # Update lobby state
    success, error = lobby_manager.update_lobby_state(
        lobby_id, host_id,
        restaurants=restaurants,
        selected_restaurant=selected_restaurant,
        location=location,
        mood=mood
    )
    
    if success:
        # Broadcast to all players in the lobby
        socketio.emit('spin_result', {
            'restaurants': restaurants,
            'selected_restaurant': selected_restaurant,
            'location': location,
            'mood': mood
        }, room=lobby_id)
    else:
        emit('error', {'message': error or 'Failed to update lobby state'})

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
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
