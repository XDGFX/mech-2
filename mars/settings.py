"""
settings.py
Storage of common settings.

Mechatronics 2
~ Callum Morrison, 2020
"""

# Camera framerate in FPS
FRAMERATE = 10

# General data transmission rate for UI
DATARATE = 1

# Rate to send updated communications
COMMSRATE = 1

# Radius within which the Engineer can hear / see the Alien
DETECTION_RADIUS = 0

# Radius within which the Engineer has reached a marker
MARKER_RADIUS = 5

# How much aruco positions can change with each update; 1 is 100% the new value
MARKER_SMOOTHING = 0.3

# General variables for communications
TEAM_NAME = "ALIEN_SELF_ISOLATION"
