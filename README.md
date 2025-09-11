# Name Roulette - Vite + React Frontend

A beautiful React frontend featuring a spinning roulette wheel to randomly select names. Built with Vite for lightning-fast development and optimized builds. The application is designed to work with a backend service for managing names.

## Features

- 🎯 **Interactive Roulette Wheel**: Smooth spinning animation with realistic physics
- 📝 **Name Management**: Add, remove, and manage names dynamically
- 🎨 **Beautiful UI**: Modern gradient design with glassmorphism effects
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔄 **Backend Integration**: Ready to connect to your backend service
- 🎉 **Winner Display**: Animated winner announcement
- ⚡ **Vite Powered**: Lightning-fast development server and optimized builds

## Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Open in Browser**
   The app will automatically open at `http://localhost:3000`

## Backend Integration

The app is designed to work with a backend service. It expects the following API endpoints:

### API Endpoints

- `GET /api/names` - Fetch all names
- `POST /api/names` - Add a new name
- `DELETE /api/names` - Remove a name

### Environment Configuration

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### API Response Format

**GET /api/names**
```json
{
  "names": ["Alice Johnson", "Bob Smith", "Carol Davis"]
}
```

**POST /api/names**
```json
{
  "name": "New Name"
}
```

**DELETE /api/names**
```json
{
  "name": "Name to Remove"
}
```

## Development Mode

If no backend is available, the app will automatically use mock data for development and testing.

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm start` - Alias for `npm run dev`

## Build for Production

```bash
npm run build
```

This creates a `dist` folder with optimized production files.

## Preview Production Build

```bash
npm run preview
```

This serves the production build locally for testing.

## Project Structure

```
src/
├── components/
│   ├── Roulette.jsx          # Main roulette wheel component
│   ├── Roulette.css          # Roulette styling
│   ├── NameManager.jsx       # Name management component
│   └── NameManager.css       # Name manager styling
├── services/
│   └── api.js               # API service layer
├── App.jsx                  # Main app component
├── App.css                  # App styling
├── main.jsx                 # Entry point (Vite convention)
└── index.css                # Global styles
```

## Customization

### Styling
- Modify CSS files to change colors, animations, and layout
- The roulette uses CSS transforms for smooth animations
- All colors are defined using CSS custom properties for easy theming

### Animation
- Roulette spin duration: 4 seconds
- Uses cubic-bezier easing for realistic physics
- Winner display includes pulsing animation

### Backend Integration
- Update `src/services/api.js` to modify API endpoints
- Change `API_BASE_URL` to point to your backend
- Mock data is available for development

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Vite Benefits

This project uses Vite instead of Webpack for several advantages:

- ⚡ **Lightning Fast**: Instant server start and hot module replacement
- 🚀 **Optimized Builds**: Faster build times with esbuild
- 📦 **Smaller Bundle**: Better tree-shaking and code splitting
- 🔧 **Zero Config**: Works out of the box with sensible defaults
- 🎯 **Modern**: Built for modern browsers with native ES modules

## License

MIT License - feel free to use and modify as needed.
