# Restaurant Finder

A Python CLI application that finds restaurants using the Yelp API. Simply provide a location and get a list of top-rated restaurants with ratings, reviews, and contact information.

## Features

- 🔍 **Location-based Search**: Find restaurants in any city or location
- ⭐ **Rating & Reviews**: See star ratings and review counts
- 📍 **Address Information**: Get full addresses for each restaurant
- 💰 **Price Range**: View price indicators ($, $$, $$$, $$$$)
- 🏷️ **Categories**: See restaurant categories and cuisine types
- 🔗 **Direct Links**: Access Yelp pages for each restaurant
- ⚙️ **Configurable**: Set default location and result limits

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Yelp API Key

1. Go to [Yelp Developers](https://www.yelp.com/developers)
2. Create an account and create a new app
3. Copy your API key

### 3. Create Environment File

Create a `.env` file in the project root:

```env
YELP_API_KEY=your_actual_yelp_api_key_here
DEFAULT_LOCATION=Raleigh, NC
```

Replace `your_actual_yelp_api_key_here` with your actual Yelp API key.

## Usage

### Basic Usage

```bash
# Use default location from .env file
python app.py

# Search in a specific location
python app.py "New York, NY"

# Limit results to 5 restaurants
python app.py "San Francisco, CA" --limit 5

# Get help
python app.py --help
```

### Command Line Options

- `location` (optional): The city or location to search in
  - If not provided, uses `DEFAULT_LOCATION` from `.env` file
  - Falls back to "Raleigh, NC" if no default is set

- `--limit` or `-l` (optional): Maximum number of restaurants to return
  - Default: 10
  - Range: 1-50 (Yelp API limit)

### Example Output

```
Found 10 restaurants in New York, NY:

1. Joe's Pizza (4.5⭐, 2847 reviews)
   Categories: Pizza, Italian
   Price: $$
   Address: 7 Carmine St, New York, NY 10014
   Link: https://www.yelp.com/biz/joes-pizza-new-york

2. Katz's Delicatessen (4.0⭐, 15234 reviews)
   Categories: Delis, Sandwiches, Jewish
   Price: $$
   Address: 205 E Houston St, New York, NY 10002
   Link: https://www.yelp.com/biz/katzs-delicatessen-new-york
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `YELP_API_KEY` | Your Yelp API key (required) | None |
| `DEFAULT_LOCATION` | Default search location | "Raleigh, NC" |

### API Limits

- Yelp API allows up to 50 results per request
- Rate limits apply based on your Yelp API plan
- Free tier typically allows 500 requests per day

## Troubleshooting

### Common Issues

1. **"Please set your YELP_API_KEY in the .env file"**
   - Make sure your `.env` file exists and contains a valid API key
   - Ensure the API key is not set to "YOUR_YELP_API_KEY"

2. **"API error: 401"**
   - Your API key is invalid or expired
   - Check your Yelp Developer account

3. **"API error: 429"**
   - You've exceeded the rate limit
   - Wait before making more requests

4. **No results found**
   - Try a different location format
   - Check if the location exists

## License

MIT License - feel free to use and modify as needed.
