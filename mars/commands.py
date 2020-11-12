"""
commands.py
module containing all the commands to send to the robots.

Mechatronics 2
~ Alberto Guerra Martinuzzi, 2020
"""
import threading
from mars import settings
from mars import comms

# list containing all the commands that will be sent
callstack = []

# 3 main topics: alien, engineer, compound, they each have 8 cahnnels available
# list of channel names in the form - TEAM_NAME + topic + channel_number (1-8)
alien_channels = [settings.TEAM_NAME + "-alien/" + str(n) for n in range(1, 9)]
enginner_channels = [settings.TEAM_NAME +
                     "-engineer/" + str(n) for n in range(1, 9)]
compound_channels = [settings.TEAM_NAME +
                     "-compound/" + str(n) for n in range(1, 9)]

# This dictionary contains the names for each topic and channel.
# Channels are accessed by using the topic name and the channel number in the form 0-7 (because of python lists)
# For example, access topic:alien and channel:1 <topics["aliens"][0]> returns the string "Team-B-alien/1"
topics = {
    "alien": alien_channels,
    "engineer": enginner_channels,
    "compound": compound_channels
}

command_channels = {
    "MV": 1,
    "STP": 3,
    "FNC": 4

}

data_avaliable = threading.Event()


def merge_data(high_word, low_word):
    # mask for signed 32bit integers to get a signed 16bit integer
    bitmask = 0x0000FFFF
    # shifts the high_word 16 bits and takes only the lower 16bits from the low_word
    msg = str((high_word << 16) + (low_word & bitmask))
    return msg


def move(device, distance, angle):
    global callstack, data_avaliable
    payload = merge_data(distance, angle)
    callstack.append(
        {
            "dest": device,
            "command": "MV",
            "payload": payload
        }
    )
    data_avaliable.set()


def stop(device):
    global callstack, data_avaliable
    payload = "1"
    callstack.append(
        {
            "dest": device,
            "command": "STP",
            "payload": payload
        }
    )
    data_avaliable.set()


def function(device):
    global callstack, data_avaliable
    payload = "1"
    callstack.append(
        {
            "dest": device,
            "command": "FNC",
            "payload": payload
        }
    )
    data_avaliable.set()