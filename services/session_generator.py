import random
import string

def generate_room_id(existing_rooms):
    """
    Generate a unique 6-character room ID.
    
    Args:
        existing_rooms (set): Set of existing room IDs to avoid duplicates
        
    Returns:
        str: A unique 6-character room ID
    """
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if room_id not in existing_rooms:
            return room_id
