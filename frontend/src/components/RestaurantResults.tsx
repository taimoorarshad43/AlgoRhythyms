import React from 'react';
import { MapPin, DollarSign, Star } from 'lucide-react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';

interface RestaurantResultsProps {
  restaurants: any[];
  selectedRestaurant: any;
}

export function RestaurantResults({ restaurants, selectedRestaurant }: RestaurantResultsProps) {
  return (
    <div className="mt-8 max-w-4xl mx-auto">
      <Card className="p-6 bg-[#1a1a1a] border-[#fbbf24]/20">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-[#fbbf24] rounded-full animate-pulse" />
          <h3 className="text-white">Roulette Table: {restaurants.length} Options</h3>
        </div>

        <div className="space-y-3">
          {restaurants.map((restaurant, index) => (
            <Card
              key={index}
              className={`p-4 transition-all ${
                selectedRestaurant?.name === restaurant.name
                  ? 'bg-gradient-to-r from-[#dc2626] to-[#991b1b] border-[#fbbf24] shadow-lg shadow-[#dc2626]/20'
                  : 'bg-[#0a0a0a] border-[#fbbf24]/20 hover:border-[#fbbf24]/50'
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`w-10 h-10 rounded flex items-center justify-center flex-shrink-0 ${
                    selectedRestaurant?.name === restaurant.name
                      ? 'bg-[#fbbf24] text-black'
                      : 'bg-gradient-to-br from-[#dc2626] to-[#991b1b] text-white shadow-lg shadow-[#dc2626]/20'
                  }`}
                >
                  {index + 1}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-white">
                    {restaurant.name}
                  </h4>

                  <div className="flex flex-wrap items-center gap-3 mt-2 text-sm">
                    <div
                      className={`flex items-center gap-1 ${
                        selectedRestaurant?.name === restaurant.name
                          ? 'text-white'
                          : 'text-[#a3a3a3]'
                      }`}
                    >
                      <MapPin className="w-4 h-4" />
                      <span>{restaurant.cuisine || 'Various'}</span>
                    </div>

                    <div
                      className={`flex items-center gap-1 ${
                        selectedRestaurant?.name === restaurant.name
                          ? 'text-white'
                          : 'text-[#a3a3a3]'
                      }`}
                    >
                      <Star className="w-4 h-4 fill-current" />
                      <span>
                        {restaurant.rating} ({restaurant.review_count || 0} reviews)
                      </span>
                    </div>
                  </div>

                  {/* Reviews - Integrated into card flow */}
                  {restaurant.reviews && restaurant.reviews.length > 0 && (
                    <div className="mt-4 space-y-3">
                      {restaurant.reviews.map((review: any, reviewIndex: number) => (
                        <div key={reviewIndex} className="flex items-start gap-3 pb-3 border-b border-[#fbbf24]/10 last:border-0 last:pb-0">
                          <Avatar className="w-8 h-8 flex-shrink-0">
                            <AvatarFallback
                              className={`text-xs ${
                                selectedRestaurant?.name === restaurant.name
                                  ? 'bg-[#fbbf24] text-black'
                                  : 'bg-gradient-to-br from-[#dc2626] to-[#991b1b] text-[#fbbf24]'
                              }`}
                            >
                              {review.user_name ? review.user_name.charAt(0) : '?'}
                            </AvatarFallback>
                          </Avatar>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <span
                                className={`text-sm ${
                                  selectedRestaurant?.name === restaurant.name
                                    ? 'text-white'
                                    : 'text-white'
                                }`}
                              >
                                {review.user_name || 'Anonymous'}
                              </span>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`w-3 h-3 ${
                                      i < (review.rating || 0)
                                        ? 'text-[#fbbf24] fill-[#fbbf24]'
                                        : 'text-[#2a2a2a]'
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                            <p
                              className={`text-sm mb-1 ${
                                selectedRestaurant?.name === restaurant.name
                                  ? 'text-white/90'
                                  : 'text-[#a3a3a3]'
                              }`}
                            >
                              {review.text || 'No review text available'}
                            </p>
                            <span
                              className={`text-xs ${
                                selectedRestaurant?.name === restaurant.name
                                  ? 'text-white/60'
                                  : 'text-[#a3a3a3]/70'
                              }`}
                            >
                              {review.time_created || ''}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <p
                    className={`mt-4 text-sm ${
                      selectedRestaurant?.name === restaurant.name
                        ? 'text-white'
                        : 'text-[#a3a3a3]'
                    }`}
                  >
                    {restaurant.address}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}
