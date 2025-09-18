# Restaurant Mood Finder - Flask UI

A simple web interface for finding restaurants based on location and mood criteria.

## Features

- 🍽️ **Mood-Based Search**: Find restaurants that match your dining mood
- 📍 **Location-Based**: Search in any city or area
- ⭐ **Real Reviews**: Get reviews from multiple sources (Google, Yelp, TripAdvisor)
- 🎨 **Modern UI**: Clean, responsive design with Bootstrap
- 📱 **Mobile Friendly**: Works on all devices

## How to Run

1. **Install Dependencies**:
   ```bash
   source venv/bin/activate
   pip install flask==2.3.3
   ```

2. **Start the Flask App**:
   ```bash
   python flask_app.py
   ```

3. **Open in Browser**:
   - Main app: http://localhost:5000
   - Demo results: http://localhost:5000/demo
   - Restaurant Roulette: http://localhost:5000/roulette

## Usage

### Search for Restaurants
1. Go to http://localhost:5000
2. Enter a location (e.g., "New York City", "Somerset, NJ")
3. Enter a mood (e.g., "spicy and exciting", "romantic and cozy")
4. Click "Find Restaurants"

### Restaurant Roulette
1. Go to http://localhost:5000/roulette
2. Enter a location (e.g., "New York City", "Somerset, NJ")
3. Enter a mood (e.g., "spicy and exciting", "romantic and cozy")
4. Click "Spin the Roulette!" to search for restaurants and get a roulette wheel
5. Spin the wheel to get a random restaurant review
6. Click "View Full Restaurant" to see the complete restaurant card
7. Click "Spin Again" to try another random selection

### Example Moods
- **Spicy & Exciting**: Hot, bold flavors with energetic atmosphere
- **Romantic & Cozy**: Intimate settings perfect for dates
- **Casual & Fun**: Relaxed atmosphere for friends and family
- **Upscale & Elegant**: Fine dining with sophisticated ambiance

## API Endpoints

### POST /search
Search for restaurants based on location and mood.

**Request Body**:
```json
{
  "location": "Somerset, NJ",
  "mood": "spicy and exciting"
}
```

**Response**:
```json
{
  "success": true,
  "location": "Somerset, NJ",
  "mood": "spicy and exciting",
  "total_restaurants": 10,
  "restaurants": [
    {
      "id": "yelp_business_id",
      "name": "Restaurant Name",
      "cuisine": "Mexican",
      "price_range": "$$",
      "rating": 4.5,
      "review_count": 150,
      "address": "123 Main St, City, State",
      "phone": "+1-555-123-4567",
      "url": "https://yelp.com/biz/restaurant-name",
      "image_url": "https://s3-media1.fl.yelpcdn.com/...",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "categories": ["Mexican", "Restaurants"],
      "mood_match": "This restaurant matches the mood because...",
      "reviews": [
        {
          "user_name": "Reviewer 1",
          "rating": 5,
          "text": "Amazing spicy food! The atmosphere is electric...",
          "source": "Google Reviews",
          "url": "https://google.com/reviews/...",
          "time_created": "Recent"
        }
      ]
    }
  ],
  "timestamp": "2025-01-18T00:30:00"
}
```

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Templates**: Jinja2
- **APIs**: Yelp API (restaurants), SERPAPI (reviews), Google Gemini (AI filtering)
- **Styling**: Bootstrap 5, Font Awesome icons, custom CSS

## File Structure

```
├── flask_app.py              # Main Flask application
├── food_restaurant_vibe.py   # Restaurant recommendation logic
├── templates/
│   ├── base.html            # Base template with common layout
│   ├── index.html           # Main search page
│   ├── results.html         # Results display page
│   └── roulette_search.html # Interactive roulette search interface
└── README_Flask_UI.md       # This file
```

## Demo

- **Regular Results**: Visit http://localhost:5000/demo to see sample results without making API calls
- **Roulette Interface**: Visit http://localhost:5000/roulette to try the interactive restaurant roulette with real data

## Notes

- The app uses real Yelp data for restaurant information
- Reviews are gathered from multiple sources via SERPAPI
- AI (Google Gemini) filters restaurants to match mood criteria
- All restaurant data is real and current
