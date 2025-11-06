import { useState } from 'react';
import { Utensils } from 'lucide-react';
import { Button } from './components/ui/button';
import { WheelSpinner } from './components/WheelSpinner';
import { RestaurantResults } from './components/RestaurantResults';
import { HomeView } from './components/HomeView';
import { MultiplayerMode } from './components/MultiplayerMode';

export default function App() {
  const [location, setLocation] = useState('');
  const [mood, setMood] = useState('');
  const [restaurants, setRestaurants] = useState<any[]>([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState<any>(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [currentView, setCurrentView] = useState<'home' | 'spin' | 'multiplayer'>('home');
  const [players, setPlayers] = useState<string[]>([]);
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(0);

  const handleNavigation = (view: 'home' | 'spin' | 'multiplayer') => {
    setCurrentView(view);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-[#fbbf24]/20 py-4 bg-[#1a1a1a] shadow-lg shadow-[#fbbf24]/5">
        <div className="container mx-auto px-4">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-[#dc2626] to-[#991b1b] rounded-full flex items-center justify-center shadow-lg shadow-[#dc2626]/20">
                <Utensils className="w-6 h-6 text-[#fbbf24]" />
              </div>
              <h1 className="text-white">Restaurant Roulette</h1>
            </div>

            {/* Navigation Bar */}
            <nav className="flex items-center gap-2">
              <Button
                variant="ghost"
                className={`${
                  currentView === 'home'
                    ? 'bg-[#dc2626] text-white hover:bg-[#b91c1c]'
                    : 'text-[#a3a3a3] hover:text-white hover:bg-[#1a1a1a]'
                }`}
                onClick={() => handleNavigation('home')}
              >
                Home
              </Button>
              <Button
                variant="ghost"
                className={`${
                  currentView === 'spin'
                    ? 'bg-[#dc2626] text-white hover:bg-[#b91c1c]'
                    : 'text-[#a3a3a3] hover:text-white hover:bg-[#1a1a1a]'
                }`}
                onClick={() => handleNavigation('spin')}
              >
                Spin the Wheel
              </Button>
              <Button
                variant="ghost"
                className={`${
                  currentView === 'multiplayer'
                    ? 'bg-[#dc2626] text-white hover:bg-[#b91c1c]'
                    : 'text-[#a3a3a3] hover:text-white hover:bg-[#1a1a1a]'
                }`}
                onClick={() => handleNavigation('multiplayer')}
              >
                Multiplayer
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {currentView === 'home' && <HomeView onGetStarted={() => setCurrentView('spin')} />}
        
        {currentView === 'spin' && (
          <>
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
            />
            {restaurants.length > 0 && (
              <RestaurantResults 
                restaurants={restaurants}
                selectedRestaurant={selectedRestaurant}
              />
            )}
          </>
        )}
        
        {currentView === 'multiplayer' && (
          <MultiplayerMode
            players={players}
            setPlayers={setPlayers}
            currentPlayerIndex={currentPlayerIndex}
            setCurrentPlayerIndex={setCurrentPlayerIndex}
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
          />
        )}
      </main>
    </div>
  );
}
