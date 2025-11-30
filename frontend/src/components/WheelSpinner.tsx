import React, { useState, useRef, useEffect } from 'react';
import { MapPin, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { Socket } from 'socket.io-client';

interface WheelSpinnerProps {
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
  playerName?: string;
  isHost?: boolean;
  lobbyId?: string;
  playerId?: string;
  socket?: Socket | null;
}

export function WheelSpinner({
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
  playerName,
  isHost = false,
  lobbyId,
  playerId,
  socket,
}: WheelSpinnerProps) {
  const [rotation, setRotation] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleSpin = async () => {
    if (!location.trim() || !mood.trim()) {
      setError('Please enter both location and mood');
      return;
    }

    setError(null);
    setIsLoading(true);
    setIsSpinning(true);

    try {
      // Call Flask API
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: location.trim(),
          mood: mood.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to fetch restaurants');
      }

      const fetchedRestaurants = data.restaurants || [];
      setRestaurants(fetchedRestaurants);

      // Start spin animation
      const spins = 5 + Math.random() * 3;
      const finalRotation = rotation + spins * 360 + Math.random() * 360;
      setRotation(finalRotation);

      // Select restaurant after spin animation
      setTimeout(() => {
        if (fetchedRestaurants.length > 0) {
          const index = Math.floor(Math.random() * fetchedRestaurants.length);
          const selected = fetchedRestaurants[index];
          setSelectedRestaurant(selected);
          
          // If in multiplayer mode and host, emit the result to all players
          if (isHost && lobbyId && playerId && socket) {
            socket.emit('host_spin', {
              lobby_id: lobbyId,
              host_id: playerId,
              restaurants: fetchedRestaurants,
              selected_restaurant: selected,
              location: location.trim(),
              mood: mood.trim(),
            });
          }
        }
        setIsSpinning(false);
        setIsLoading(false);
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch restaurants');
      setIsSpinning(false);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 140;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const segments = restaurants.length > 0 ? restaurants.length : 8;
    const anglePerSegment = (2 * Math.PI) / segments;

    // Draw segments
    for (let i = 0; i < segments; i++) {
      const startAngle = i * anglePerSegment + (rotation * Math.PI) / 180;
      const endAngle = (i + 1) * anglePerSegment + (rotation * Math.PI) / 180;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();

      // Alternate colors - red and black
      ctx.fillStyle = i % 2 === 0 ? '#dc2626' : '#1a1a1a';
      ctx.fill();
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw text
      if (restaurants.length > 0) {
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(startAngle + anglePerSegment / 2);
        ctx.textAlign = 'center';
        ctx.fillStyle = i % 2 === 0 ? '#ffffff' : '#fbbf24';
        ctx.font = '12px Arial';
        const name = restaurants[i]?.name.substring(0, 10) || '';
        ctx.fillText(name, radius * 0.65, 5);
        ctx.restore();
      }
    }

    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, 40, 0, 2 * Math.PI);
    ctx.fillStyle = '#000000';
    ctx.fill();
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw border
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 8;
    ctx.stroke();

    // Draw pointer at top (fixed arrow)
    ctx.beginPath();
    ctx.moveTo(centerX, 20);
    ctx.lineTo(centerX - 10, 0);
    ctx.lineTo(centerX + 10, 0);
    ctx.closePath();
    ctx.fillStyle = '#fbbf24';
    ctx.fill();
  }, [rotation, restaurants]);

  const canSpin = location.trim() !== '' && mood.trim() !== '';

  return (
    <div className="max-w-4xl mx-auto">
      {playerName && (
        <div className="text-center mb-6">
          <h2 className="text-white">
            <span className="text-[#fbbf24]">{playerName}</span>'s Turn
          </h2>
        </div>
      )}

      {/* Input Fields - Both Required */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Card className="p-6 bg-[#1a1a1a] border-2 border-[#fbbf24]/20 hover:border-[#fbbf24]/50 transition-all">
          <div className="flex flex-col items-center text-center gap-3">
            <MapPin className="w-12 h-12 text-[#dc2626]" />
            <h3 className="text-white">Location</h3>
            <p className="text-[#a3a3a3]">Where do you want to eat?</p>
            <Input
              placeholder="Enter location (e.g., New York, NY)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="mt-2 bg-[#0a0a0a] border-[#fbbf24]/20 text-white placeholder:text-[#a3a3a3] focus:border-[#fbbf24]"
            />
          </div>
        </Card>

        <Card className="p-6 bg-[#1a1a1a] border-2 border-[#fbbf24]/20 hover:border-[#fbbf24]/50 transition-all">
          <div className="flex flex-col items-center text-center gap-3">
            <Sparkles className="w-12 h-12 text-[#dc2626]" />
            <h3 className="text-white">Mood</h3>
            <p className="text-[#a3a3a3]">What's your vibe?</p>
            <Input
              placeholder="Enter mood (e.g., Spicy, Cozy, Upscale)"
              value={mood}
              onChange={(e) => setMood(e.target.value)}
              className="mt-2 bg-[#0a0a0a] border-[#fbbf24]/20 text-white placeholder:text-[#a3a3a3] focus:border-[#fbbf24]"
            />
          </div>
        </Card>
      </div>

      {/* Roulette Section */}
      <Card className="p-8 bg-[#1a1a1a] border-[#fbbf24]/20">
        <div className="text-center mb-6">
          <h2 className="text-white">Roulette Ready!</h2>
          <p className="text-[#a3a3a3] mt-2">
            {!canSpin 
              ? 'Please enter both location and mood to spin!'
              : restaurants.length > 0
              ? `Found ${restaurants.length} restaurants in ${location} matching "${mood}" mood`
              : 'Tap the wheel to spin!'}
          </p>
          {error && (
            <p className="text-[#dc2626] mt-2">
              ⚠️ {error}
            </p>
          )}
          {selectedRestaurant && !isSpinning && !isLoading && (
            <p className="text-[#fbbf24] mt-2">
              🎉 Selected: {selectedRestaurant.name}!
            </p>
          )}
        </div>

        <div className="flex justify-center mb-6">
          <canvas
            ref={canvasRef}
            width={400}
            height={400}
          />
        </div>

        <div className="text-center">
          {isHost === false && lobbyId && (
            <div className="mb-4 p-4 bg-[#0a0a0a] border border-[#fbbf24]/20 rounded-lg">
              <p className="text-[#a3a3a3] text-sm">
                Only the host can spin the roulette. Waiting for host...
              </p>
            </div>
          )}
          <Button
            onClick={handleSpin}
            disabled={isSpinning || isLoading || !canSpin || (lobbyId && !isHost)}
            className="bg-gradient-to-r from-[#dc2626] to-[#991b1b] hover:from-[#b91c1c] hover:to-[#7f1d1d] text-white px-8 py-6 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#dc2626]/20"
          >
            {isLoading ? '⏳ Loading restaurants...' : isSpinning ? '🎡 Spinning...' : '▶ Spin the Wheel!'}
          </Button>
          <p className="text-[#a3a3a3] text-sm mt-3">
            {lobbyId && !isHost 
              ? 'Only the host can spin the roulette'
              : 'Click to spin and discover a random restaurant!'}
          </p>
        </div>
      </Card>
    </div>
  );
}
