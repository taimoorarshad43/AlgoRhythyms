# Testing Multiplayer Mode

This guide will help you test the real-time multiplayer functionality.

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js and npm** installed
3. **Virtual environment** (recommended)

## Step 1: Install Backend Dependencies

```bash
# Navigate to project root
cd /home/tars43/UFA/MIT/AlgoRhythyms

# Activate virtual environment (if using one)
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

**Note:** If you encounter issues installing `eventlet`, you might need:
```bash
pip install eventlet --upgrade
```

## Step 2: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# This will install socket.io-client and other dependencies
```

## Step 3: Build Frontend (if needed)

If your Flask app serves from `frontend/dist`, you need to build:

```bash
# From frontend directory
npm run build
```

## Step 4: Start the Backend Server

```bash
# From project root directory
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Restarting with stat
```

The server will run on `http://localhost:5000`

## Step 5: Start Frontend Development Server (Optional)

If you want to run the frontend separately for development:

```bash
# From frontend directory
npm run dev
```

This typically runs on `http://localhost:5173` (Vite default)

**Note:** If Flask serves the built frontend from `frontend/dist`, you can skip this step and just access `http://localhost:5000` directly.

## Step 6: Testing Multiplayer Mode

### Test Setup

You'll need **at least 2 browser windows/tabs** to test multiplayer:

1. **Window 1** - Host (creates lobby)
2. **Window 2** - Player (joins lobby)

### Test Scenario 1: Create and Join Lobby

1. **In Window 1 (Host):**
   - Navigate to `http://localhost:5000` (or your frontend dev server URL)
   - Click "Multiplayer" in the navigation
   - Click "Create Lobby"
   - You should see a 6-character lobby ID (e.g., "ABC123")
   - Copy the lobby ID

2. **In Window 2 (Player):**
   - Navigate to the same URL
   - Click "Multiplayer"
   - Click "Join Existing Lobby"
   - Paste the lobby ID from Window 1
   - Click "Join Lobby"
   - You should see "Waiting for host to spin..." message

3. **Verify:**
   - Both windows should show the same lobby ID
   - Both windows should show player count (should be 2)
   - Window 1 should show "You are the host" with a crown icon
   - Window 2 should show "Waiting for host to spin..."

### Test Scenario 2: Host Spins Roulette

1. **In Window 1 (Host):**
   - Enter a location (e.g., "New York, NY")
   - Enter a mood (e.g., "Cozy")
   - Click "Spin the Wheel!"
   - Wait for restaurants to load and wheel to spin

2. **In Window 2 (Player):**
   - You should automatically see:
     - The same restaurants appear
     - The same selected restaurant
     - The same location and mood
   - The wheel should also spin (if animation is synced)

3. **Verify:**
   - Both windows show the same restaurant list
   - Both windows show the same selected restaurant
   - Window 2's spin button should be disabled (only host can spin)

### Test Scenario 3: Multiple Players

1. Open **Window 3** (another player)
2. Join the same lobby using the lobby ID
3. Verify:
   - Player count updates to 3 in all windows
   - When host spins, all 3 windows receive the same results

### Test Scenario 4: Leave Lobby

1. In any non-host window, click "Leave Lobby"
2. Verify:
   - That window returns to create/join screen
   - Other windows show updated player count
   - Lobby still exists (host is still there)

## Debugging Tips

### Check Browser Console

Open browser DevTools (F12) and check the Console tab for:
- WebSocket connection messages
- Socket events being received
- Any errors

You should see messages like:
```
Connected to server
Server message: {message: "Connected to server"}
Received lobby state: {...}
Received spin result: {...}
```

### Check Backend Logs

The Flask server will show:
- WebSocket connections
- API requests
- Any errors

Look for:
```
127.0.0.1 - - [timestamp] "POST /api/lobby/create HTTP/1.1" 200 -
127.0.0.1 - - [timestamp] "POST /api/lobby/join HTTP/1.1" 200 -
```

### Common Issues

1. **"Cannot connect to server"**
   - Check if backend is running on port 5000
   - Check browser console for WebSocket errors
   - Verify CORS settings

2. **"Lobby not found"**
   - Lobby might have expired (30 minutes inactivity)
   - Check lobby ID is correct (case-insensitive but should match)
   - Verify backend is running

3. **"Only the host can spin"**
   - This is correct behavior for non-host players
   - Only the lobby creator can spin

4. **Restaurants not syncing**
   - Check browser console for `spin_result` events
   - Verify WebSocket connection is active
   - Check backend logs for `host_spin` events

5. **Frontend not loading**
   - If using Flask to serve frontend, ensure `npm run build` was run
   - Check `frontend/dist` directory exists
   - Verify Flask `static_folder` path is correct

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] Frontend loads and connects to WebSocket
- [ ] Can create a lobby and get lobby ID
- [ ] Can join lobby with lobby ID
- [ ] Player count updates correctly
- [ ] Host can spin roulette
- [ ] Non-host players receive spin results
- [ ] All players see same restaurants
- [ ] All players see same selected restaurant
- [ ] Can leave lobby
- [ ] Lobby expires after 30 minutes of inactivity

## Advanced Testing

### Test Lobby Expiration

1. Create a lobby
2. Wait 30+ minutes without activity
3. Try to join with the same lobby ID
4. Should get "Lobby not found or expired" error

### Test Concurrent Spins

1. Host spins multiple times quickly
2. Verify all players receive each spin result
3. Verify no race conditions occur

### Test Network Issues

1. Disconnect one player's network
2. Reconnect
3. Verify they can rejoin and receive current state

## Next Steps

Once basic testing passes:
- Test with more players (3-5)
- Test on different devices/networks
- Test lobby expiration
- Monitor performance with multiple concurrent lobbies

