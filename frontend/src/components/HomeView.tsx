import { Sparkles, MapPin, Star } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface HomeViewProps {
  onGetStarted: () => void;
}

export function HomeView({ onGetStarted }: HomeViewProps) {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h2 className="text-white mb-4">Can't Decide Where to Eat?</h2>
        <p className="text-[#a3a3a3] text-lg mb-8">
          Let the wheel decide! Discover amazing restaurants based on your location and mood.
        </p>
        <Button
          onClick={onGetStarted}
          className="bg-gradient-to-r from-[#dc2626] to-[#991b1b] hover:from-[#b91c1c] hover:to-[#7f1d1d] text-white px-8 py-6 shadow-lg shadow-[#dc2626]/20"
        >
          Get Started
        </Button>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20 text-center hover:border-[#fbbf24]/50 transition-all">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-[#0a0a0a] rounded-full flex items-center justify-center border-2 border-[#fbbf24]/30">
              <MapPin className="w-8 h-8 text-[#dc2626]" />
            </div>
          </div>
          <h3 className="text-white mb-2">Location-Based</h3>
          <p className="text-[#a3a3a3]">
            Find restaurants near you or anywhere you want to explore.
          </p>
        </Card>

        <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20 text-center hover:border-[#fbbf24]/50 transition-all">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-[#0a0a0a] rounded-full flex items-center justify-center border-2 border-[#fbbf24]/30">
              <Sparkles className="w-8 h-8 text-[#dc2626]" />
            </div>
          </div>
          <h3 className="text-white mb-2">Mood-Based</h3>
          <p className="text-[#a3a3a3]">
            Match restaurants to your vibe - spicy, cozy, upscale, and more.
          </p>
        </Card>

        <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20 text-center hover:border-[#fbbf24]/50 transition-all">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-[#0a0a0a] rounded-full flex items-center justify-center border-2 border-[#fbbf24]/30">
              <Star className="w-8 h-8 text-[#dc2626]" />
            </div>
          </div>
          <h3 className="text-white mb-2">Real Reviews</h3>
          <p className="text-[#a3a3a3]">
            Read authentic reviews from real diners for each restaurant.
          </p>
        </Card>
      </div>

      {/* How it Works */}
      <Card className="p-8 bg-[#1a1a1a] border-[#fbbf24]/20">
        <h3 className="text-white text-center mb-6">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-br from-[#dc2626] to-[#991b1b] text-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg shadow-[#dc2626]/20">
              1
            </div>
            <p className="text-white">Enter location and mood</p>
            <p className="text-[#a3a3a3] text-sm mt-1">Both are required</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-br from-[#dc2626] to-[#991b1b] text-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg shadow-[#dc2626]/20">
              2
            </div>
            <p className="text-white">Spin the wheel</p>
            <p className="text-[#a3a3a3] text-sm mt-1">Watch the magic happen</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-br from-[#dc2626] to-[#991b1b] text-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg shadow-[#dc2626]/20">
              3
            </div>
            <p className="text-white">Discover your restaurant</p>
            <p className="text-[#a3a3a3] text-sm mt-1">Get ready for a great meal!</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
