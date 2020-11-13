"""
settings.py
Storage of common settings.

Mechatronics 2
~ Callum Morrison, 2020
"""

# Camera framerate in FPS
FRAMERATE = 30

# General data transmission rate for UI
DATARATE = 1

# Rate to send updated communications
COMMSRATE = 1

# Radius within which the Engineer can hear / see the Alien
DETECTION_RADIUS = 20

# Radius within which the Engineer has reached a marker
MARKER_RADIUS = 5

# General variables for communications
TEAM_NAME = "ALIEN_SELF_ISOLATION"

# Map of channels and functions
DATA_CHANNELS = {
    0: "settings",
    1: "move",
    2: "adjust",
    3: "stop",
    4: "function",
    5: "recieve",
    6: "none",
    7: "none",
}
