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
COMMSRATE = 5

# Radius within which the Engineer can hear / see the Alien
DETECTION_RADIUS = 30

# Radius within which the Engineer has reached a marker
MARKER_RADIUS = 5

# How much aruco positions can change with each update; 1 is 100% the new value
MARKER_SMOOTHING = 0.3

# General variables for communications
TEAM_NAME = "ALIEN_SELF_ISOLATION"
TOPICS = ["alien", "engineer", "compound"]
CONNECTION_ATTEMPTS_LIMIT = 5

# MQTT Server information
SERVER_IP = "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com"
PORT = 31415
USERNAME = "student"
PASSWORD = "smartPass"

# Map of channels and functions
DATA_CHANNELS = {
    "settings": 0,
    "move":     1,
    "adjust":   2,
    "stop":     3,
    "function": 4,
    "recieve":  5,
    "none1":    6,
    "connected": 7
}

# Messages from the alien/engineer
DEVICE_MESSAGES = {
    "connected": 0b000000100,   # status of device
    "stopped": 0b000000001,   # Device is not moving
    "moving":  0b000000010,   # Device is moving
    "action":  0b000000011    # Customizable action

}

# messages recieved from the compound
COMPOUND_MESSAGES = {
    "A": 0b00000001,   # Door A is closed/open
    "B": 0b00000010,   # Door B is closed/open
    "C": 0b00000011,   # Door C is closed/open
    "D": 0b00000100   # Door D is closed/open
}

# Unit conversion for Engineer
DIST_MULTIPLIER = 1
