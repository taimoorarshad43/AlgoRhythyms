import requests
import argparse
import os
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('YELP_API_KEY')
if not API_KEY or API_KEY == "YOUR_YELP_API_KEY":
    raise ValueError("Please set your YELP_API_KEY in the config.env file")

ENDPOINT = "https://api.yelp.com/v3/businesses/search"

def get_restaurants(location, limit=10):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {
        "term": "restaurants",
        "location": location,
        "limit": limit,
        "sort_by": "rating"  # could also use "best_match" or "review_count"
    }
    
    response = requests.get(ENDPOINT, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    data = response.json()
    businesses = data.get("businesses", [])
    
    results = []
    for biz in businesses:
        results.append({
            "name": biz["name"],
            "rating": biz["rating"],
            "review_count": biz["review_count"],
            "categories": [c["title"] for c in biz["categories"]],
            "price": biz.get("price", "N/A"),
            "address": " ".join(biz["location"]["display_address"]),
            "url": biz["url"]
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Find restaurants using Yelp API')
    parser.add_argument('location', nargs='?', 
                       default=os.getenv('DEFAULT_LOCATION', 'Raleigh, NC'),
                       help='Location to search for restaurants (default: from config.env or "Raleigh, NC")')
    parser.add_argument('--limit', '-l', type=int, default=10,
                       help='Maximum number of restaurants to return (default: 10)')
    
    args = parser.parse_args()
    
    try:
        restaurants = get_restaurants(args.location, args.limit)
        print(f"Found {len(restaurants)} restaurants in {args.location}:\n")
        
        for idx, r in enumerate(restaurants, 1):
            print(f"{idx}. {r['name']} ({r['rating']}⭐, {r['review_count']} reviews)")
            print(f"   Categories: {', '.join(r['categories'])}")
            print(f"   Price: {r['price']}")
            print(f"   Address: {r['address']}")
            print(f"   Link: {r['url']}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

# Example usage:
if __name__ == "__main__":
    exit(main())
