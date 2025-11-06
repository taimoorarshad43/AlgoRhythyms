import { useState, useEffect } from 'react';
import { Users, Plus, Trash2, Play, Copy, Check } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { WheelSpinner } from './WheelSpinner';
import { RestaurantResults } from './RestaurantResults';

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

// Generate a random lobby ID
const generateLobbyId = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let id = '';
  for (let i = 0; i < 6; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return id;
};

export function MultiplayerMode({
  players,
  setPlayers,
  currentPlayerIndex,
  setCurrentPlayerIndex,
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
  const [newPlayerName, setNewPlayerName] = useState('');
  const [gameStarted, setGameStarted] = useState(false);
  const [lobbyId, setLobbyId] = useState('');
  const [copied, setCopied] = useState(false);

  // Generate lobby ID on mount
  useEffect(() => {
    setLobbyId(generateLobbyId());
  }, []);

  const copyLobbyId = () => {
    navigator.clipboard.writeText(lobbyId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const addPlayer = () => {
    if (newPlayerName.trim() && !players.includes(newPlayerName.trim())) {
      setPlayers([...players, newPlayerName.trim()]);
      setNewPlayerName('');
    }
  };

  const removePlayer = (index: number) => {
    const newPlayers = players.filter((_, i) => i !== index);
    setPlayers(newPlayers);
    if (currentPlayerIndex >= newPlayers.length) {
      setCurrentPlayerIndex(0);
    }
  };

  const startGame = () => {
    if (players.length >= 2) {
      setGameStarted(true);
      setCurrentPlayerIndex(0);
    }
  };

  const nextPlayer = () => {
    setCurrentPlayerIndex((currentPlayerIndex + 1) % players.length);
    setSelectedRestaurant(null);
  };

  const endGame = () => {
    setGameStarted(false);
    setCurrentPlayerIndex(0);
    setSelectedRestaurant(null);
    setRestaurants([]);
  };

  if (!gameStarted) {
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
              Add players to your group and take turns spinning the wheel!
            </p>
          </div>

          {/* Lobby ID */}
          <div className="mb-8">
            <Card className="p-6 bg-[#0a0a0a] border-2 border-[#fbbf24]/30">
              <div className="text-center">
                <p className="text-[#a3a3a3] mb-2">Lobby ID</p>
                <div className="flex items-center justify-center gap-3">
                  <div className="flex items-center gap-2 bg-[#1a1a1a] px-6 py-3 rounded-lg border border-[#fbbf24]/20">
                    <span className="text-[#fbbf24] tracking-wider">{lobbyId}</span>
                  </div>
                  <Button
                    onClick={copyLobbyId}
                    variant="outline"
                    size="icon"
                    className="border-[#fbbf24]/30 text-[#fbbf24] hover:bg-[#fbbf24] hover:text-black"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <p className="text-[#a3a3a3] text-sm mt-2">Share this ID with your friends to join!</p>
              </div>
            </Card>
          </div>

          {/* Add Player */}
          <div className="mb-8">
            <h3 className="text-white mb-4">Add Players (Minimum 2)</h3>
            <div className="flex gap-2">
              <Input
                placeholder="Enter player name"
                value={newPlayerName}
                onChange={(e) => setNewPlayerName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addPlayer()}
                className="bg-[#0a0a0a] border-[#fbbf24]/20 text-white placeholder:text-[#a3a3a3] focus:border-[#fbbf24]"
              />
              <Button
                onClick={addPlayer}
                className="bg-gradient-to-r from-[#dc2626] to-[#991b1b] hover:from-[#b91c1c] hover:to-[#7f1d1d] text-white shadow-lg shadow-[#dc2626]/20"
              >
                <Plus className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Players List */}
          {players.length > 0 && (
            <div className="mb-8">
              <h3 className="text-white mb-4">Players ({players.length})</h3>
              <div className="space-y-2">
                {players.map((player, index) => (
                  <Card
                    key={index}
                    className="p-4 bg-[#0a0a0a] border-[#fbbf24]/20 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-[#dc2626] to-[#991b1b] rounded-full flex items-center justify-center shadow-lg shadow-[#dc2626]/20">
                        <span className="text-white">{index + 1}</span>
                      </div>
                      <span className="text-white">{player}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removePlayer(index)}
                      className="text-[#dc2626] hover:text-white hover:bg-[#dc2626]/20"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Start Game */}
          <div className="text-center">
            <Button
              onClick={startGame}
              disabled={players.length < 2}
              className="bg-gradient-to-r from-[#fbbf24] to-[#f59e0b] hover:from-[#f59e0b] hover:to-[#d97706] text-black px-8 py-6 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#fbbf24]/20"
            >
              <Play className="w-5 h-5 mr-2" />
              Start Game
            </Button>
            {players.length < 2 && (
              <p className="text-[#dc2626] text-sm mt-3">
                Add at least 2 players to start
              </p>
            )}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Game Header with Lobby ID */}
      <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-white">Multiplayer Game</h2>
              <p className="text-[#a3a3a3] mt-1">
                Current Player: <span className="text-[#fbbf24]">{players[currentPlayerIndex]}</span>
              </p>
            </div>
            <div className="flex items-center gap-2 bg-[#0a0a0a] px-4 py-2 rounded-lg border border-[#fbbf24]/20">
              <span className="text-[#a3a3a3] text-sm">Lobby:</span>
              <span className="text-[#fbbf24] tracking-wider">{lobbyId}</span>
              <Button
                onClick={copyLobbyId}
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-[#fbbf24] hover:bg-[#fbbf24] hover:text-black"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              </Button>
            </div>
          </div>
          <Button
            onClick={endGame}
            variant="outline"
            className="border-[#dc2626] text-[#dc2626] hover:bg-[#dc2626] hover:text-white"
          >
            End Game
          </Button>
        </div>

        {/* Players Progress */}
        <div className="flex flex-wrap gap-2">
          {players.map((player, index) => (
            <Badge
              key={index}
              className={`px-3 py-2 ${
                index === currentPlayerIndex
                  ? 'bg-gradient-to-r from-[#fbbf24] to-[#f59e0b] text-black'
                  : 'bg-[#2a2a2a] text-[#a3a3a3] border border-[#fbbf24]/20'
              }`}
            >
              {player}
            </Badge>
          ))}
        </div>
      </Card>

      {/* Wheel Spinner */}
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
        playerName={players[currentPlayerIndex]}
      />

      {/* Results and Next Player */}
      {restaurants.length > 0 && (
        <>
          <RestaurantResults 
            restaurants={restaurants}
            selectedRestaurant={selectedRestaurant}
          />
          
          {selectedRestaurant && !isSpinning && (
            <div className="text-center mt-8">
              <Button
                onClick={nextPlayer}
                className="bg-gradient-to-r from-[#fbbf24] to-[#f59e0b] hover:from-[#f59e0b] hover:to-[#d97706] text-black px-8 py-6 shadow-lg shadow-[#fbbf24]/20"
              >
                Next Player's Turn
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
