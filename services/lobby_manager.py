"""
Lobby management system for multiplayer mode.
Handles lobby creation, joining, state management, and expiration.
"""

import time
import threading
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class Lobby:
    """Represents a multiplayer lobby."""
    lobby_id: str
    host_id: str  # Session ID of the host
    created_at: datetime
    last_activity: datetime
    players: Set[str] = field(default_factory=set)  # Set of player session IDs
    restaurants: list = field(default_factory=list)
    selected_restaurant: Optional[dict] = None
    location: str = ""
    mood: str = ""
    
    def is_expired(self, expiration_minutes: int = 30) -> bool:
        """Check if lobby has expired due to inactivity."""
        return datetime.now() - self.last_activity > timedelta(minutes=expiration_minutes)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

class LobbyManager:
    """Manages all multiplayer lobbies."""
    
    def __init__(self, expiration_minutes: int = 30):
        self.lobbies: Dict[str, Lobby] = {}
        self.expiration_minutes = expiration_minutes
        self.lock = threading.Lock()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up expired lobbies."""
        def cleanup_expired():
            while True:
                time.sleep(60)  # Check every minute
                self.cleanup_expired_lobbies()
        
        thread = threading.Thread(target=cleanup_expired, daemon=True)
        thread.start()
    
    def create_lobby(self, lobby_id: str, host_id: str) -> Lobby:
        """Create a new lobby."""
        with self.lock:
            lobby = Lobby(
                lobby_id=lobby_id,
                host_id=host_id,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            lobby.players.add(host_id)
            self.lobbies[lobby_id] = lobby
            return lobby
    
    def _get_lobby_unlocked(self, lobby_id: str) -> Optional[Lobby]:
        """Get a lobby by ID (assumes lock is already held)."""
        lobby = self.lobbies.get(lobby_id)
        if lobby and not lobby.is_expired(self.expiration_minutes):
            return lobby
        elif lobby:
            # Lobby expired, remove it
            del self.lobbies[lobby_id]
        return None
    
    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        """Get a lobby by ID."""
        with self.lock:
            return self._get_lobby_unlocked(lobby_id)
    
    def join_lobby(self, lobby_id: str, player_id: str) -> tuple[bool, Optional[Lobby], Optional[str]]:
        """
        Join a lobby.
        Returns: (success, lobby, error_message)
        """
        with self.lock:
            lobby = self._get_lobby_unlocked(lobby_id)
            if not lobby:
                return False, None, "Lobby not found or expired"
            
            if player_id in lobby.players:
                return False, None, "Already in this lobby"
            
            lobby.players.add(player_id)
            lobby.update_activity()
            return True, lobby, None
    
    def leave_lobby(self, lobby_id: str, player_id: str):
        """Remove a player from a lobby."""
        with self.lock:
            lobby = self.lobbies.get(lobby_id)
            if lobby:
                lobby.players.discard(player_id)
                lobby.update_activity()
                
                # If host leaves, lobby is effectively dead (but keep it for now)
                # If no players left, remove lobby
                if len(lobby.players) == 0:
                    del self.lobbies[lobby_id]
    
    def update_lobby_state(self, lobby_id: str, host_id: str, restaurants: list = None, 
                          selected_restaurant: dict = None, location: str = None, mood: str = None):
        """Update lobby state (only host can do this)."""
        with self.lock:
            lobby = self._get_lobby_unlocked(lobby_id)
            if not lobby:
                return False, "Lobby not found"
            
            if lobby.host_id != host_id:
                return False, "Only the host can update lobby state"
            
            if restaurants is not None:
                lobby.restaurants = restaurants
            if selected_restaurant is not None:
                lobby.selected_restaurant = selected_restaurant
            if location is not None:
                lobby.location = location
            if mood is not None:
                lobby.mood = mood
            
            lobby.update_activity()
            return True, None
    
    def cleanup_expired_lobbies(self):
        """Remove expired lobbies."""
        with self.lock:
            expired_ids = [
                lobby_id for lobby_id, lobby in self.lobbies.items()
                if lobby.is_expired(self.expiration_minutes)
            ]
            for lobby_id in expired_ids:
                if lobby_id in self.lobbies:
                    del self.lobbies[lobby_id]
    
    def get_lobby_info(self, lobby_id: str) -> Optional[dict]:
        """Get lobby information for clients."""
        lobby = self.get_lobby(lobby_id)
        if not lobby:
            return None
        
        return {
            "lobby_id": lobby.lobby_id,
            "host_id": lobby.host_id,
            "player_count": len(lobby.players),
            "has_restaurants": len(lobby.restaurants) > 0,
            "has_selection": lobby.selected_restaurant is not None,
            "location": lobby.location,
            "mood": lobby.mood
        }

# Global lobby manager instance
lobby_manager = LobbyManager(expiration_minutes=30)

