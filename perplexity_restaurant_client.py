import os
import requests
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class PerplexityRestaurantClient:
    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("Please set your PERPLEXITY_API_KEY in the .env file")
        
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model = "llama-3.1-sonar-large-128k-online"  # Best model for web search
        
    def _make_request(self, query: str, max_tokens: int = 1000) -> str:
        """Make a request to Perplexity API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": query}],
            "temperature": 0.3,  # Lower temperature for more consistent results
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"Error making request to Perplexity API: {str(e)}"
        except KeyError as e:
            return f"Error parsing response: {str(e)}"
    
    def get_restaurants_by_location(self, location: str) -> str:
        """
        Get restaurant recommendations for a specific location using Perplexity's web search.
        
        Args:
            location: The city or area to find restaurants in
            
        Returns:
            A formatted string with restaurant recommendations
        """
        query = f"""
        Find the top 10 restaurants in {location}. For each restaurant, provide:
        - Restaurant name
        - Cuisine type
        - Price range ($, $$, $$$, or $$$$)
        - Brief description (1-2 sentences about atmosphere, specialty, or what makes it unique)
        - Neighborhood/area within the city
        - Overall rating if available
        
        Format the response in a clear, organized way. Use real, current information from web sources.
        """
        
        return self._make_request(query)
    
    def get_restaurant_reviews(self, location: str) -> str:
        """
        Get real restaurant reviews for restaurants in a specific location.
        
        Args:
            location: The city or area to find restaurant reviews for
            
        Returns:
            A formatted string with real restaurant reviews
        """
        query = f"""
        Find real customer reviews for restaurants in {location}. Provide:
        - Restaurant name
        - Reviewer name (if available)
        - Rating (1-5 stars)
        - Review text (actual customer review)
        - Date of review (if available)
        
        Include a mix of positive and negative reviews. Use real, current reviews from review sites like Yelp, Google Reviews, or TripAdvisor.
        Format the response clearly with 8-10 reviews total.
        """
        
        return self._make_request(query)
    
    def get_restaurant_reviews_by_name(self, restaurant_name: str, location: str) -> str:
        """
        Get reviews for a specific restaurant.
        
        Args:
            restaurant_name: Name of the restaurant
            location: City or area where the restaurant is located
            
        Returns:
            A formatted string with reviews for the specific restaurant
        """
        query = f"""
        Find real customer reviews for "{restaurant_name}" in {location}. Provide:
        - Restaurant name and location
        - 5-8 actual customer reviews with:
          - Reviewer name (if available)
          - Rating (1-5 stars)
          - Review text (actual customer review)
          - Date of review (if available)
        
        Use real, current reviews from review sites. Include both positive and negative reviews if available.
        """
        
        return self._make_request(query)
    
    def get_restaurant_vibe_analysis(self, location: str) -> str:
        """
        Analyze the overall restaurant scene and vibe in a location.
        
        Args:
            location: The city or area to analyze
            
        Returns:
            A formatted string with vibe analysis
        """
        query = f"""
        Analyze the restaurant scene and dining vibe in {location}. Provide insights on:
        - Overall dining atmosphere and culture
        - Popular cuisine types and trends
        - Price ranges and dining styles
        - Best neighborhoods for dining
        - Unique local specialties or must-try dishes
        - Dining hours and local customs
        
        Use current information from local sources, food blogs, and review sites.
        """
        
        return self._make_request(query)
    
    def interactive_chat(self):
        """Interactive chat interface for restaurant queries."""
        print("\n🍽️  Perplexity Restaurant Client Started!")
        print("Ask me about restaurants, reviews, or dining in any location!")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("🍴 Your question: ").strip()
                if query.lower() == 'quit':
                    break
                
                if not query:
                    continue
                
                print("\n🔍 Searching for information...")
                response = self._make_request(query)
                print(f"\n📋 Response:\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")

def main():
    """Main function to demonstrate the client."""
    try:
        client = PerplexityRestaurantClient()
        
        print("Perplexity Restaurant Client Demo")
        print("=" * 40)
        
        # Demo: Get restaurants for a location
        location = input("Enter a location to find restaurants: ").strip()
        if location:
            print(f"\n🔍 Finding restaurants in {location}...")
            restaurants = client.get_restaurants_by_location(location)
            print(f"\n📋 Restaurants in {location}:\n{restaurants}")
            
            # Ask if user wants reviews
            get_reviews = input(f"\nWould you like to see reviews for restaurants in {location}? (y/n): ").strip().lower()
            if get_reviews == 'y':
                print(f"\n🔍 Finding reviews for restaurants in {location}...")
                reviews = client.get_restaurant_reviews(location)
                print(f"\n📋 Reviews:\n{reviews}")
        
        # Ask if user wants interactive mode
        interactive = input("\nWould you like to enter interactive mode? (y/n): ").strip().lower()
        if interactive == 'y':
            client.interactive_chat()
            
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("Please set your PERPLEXITY_API_KEY in the .env file")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
