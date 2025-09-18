#!/usr/bin/env python3
"""
Flask app for serving restaurant recommendations with mood-based search.
"""

import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our restaurant recommendation function
from food_restaurant_vibe import get_restaurants_by_mood

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with search form."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_restaurants():
    """Search for restaurants based on location and mood."""
    try:
        data = request.get_json()
        location = data.get('location', '').strip()
        mood = data.get('mood', '').strip()
        
        if not location or not mood:
            return jsonify({
                'success': False,
                'error': 'Both location and mood are required'
            }), 400
        
        # Get restaurant recommendations
        result = get_restaurants_by_mood(location, mood)
        
        # Parse the JSON result
        try:
            restaurant_data = json.loads(result)
            return jsonify(restaurant_data)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Error parsing restaurant data: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/roulette')
def roulette_search():
    """Roulette search page with location and mood input."""
    return render_template('roulette_search.html')

@app.route('/demo')
def demo():
    """Demo page with sample data."""
    # Sample restaurant data for demo
    sample_data = {
        'success': True,
        'location': 'Somerset, NJ',
        'mood': 'spicy and exciting',
        'total_restaurants': 3,
        'restaurants': [
            {
                'id': 'demo_1',
                'name': 'Jalapeno And Cilantro Grill',
                'cuisine': 'Mexican',
                'price_range': '$$',
                'rating': 4.8,
                'review_count': 44,
                'address': '28 S Main St Milltown, NJ 08850',
                'phone': '+1-732-555-0123',
                'url': 'https://yelp.com/biz/jalapeno-cilantro-grill',
                'image_url': 'https://via.placeholder.com/300x200?text=Mexican+Restaurant',
                'coordinates': {'latitude': 40.4567, 'longitude': -74.4432},
                'categories': ['Mexican', 'Restaurants'],
                'mood_match': 'Mexican cuisine is known for its spicy dishes, offering an exciting flavor profile.',
                'reviews': [
                    {
                        'user_name': 'Sarah M.',
                        'rating': 5,
                        'text': 'Amazing spicy tacos! The atmosphere is electric and the food is incredibly flavorful. Perfect for a spicy food adventure!',
                        'source': 'Google Reviews',
                        'url': 'https://google.com/reviews/demo1',
                        'time_created': '2025-01-15'
                    },
                    {
                        'user_name': 'Mike R.',
                        'rating': 4,
                        'text': 'Great Mexican food with plenty of heat. The jalapeño poppers are incredible and the service is fast.',
                        'source': 'Yelp',
                        'url': 'https://yelp.com/reviews/demo1',
                        'time_created': '2025-01-10'
                    },
                    {
                        'user_name': 'Lisa K.',
                        'rating': 5,
                        'text': 'Perfect spot for spicy food lovers! The salsa is homemade and has the perfect kick. Highly recommend!',
                        'source': 'TripAdvisor',
                        'url': 'https://tripadvisor.com/reviews/demo1',
                        'time_created': '2025-01-08'
                    }
                ]
            },
            {
                'id': 'demo_2',
                'name': 'Ara\'s Hot Chicken',
                'cuisine': 'Halal',
                'price_range': '$$',
                'rating': 4.7,
                'review_count': 31,
                'address': '323 Raritan Ave Highland Park, NJ 08904',
                'phone': '+1-732-555-0456',
                'url': 'https://yelp.com/biz/aras-hot-chicken',
                'image_url': 'https://via.placeholder.com/300x200?text=Hot+Chicken',
                'coordinates': {'latitude': 40.4989, 'longitude': -74.4247},
                'categories': ['Halal', 'Chicken', 'Restaurants'],
                'mood_match': 'The name itself suggests spicy chicken, implying an exciting and flavorful experience.',
                'reviews': [
                    {
                        'user_name': 'Ahmed H.',
                        'rating': 5,
                        'text': 'Best hot chicken in the area! The spice levels are perfect and the chicken is always crispy and juicy.',
                        'source': 'Google Reviews',
                        'url': 'https://google.com/reviews/demo2',
                        'time_created': '2025-01-12'
                    },
                    {
                        'user_name': 'Jennifer L.',
                        'rating': 4,
                        'text': 'Great halal chicken with amazing spice options. The medium heat is perfect for most people.',
                        'source': 'Yelp',
                        'url': 'https://yelp.com/reviews/demo2',
                        'time_created': '2025-01-09'
                    },
                    {
                        'user_name': 'Carlos M.',
                        'rating': 5,
                        'text': 'Incredible spicy chicken! The hot level is not for the faint of heart but so worth it.',
                        'source': 'TripAdvisor',
                        'url': 'https://tripadvisor.com/reviews/demo2',
                        'time_created': '2025-01-07'
                    }
                ]
            },
            {
                'id': 'demo_3',
                'name': '蜀世冒菜 S&Y Mini HotPot',
                'cuisine': 'Hot Pot',
                'price_range': '$$',
                'rating': 4.7,
                'review_count': 26,
                'address': '1644 NJ-27 Edison, NJ 08817',
                'phone': '+1-732-555-0789',
                'url': 'https://yelp.com/biz/sy-mini-hotpot',
                'image_url': 'https://via.placeholder.com/300x200?text=Szechuan+Hot+Pot',
                'coordinates': {'latitude': 40.5187, 'longitude': -74.4121},
                'categories': ['Hot Pot', 'Chinese', 'Restaurants'],
                'mood_match': 'Szechuan hot pot is known for its intense spiciness and interactive dining experience, making it exciting.',
                'reviews': [
                    {
                        'user_name': 'David W.',
                        'rating': 5,
                        'text': 'Authentic Szechuan hot pot with incredible spice levels. The interactive cooking experience is so much fun!',
                        'source': 'Google Reviews',
                        'url': 'https://google.com/reviews/demo3',
                        'time_created': '2025-01-14'
                    },
                    {
                        'user_name': 'Amy T.',
                        'rating': 4,
                        'text': 'Great hot pot place with lots of spicy options. The broth is flavorful and the ingredients are fresh.',
                        'source': 'Yelp',
                        'url': 'https://yelp.com/reviews/demo3',
                        'time_created': '2025-01-11'
                    },
                    {
                        'user_name': 'Robert K.',
                        'rating': 5,
                        'text': 'Perfect for spice lovers! The mala broth is incredible and the dining experience is unique and exciting.',
                        'source': 'TripAdvisor',
                        'url': 'https://tripadvisor.com/reviews/demo3',
                        'time_created': '2025-01-06'
                    }
                ]
            }
        ],
        'timestamp': '2025-01-18T00:30:00'
    }
    
    return render_template('results.html', data=sample_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
