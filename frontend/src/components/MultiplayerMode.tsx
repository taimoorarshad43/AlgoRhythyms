import React, { useState, useEffect, useRef } from 'react';
import { Users, Copy, Check, LogIn, Crown } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { WheelSpinner } from './WheelSpinner';
import { RestaurantResults } from './RestaurantResults';
import io, { Socket } from 'socket.io-client';

interface MultiplayerModeProps {
  players: string[];
  setPlayers: (players: string[]) => void;
  currentPlayerIndex: number;
  setCurrentPlayerIndex: (index: number) => void;
  location: string;
  setLocation: (location: string) => void;
  mood: string;
  setMood: (mood: string) => void;
  restaurants: any[];
  setRestaurants: (restaurants: any[]) => void;
  selectedRestaurant: any;
  setSelectedRestaurant: (restaurant: any) => void;
  isSpinning: boolean;
  setIsSpinning: (spinning: boolean) => void;
}

type LobbyMode = 'create' | 'join' | 'connected';

export function MultiplayerMode({
  location,
  setLocation,
  mood,
  setMood,
  restaurants,
  setRestaurants,
  selectedRestaurant,
  setSelectedRestaurant,
  isSpinning,
  setIsSpinning,
}: MultiplayerModeProps) {
  const [lobbyMode, setLobbyMode] = useState<LobbyMode>('create');
  const [lobbyId, setLobbyId] = useState('');
  const [joinLobbyId, setJoinLobbyId] = useState('');
  const [copied, setCopied] = useState(false);
  const [isHost, setIsHost] = useState(false);
  const [playerCount, setPlayerCount] = useState(1);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [playerIds, setPlayerIds] = useState<string[]>([]);
  const socketRef = useRef<Socket | null>(null);
  const lobbyIdRef = useRef<string>('');
  const playerIdRef = useRef<string>('');

  // Keep lobbyId in a ref so reconnect handlers see the latest value
  useEffect(() => {
    lobbyIdRef.current = lobbyId;
  }, [lobbyId]);

  // Generate unique player ID
  useEffect(() => {
    playerIdRef.current = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Initialize socket connection
  useEffect(() => {
    // Determine Socket.IO server URL
    // Use relative URL for production (Render deployment)
    // In development, Vite proxy will handle routing to Flask backend
    let socketUrl = window.location.origin;
    
    // Only use localhost in development if we're explicitly on a dev port
    // This allows Vite proxy to work in dev while using relative URLs in production
    if (window.location.hostname === 'localhost' && 
        window.location.port !== '' && 
        window.location.port !== '5000') {
      // In dev with separate frontend/backend, use localhost:5000
      socketUrl = 'http://localhost:5000';
    }
    
    console.log('🔌 Connecting to Socket.IO server at:', socketUrl);
    console.log('📍 Current origin:', window.location.origin, 'Port:', window.location.port);
    
    const socket = io(socketUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });
    socketRef.current = socket;

    const rejoinLobbyIfNeeded = () => {
      const currentLobbyId = lobbyIdRef.current;
      if (socketRef.current?.connected && currentLobbyId) {
        console.log('↩️ Rejoining lobby after reconnect:', currentLobbyId);
        socketRef.current.emit('join_lobby', {
          lobby_id: currentLobbyId,
          player_id: playerIdRef.current,
        });
      }
    };

    socket.on('connect', () => {
      console.log('✅ Connected to server, socket ID:', socket.id);
      setConnected(true);
      setError(null);
      rejoinLobbyIfNeeded();
    });

    socket.on('reconnect', (attempt) => {
      console.log('🔄 Reconnected to server after attempt:', attempt);
      rejoinLobbyIfNeeded();
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from server, reason:', reason);
      setConnected(false);
    });

    socket.on('connected', (data) => {
      console.log('Server message:', data);
    });

    socket.on('lobby_joined', (data) => {
      console.log('Successfully joined lobby room:', data);
      setPlayerCount(data.player_count || 1);
      // Add current player to the list
      if (playerIdRef.current) {
        setPlayerIds(prev => {
          if (!prev.includes(playerIdRef.current)) {
            return [...prev, playerIdRef.current];
          }
          return prev;
        });
      }
    });

    socket.on('lobby_state', (data) => {
      console.log('Received lobby state:', data);
      if (data.restaurants && data.restaurants.length > 0) {
        setRestaurants(data.restaurants);
      }
      if (data.selected_restaurant) {
        setSelectedRestaurant(data.selected_restaurant);
      }
      if (data.location) {
        setLocation(data.location);
      }
      if (data.mood) {
        setMood(data.mood);
      }
      setIsHost(data.is_host || false);
    });

    socket.on('spin_result', (data) => {
      console.log('Received spin result:', data);
      setRestaurants(data.restaurants || []);
      setSelectedRestaurant(data.selected_restaurant || null);
      setLocation(data.location || '');
      setMood(data.mood || '');
      setIsSpinning(false);
    });

    socket.on('player_joined', (data) => {
      console.log('Player joined:', data);
      setPlayerCount(data.player_count || 1);
      // Add the new player to the list
      if (data.player_id && !playerIds.includes(data.player_id)) {
        setPlayerIds(prev => [...prev, data.player_id]);
      }
    });

    socket.on('player_left', (data) => {
      console.log('Player left:', data);
      setPlayerCount(data.player_count || 1);
      // Remove the player from the list
      if (data.player_id) {
        setPlayerIds(prev => prev.filter(id => id !== data.player_id));
      }
    });

    socket.on('error', (data) => {
      console.error('Socket error:', data);
      setError(data.message || 'An error occurred');
      setLoading(false);
    });

    socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error);
      setError(`Connection failed: ${error.message || 'Unable to connect to server. Make sure Flask is running on port 5000.'}`);
      setConnected(false);
      setLoading(false);
    });

    // Set a timeout to show error if connection takes too long
    const connectionTimeout = setTimeout(() => {
      if (!socket.connected) {
        console.warn('Connection timeout - socket not connected after 5 seconds');
        setError('Connection timeout. Make sure the Flask server is running on port 5000.');
      }
    }, 5000);

    // Cleanup on unmount
    return () => {
      clearTimeout(connectionTimeout);
      if (socket.connected) {
        socket.disconnect();
      }
    };
  }, []);

  const createLobby = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/lobby/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          host_id: playerIdRef.current,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setLobbyId(data.lobby_id);
        lobbyIdRef.current = data.lobby_id;
        setIsHost(true);
        setLobbyMode('connected');
        setPlayerIds([playerIdRef.current]);
        
        // Join the socket room - wait for connection if needed
        if (socketRef.current) {
          if (socketRef.current.connected) {
            socketRef.current.emit('join_lobby', {
              lobby_id: data.lobby_id,
              player_id: playerIdRef.current,
            });
          } else {
            // Wait for connection before joining
            socketRef.current.once('connect', () => {
              socketRef.current?.emit('join_lobby', {
                lobby_id: data.lobby_id,
                player_id: playerIdRef.current,
              });
            });
          }
        }
      } else {
        setError(data.error || 'Failed to create lobby');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create lobby');
    } finally {
      setLoading(false);
    }
  };

  const joinLobby = async () => {
    if (!joinLobbyId.trim()) {
      setError('Please enter a lobby ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      console.log('Attempting to join lobby:', joinLobbyId.trim().toUpperCase());
      
      // Add timeout to fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch('/api/lobby/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lobby_id: joinLobbyId.trim().toUpperCase(),
          player_id: playerIdRef.current,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Join lobby response:', data);
      if (data.success) {
        setLobbyId(data.lobby_id);
        lobbyIdRef.current = data.lobby_id;
        setIsHost(data.is_host || false);
        setPlayerCount(data.player_count || 1);
        setLobbyMode('connected');
        setPlayerIds([playerIdRef.current]);
        
        // Set existing state if available
        if (data.restaurants && data.restaurants.length > 0) {
          setRestaurants(data.restaurants);
        }
        if (data.selected_restaurant) {
          setSelectedRestaurant(data.selected_restaurant);
        }
        if (data.location) {
          setLocation(data.location);
        }
        if (data.mood) {
          setMood(data.mood);
        }
        
        // Join the socket room - wait for connection if needed
        if (socketRef.current) {
          if (socketRef.current.connected) {
            socketRef.current.emit('join_lobby', {
              lobby_id: data.lobby_id,
              player_id: playerIdRef.current,
            });
          } else {
            // Wait for connection before joining
            socketRef.current.once('connect', () => {
              socketRef.current?.emit('join_lobby', {
                lobby_id: data.lobby_id,
                player_id: playerIdRef.current,
              });
            });
          }
        }
      } else {
        setError(data.error || 'Failed to join lobby');
      }
    } catch (err: any) {
      console.error('Error joining lobby:', err);
      if (err.name === 'AbortError') {
        setError('Request timed out. Please check if the server is running and try again.');
      } else {
        setError(err.message || 'Failed to join lobby');
      }
    } finally {
      setLoading(false);
    }
  };

  const copyLobbyId = () => {
    navigator.clipboard.writeText(lobbyId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const leaveLobby = () => {
    if (socketRef.current && lobbyId) {
      socketRef.current.emit('leave_lobby', {
        lobby_id: lobbyId,
        player_id: playerIdRef.current,
      });
    }
    setLobbyMode('create');
    setLobbyId('');
    lobbyIdRef.current = '';
    setJoinLobbyId('');
    setRestaurants([]);
    setSelectedRestaurant(null);
    setLocation('');
    setMood('');
    setIsHost(false);
    setPlayerCount(1);
    setPlayerIds([]);
    setError(null);
  };

  // Show create/join selection
  if (lobbyMode === 'create' || lobbyMode === 'join') {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="p-8 bg-[#1a1a1a] border-[#fbbf24]/20">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-[#dc2626] to-[#991b1b] rounded-full flex items-center justify-center shadow-lg shadow-[#dc2626]/20">
                <Users className="w-8 h-8 text-[#fbbf24]" />
              </div>
            </div>
            <h2 className="text-white mb-2">Multiplayer Mode</h2>
            <p className="text-[#a3a3a3]">
              {lobbyMode === 'create' 
                ? 'Create a lobby and share the ID with friends!'
                : 'Join an existing lobby with a lobby ID'}
            </p>
          </div>

          {!connected && !error && (
            <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
              <p className="text-yellow-500 text-sm">Connecting to server...</p>
              <p className="text-yellow-500/70 text-xs mt-1">Make sure Flask server is running on port 5000</p>
            </div>
          )}
          
          {connected && (
            <div className="mb-6 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
              <p className="text-green-500 text-sm">✅ Connected to server</p>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
              <p className="text-red-500 text-sm">{error}</p>
            </div>
          )}

          {lobbyMode === 'create' ? (
            <div className="space-y-6">
              <div className="text-center">
                <Button
                  onClick={createLobby}
                  disabled={loading || !connected}
                  className="bg-gradient-to-r from-[#fbbf24] to-[#f59e0b] hover:from-[#f59e0b] hover:to-[#d97706] text-black px-8 py-6 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#fbbf24]/20"
                >
                  {loading ? 'Creating...' : 'Create Lobby'}
                </Button>
              </div>
              <div className="text-center">
                <Button
                  onClick={() => setLobbyMode('join')}
                  variant="outline"
                  className="border-[#fbbf24]/30 text-[#fbbf24] hover:bg-[#fbbf24] hover:text-black"
                >
                  <LogIn className="w-4 h-4 mr-2" />
                  Join Existing Lobby
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <label className="text-white mb-2 block">Enter Lobby ID</label>
                <Input
                  placeholder="Enter 6-character lobby ID"
                  value={joinLobbyId}
                  onChange={(e) => setJoinLobbyId(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === 'Enter' && joinLobby()}
                  maxLength={6}
                  className="bg-[#0a0a0a] border-[#fbbf24]/20 text-white placeholder:text-[#a3a3a3] focus:border-[#fbbf24] text-center text-2xl tracking-wider uppercase"
                />
              </div>
              <div className="flex gap-4">
                <Button
                  onClick={joinLobby}
                  disabled={loading || !connected || !joinLobbyId.trim()}
                  className="flex-1 bg-gradient-to-r from-[#fbbf24] to-[#f59e0b] hover:from-[#f59e0b] hover:to-[#d97706] text-black px-8 py-6 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#fbbf24]/20"
                >
                  {loading ? 'Joining...' : 'Join Lobby'}
                </Button>
                <Button
                  onClick={() => {
                    setLobbyMode('create');
                    setJoinLobbyId('');
                    setError(null);
                  }}
                  variant="outline"
                  className="border-[#fbbf24]/30 text-[#fbbf24] hover:bg-[#fbbf24] hover:text-black"
                >
                  Back
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    );
  }

  // Show connected lobby view
  return (
    <div className="max-w-4xl mx-auto">
      {/* Lobby Header */}
      <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div>
              <h2 className="text-white flex items-center gap-2">
                {isHost && <Crown className="w-5 h-5 text-[#fbbf24]" />}
                Multiplayer Lobby
              </h2>
              <p className="text-[#a3a3a3] mt-1">
                {isHost ? 'You are the host' : 'Waiting for host to spin...'}
              </p>
            </div>
            <div className="flex items-center gap-2 bg-[#0a0a0a] px-4 py-2 rounded-lg border border-[#fbbf24]/20">
              <span className="text-[#a3a3a3] text-sm">Lobby:</span>
              <span className="text-[#fbbf24] tracking-wider font-mono">{lobbyId}</span>
              <Button
                onClick={copyLobbyId}
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-[#fbbf24] hover:bg-[#fbbf24] hover:text-black"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              </Button>
            </div>
            <Badge
              className={`${
                connected
                  ? 'bg-green-900/40 text-green-300 border border-green-500/30'
                  : 'bg-red-900/40 text-red-300 border border-red-500/30'
              }`}
            >
              {connected ? '🟢 Connected' : '🔴 Disconnected'}
            </Badge>
            <Badge className="bg-[#2a2a2a] text-[#a3a3a3] border border-[#fbbf24]/20">
              {playerCount} {playerCount === 1 ? 'player' : 'players'}
            </Badge>
          </div>
          <Button
            onClick={leaveLobby}
            variant="outline"
            className="border-[#dc2626] text-[#dc2626] hover:bg-[#dc2626] hover:text-white"
          >
            Leave Lobby
          </Button>
        </div>
        
        {/* Player List */}
        <div className="mt-4 pt-4 border-t border-[#fbbf24]/20">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-[#fbbf24]" />
            <h3 className="text-white text-sm font-semibold">Players in Lobby:</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {/* Always show current player first */}
            <Badge
              className={`${
                isHost
                  ? 'bg-[#fbbf24]/20 text-[#fbbf24] border border-[#fbbf24]/50'
                  : 'bg-[#2a2a2a] text-[#a3a3a3] border border-[#fbbf24]/20'
              } ring-2 ring-[#fbbf24]/50`}
            >
              {isHost && <Crown className="w-3 h-3 mr-1" />}
              You {isHost ? '(Host)' : ''}
            </Badge>
            {/* Show other players if we have them tracked */}
            {playerIds
              .filter(id => id !== playerIdRef.current)
              .map((playerId, index) => (
                <Badge
                  key={playerId}
                  className="bg-[#2a2a2a] text-[#a3a3a3] border border-[#fbbf24]/20"
                >
                  Player {index + 2}
                </Badge>
              ))}
            {/* If we don't have full player list but know there are more players */}
            {playerIds.length === 1 && playerCount > 1 && (
              <Badge className="bg-[#2a2a2a] text-[#a3a3a3] border border-[#fbbf24]/20">
                +{playerCount - 1} {playerCount - 1 === 1 ? 'other player' : 'other players'}
              </Badge>
            )}
          </div>
        </div>
      </Card>

      {/* Wheel Spinner - Only host can spin */}
      <WheelSpinner
        location={location}
        setLocation={setLocation}
        mood={mood}
        setMood={setMood}
        restaurants={restaurants}
        setRestaurants={setRestaurants}
        selectedRestaurant={selectedRestaurant}
        setSelectedRestaurant={setSelectedRestaurant}
        isSpinning={isSpinning}
        setIsSpinning={setIsSpinning}
        isHost={isHost}
        lobbyId={lobbyId}
        playerId={playerIdRef.current}
        socket={socketRef.current}
      />

      {/* Results */}
      {restaurants.length > 0 && (
        <RestaurantResults 
          restaurants={restaurants}
          selectedRestaurant={selectedRestaurant}
        />
      )}

      {!isHost && restaurants.length === 0 && (
        <Card className="p-8 bg-[#1a1a1a] border-[#fbbf24]/20 mt-8">
          <div className="text-center">
            <p className="text-[#a3a3a3]">
              Waiting for the host to spin the roulette...
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
