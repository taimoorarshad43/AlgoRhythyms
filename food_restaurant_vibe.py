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
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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

@mcp.tool()
def get_restaurants_by_mood(location: str, mood: str) -> str:
    """
    Get 10 restaurant suggestions for a given location based on mood criteria using real Yelp data and AI filtering.
    Returns structured JSON data perfect for frontend UI consumption.
    
    Args:
        location: The city or area to find restaurants in (e.g., "Raleigh, NC", "New York City", "San Francisco")
        mood: The mood or vibe you're looking for (e.g., "spicy and exciting", "romantic and cozy", "casual and fun", "upscale and elegant", "adventurous and unique")
    
    Returns:
        A JSON string containing structured restaurant data with reviews, perfect for frontend UI
    """
    try:
        # Get API keys
        yelp_api_key = os.environ.get('YELP_API_KEY')
        serpapi_key = os.environ.get('SERPAPI_KEY')
        
        if not yelp_api_key:
            return json.dumps({
                "error": "Yelp API key not found. Please set YELP_API_KEY in your environment variables."
            })
        
        # Step 1: Get real restaurants from Yelp API
        search_headers = {"Authorization": f"Bearer {yelp_api_key}"}
        search_params = {
            "term": "restaurants",
            "location": location,
            "limit": 50,  # Get more restaurants to filter from
            "sort_by": "rating",
            "radius": 10000  # 10km radius to get more options
        }
        
        search_response = requests.get("https://api.yelp.com/v3/businesses/search", 
                                     headers=search_headers, params=search_params)
        
        if search_response.status_code != 200:
            return json.dumps({
                "error": f"Failed to search restaurants: {search_response.status_code} - {search_response.text}"
            })
        
        businesses = search_response.json().get("businesses", [])
        
        if not businesses:
            return json.dumps({
                "error": f"No restaurants found for location: {location}"
            })
        
        # Step 2: Use Gemini to filter and match restaurants to mood
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Prepare restaurant data for Gemini
        restaurant_data = []
        for business in businesses:
            restaurant_data.append({
                "name": business["name"],
                "cuisine": [cat["title"] for cat in business["categories"]],
                "price_range": business.get("price", "N/A"),
                "rating": business["rating"],
                "review_count": business["review_count"],
                "address": " ".join(business["location"]["display_address"]),
                "neighborhood": business["location"].get("city", ""),
                "url": business.get("url", ""),
                "phone": business.get("phone", ""),
                "image_url": business.get("image_url", ""),
                "business_id": business["id"]
            })
        
        # Create prompt for mood-based filtering
        prompt = f"""
        You are a restaurant recommendation expert. I have real restaurant data from Yelp for {location}, and I need you to select and rank the top 10 restaurants that best match the mood: "{mood}".
        
        Here are the real restaurants from Yelp:
        {json.dumps(restaurant_data, indent=2)}
        
        Please select exactly 10 restaurants that best match the "{mood}" mood and provide:
        - Restaurant name (use the exact name from the data)
        - Cuisine type (from the categories)
        - Price range (from the data)
        - Rating and review count
        - Address
        - Why it matches the mood (brief explanation)
        
        IMPORTANT: Only use restaurants from the provided data. Do not make up restaurants.
        Return ONLY a valid JSON array with this exact structure:
        [
            {{
                "name": "Exact Restaurant Name from Data",
                "cuisine": "Primary Cuisine Type",
                "price_range": "Price from Data",
                "rating": "Rating from Data",
                "review_count": "Review Count from Data",
                "address": "Address from Data",
                "mood_match": "Why this restaurant matches the mood"
            }}
        ]
        
        Focus on restaurants that truly embody the "{mood}" experience based on their cuisine, price range, and other characteristics.
        Return only the JSON array, nothing else.
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Parse and format the response
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            selected_restaurants = json.loads(response_text)
            
            # Step 3: Get detailed information and reviews for selected restaurants
            final_restaurants = []
            
            for selected_restaurant in selected_restaurants:
                # Find the full restaurant data from Yelp
                full_restaurant_data = None
                for business in businesses:
                    if business["name"] == selected_restaurant["name"]:
                        full_restaurant_data = business
                        break
                
                if not full_restaurant_data:
                    continue
                
                # Get reviews for this restaurant using SERPAPI
                reviews = []
                try:
                    serpapi_key = os.environ.get('SERPAPI_KEY')
                    if serpapi_key:
                        # Search for reviews using SERPAPI
                        serpapi_params = {
                            "engine": "google",
                            "q": f"{selected_restaurant['name']} {location} reviews",
                            "api_key": serpapi_key,
                            "num": 10,
                            "gl": "us",  # Country
                            "hl": "en"  # Language
                        }
                        
                        serpapi_response = requests.get("https://serpapi.com/search.json", params=serpapi_params)
                        
                        if serpapi_response.status_code == 200:
                            serpapi_data = serpapi_response.json()
                            
                            # Extract review snippets from search results
                            organic_results = serpapi_data.get("organic_results", [])
                            review_snippets = []
                            
                            for result in organic_results[:5]:  # Check first 5 results
                                snippet = result.get("snippet", "")
                                title = result.get("title", "")
                                
                                # Look for review-like content
                                if snippet and len(snippet) > 30:
                                    # Try to extract rating from snippet
                                    rating = None
                                    if "⭐" in snippet or "stars" in snippet.lower():
                                        # Extract rating if present
                                        import re
                                        rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:⭐|stars?)', snippet, re.IGNORECASE)
                                        if rating_match:
                                            rating = float(rating_match.group(1))
                                    
                                    review_snippets.append({
                                        "source": result.get("source", "Unknown"),
                                        "title": title,
                                        "text": snippet,
                                        "rating": rating,
                                        "url": result.get("link", "")
                                    })
                            
                            # Take the first 3 review snippets
                            for i, review_snippet in enumerate(review_snippets[:3]):
                                reviews.append({
                                    "user_name": f"Reviewer {i+1}",
                                    "rating": review_snippet.get("rating", "N/A"),
                                    "text": review_snippet["text"],
                                    "source": review_snippet["source"],
                                    "url": review_snippet["url"],
                                    "time_created": "Recent"
                                })
                        
                        # If SERPAPI doesn't return enough reviews, try a more specific search
                        if len(reviews) < 3:
                            specific_params = {
                                "engine": "google",
                                "q": f'"{selected_restaurant["name"]}" "{location}" "review" OR "reviews"',
                                "api_key": serpapi_key,
                                "num": 10
                            }
                            
                            specific_response = requests.get("https://serpapi.com/search.json", params=specific_params)
                            
                            if specific_response.status_code == 200:
                                specific_data = specific_response.json()
                                specific_results = specific_data.get("organic_results", [])
                                
                                for result in specific_results:
                                    if len(reviews) >= 3:
                                        break
                                    
                                    snippet = result.get("snippet", "")
                                    if snippet and len(snippet) > 30 and snippet not in [r["text"] for r in reviews]:
                                        reviews.append({
                                            "user_name": f"Reviewer {len(reviews)+1}",
                                            "rating": "N/A",
                                            "text": snippet,
                                            "source": result.get("source", "Unknown"),
                                            "url": result.get("link", ""),
                                            "time_created": "Recent"
                                        })
                    
                    # If we still don't have enough reviews, add a fallback message
                    if len(reviews) < 3:
                        reviews.append({
                            "user_name": "System",
                            "rating": "N/A",
                            "text": f"Restaurant information available. Overall rating: {selected_restaurant['rating']} stars with {selected_restaurant['review_count']} reviews on Yelp.",
                            "source": "Yelp",
                            "url": full_restaurant_data.get("url", ""),
                            "time_created": "N/A"
                        })
                        
                except Exception as e:
                    print(f"Error fetching SERPAPI reviews for {selected_restaurant['name']}: {str(e)}")
                    # Fallback to basic restaurant info
                    reviews.append({
                        "user_name": "System",
                        "rating": selected_restaurant['rating'],
                        "text": f"Restaurant information available. Overall rating: {selected_restaurant['rating']} stars with {selected_restaurant['review_count']} reviews on Yelp.",
                        "source": "Yelp",
                        "url": full_restaurant_data.get("url", ""),
                        "time_created": "N/A"
                    })
                
                # Create structured restaurant object
                restaurant_obj = {
                    "id": full_restaurant_data["id"],
                    "name": selected_restaurant["name"],
                    "cuisine": selected_restaurant["cuisine"],
                    "price_range": selected_restaurant["price_range"],
                    "rating": float(selected_restaurant["rating"]),
                    "review_count": int(selected_restaurant["review_count"]),
                    "address": selected_restaurant["address"],
                    "phone": full_restaurant_data.get("phone", ""),
                    "url": full_restaurant_data.get("url", ""),
                    "image_url": full_restaurant_data.get("image_url", ""),
                    "coordinates": {
                        "latitude": full_restaurant_data["coordinates"]["latitude"],
                        "longitude": full_restaurant_data["coordinates"]["longitude"]
                    },
                    "categories": [cat["title"] for cat in full_restaurant_data["categories"]],
                    "mood_match": selected_restaurant["mood_match"],
                    "reviews": reviews
                }
                
                final_restaurants.append(restaurant_obj)
            
            # Create the final JSON response
            result = {
                "success": True,
                "location": location,
                "mood": mood,
                "total_restaurants": len(final_restaurants),
                "restaurants": final_restaurants,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Error parsing Gemini response: {str(e)}",
                "raw_response": response.text
            })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get mood-based restaurant suggestions: {str(e)}"
        })

@mcp.tool()
def get_restaurant_reviews(location: str) -> str:
    """
    Get restaurant reviews for a specific location. Returns a simple list of restaurants with their reviews.
    
    Args:
        location: The city or area to find restaurants and get reviews for (e.g., "Raleigh, NC", "New York City", "San Francisco")
    
    Returns:
        A formatted list of restaurants with reviews. Present this data simply and clearly to the user.
    """
    try:
        # Get API keys
        yelp_api_key = os.environ.get('YELP_API_KEY')
        serpapi_key = os.environ.get('SERPAPI_KEY')
        
        if not yelp_api_key:
            return json.dumps({
                "error": "Yelp API key not found. Please set YELP_API_KEY in your environment variables."
            })
        
        if not serpapi_key:
            return json.dumps({
                "error": "SERPAPI key not found. Please set SERPAPI_KEY in your environment variables."
            })
        
        # Step 1: Get restaurants from Yelp API
        search_headers = {"Authorization": f"Bearer {yelp_api_key}"}
        search_params = {
            "term": "restaurants",
            "location": location,
            "limit": 10,
            "sort_by": "rating",
            "radius": 5000  # 5km radius to get more local results
        }
        
        search_response = requests.get("https://api.yelp.com/v3/businesses/search", 
                                     headers=search_headers, params=search_params)
        
        if search_response.status_code != 200:
            return json.dumps({
                "error": f"Failed to search restaurants: {search_response.status_code} - {search_response.text}"
            })
        
        businesses = search_response.json().get("businesses", [])
        
        if not businesses:
            return json.dumps({
                "error": f"No restaurants found for location: {location}"
            })
        
        # Step 2: Get reviews for each restaurant using SERPAPI
        all_reviews = []
        
        for business in businesses[:10]:  # Limit to 10 restaurants
            business_name = business["name"]
            business_url = business.get("url", "")
            
            # Use SERPAPI to search for reviews
            serpapi_params = {
                "engine": "google",
                "q": f"{business_name} {location} reviews",
                "api_key": serpapi_key,
                "num": 10
            }
            
            try:
                serpapi_response = requests.get("https://serpapi.com/search.json", params=serpapi_params)
                
                if serpapi_response.status_code == 200:
                    serpapi_data = serpapi_response.json()
                    
                    # Extract review snippets from search results
                    organic_results = serpapi_data.get("organic_results", [])
                    review_snippets = []
                    
                    for result in organic_results[:3]:  # Take top 3 results
                        snippet = result.get("snippet", "")
                        if snippet and len(snippet) > 50:  # Filter out very short snippets
                            review_snippets.append(snippet)
                    
                    # Create a review entry
                    if review_snippets:
                        # Combine snippets into a review
                        combined_review = " ".join(review_snippets[:2])  # Take first 2 snippets
                        
                        all_reviews.append({
                            "restaurant_name": business_name,
                            "restaurant_id": business["id"],
                            "reviewer_name": "Customer Review",
                            "rating": business["rating"],
                            "review_text": combined_review[:500],  # Limit length
                            "date": "Recent",
                            "restaurant_rating": business["rating"],
                            "restaurant_price": business.get("price", "N/A"),
                            "restaurant_categories": [cat["title"] for cat in business["categories"]],
                            "restaurant_address": " ".join(business["location"]["display_address"]),
                            "restaurant_city": business["location"]["city"],
                            "restaurant_url": business_url
                        })
                    else:
                        # If no review snippets found, create a basic entry
                        all_reviews.append({
                            "restaurant_name": business_name,
                            "restaurant_id": business["id"],
                            "reviewer_name": "No reviews found",
                            "rating": business["rating"],
                            "review_text": f"Restaurant information available. Overall rating: {business['rating']} stars with {business['review_count']} reviews on Yelp.",
                            "date": "N/A",
                            "restaurant_rating": business["rating"],
                            "restaurant_price": business.get("price", "N/A"),
                            "restaurant_categories": [cat["title"] for cat in business["categories"]],
                            "restaurant_url": business_url
                        })
                
                else:
                    # SERPAPI request failed, still include restaurant info
                    all_reviews.append({
                        "restaurant_name": business_name,
                        "restaurant_id": business["id"],
                        "reviewer_name": "SERPAPI Error",
                        "rating": business["rating"],
                        "review_text": f"Could not fetch reviews via SERPAPI. Restaurant has {business['review_count']} reviews on Yelp. Error: {serpapi_response.status_code}",
                        "date": "N/A",
                        "restaurant_rating": business["rating"],
                        "restaurant_price": business.get("price", "N/A"),
                        "restaurant_categories": [cat["title"] for cat in business["categories"]],
                        "restaurant_url": business_url
                    })
                    
            except Exception as e:
                # Handle any errors in SERPAPI request
                all_reviews.append({
                    "restaurant_name": business_name,
                    "restaurant_id": business["id"],
                    "reviewer_name": "Error",
                    "rating": business["rating"],
                    "review_text": f"Error fetching reviews: {str(e)}. Restaurant has {business['review_count']} reviews on Yelp.",
                    "date": "N/A",
                    "restaurant_rating": business["rating"],
                    "restaurant_price": business.get("price", "N/A"),
                    "restaurant_categories": [cat["title"] for cat in business["categories"]],
                    "restaurant_url": business_url
                })
        
        if not all_reviews:
            return json.dumps({
                "error": f"No restaurants or reviews found for {location}"
            })
        
        # Format the response for better presentation
        response_text = f"🍽️ RESTAURANT REVIEWS NEAR {location.upper()}\n"
        response_text += f"Found {len(all_reviews)} restaurants within 5km (includes nearby areas)\n\n"
        
        for i, restaurant in enumerate(all_reviews, 1):
            response_text += f"{i}. {restaurant['restaurant_name']} ⭐ {restaurant['rating']}\n"
            response_text += f"   📍 {restaurant.get('restaurant_address', 'Address not available')}\n"
            response_text += f"   🍴 {', '.join(restaurant['restaurant_categories'])}\n"
            response_text += f"   💰 {restaurant.get('restaurant_price', 'Price not available')}\n"
            response_text += f"   📝 Review: {restaurant['review_text']}\n"
            response_text += f"   🔗 {restaurant.get('restaurant_url', '')}\n\n"
        
        response_text += "💡 Note: These restaurants are within 5km of your search location and include nearby areas."
        
        return response_text
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch restaurant reviews: {str(e)}"
        })


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")