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