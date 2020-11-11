#!/usr/bin/env python3
"""
The communications file to send and recieve data from embedded robots
Mechatronics 2

Alberto Guerra Martinuzzi, 2020
"""
from mars import logs  # better logging methods
from mars import settings
import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import time  # This is the library that will allow us to use the sleep function

log = logs.create_log(__name__)


class comm:
    # Constructor to start the communication path
    def __init__(self):
        # Here is the list of properties of the class
        self.variable = 0
        self.client = mqtt.Client()
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        self.client.username_pw_set("student", password="smartPass")
        self.client.connect(
            "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com", 31415, 60)
        log.info("Comms object created")

    # Class destructor when deleting communication object
    def release(self):
        log.warning("Class object deleted")
        self.client.loop_stop()
        self.client.disconnect()

    # Callback function for client class
    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Connection succesful")
            self.client.subscribe("Team-B-alien/1")
        else:
            log.error("Something went wrong - exit code: " + str(rc))

    # callback function for client class
    def __on_message(self, client, userdata, msg):
        log.info(msg.topic + " Updated to " +
                 str(int(msg.payload.rstrip(b'\x00'))))

    # Function to enable listening and publishing data from the server
    def start_listening(self):
        self.client.loop_start()
        log.info("Starting listening function")

    # Function to disable listening and publishing data from the server
    def stop_listening(self):
        self.client.loop_stop()

    # Function to publish data to the desired channel
    def publish_data(self, channel, data):
        self.client.publish(channel, data)
        log.info("Data_published = " + data + " On channel: " + channel)


""" # Defining the client class callback functions

# The callback for when we connect to the server. The meaning of the return code (rc) can be found here:
# https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901079
# A zero is good.
# After we connect we subsribe to one (or more) topics in this case the topic number 1


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Here we subscribe to the list of topics and channels that we want to subscribe to
    for channel in subscribe_channels:
        client.subscribe(topics["alien"][channel])


# The callback for when a PUBLISH message is received from the server. I.e. when a new value for the topic we subscribed to above updates
# the expression str(int(msg.payload.rstrip(b'\x00'))) converts the message from the server to an integer and then a string for printing.
# Specifically:
#   msg.payload.rstrip(b'\x00') This is getting all the bytes from the server (should be 11 in our case) and removes bytes with the value \x00 from the right
#   int() converts the remaining bytes into an integer, it treats them as a string
#   str() converts the integer into a string for the purpose of printing it. See below (l.56) for an alternative way to do this
def on_message(client, userdata, msg):
    #    recieve_time = time.strftime("%Y/%m/%d, %H:%M:%S |", time.localtime())
    #   print(recieve_time + " In topic: " + msg.topic +
    #          " | Value: " + str(int(msg.payload.rstrip(b'\x00'))))
    log.info(msg.topic + " Updated to " +
             str(int(msg.payload.rstrip(b'\x00'))))

# Function to merge 2 integer values in one combined message string
# This lowers the resolution of the values to 16bit resolution but packs 2 values in one message


def merge_integers(high_word, low_word):
    # mask for signed 32bit integers to get a signed 16bit integer
    bitmask = 0x0000FFFF
    # shifts the high_word 16 bits and takes only the lower 16bits from the low_word
    msg = str((high_word << 16) + (low_word & bitmask))
    return msg


# Create the mqtt client object
client = mqtt.Client()
# Assign the function for the connection event
client.on_connect = on_connect
# Assign the function for the new message event
client.on_message = on_message

# Set the username and password
client.username_pw_set("student", password="smartPass")

# Connect to the server using a specific port with a timeout delay (in seconds)
client.connect("ec2-3-10-235-26.eu-west-2.compute.amazonaws.com", 31415, 60)

# Define the names of the topics created with team_name prefix
# 3 main topics: alien, engineer, compound, they each have 8 cahnnels available
team_name = "Team-B"
# list of channel names in the form - team_name + topic + channel_number (1-8)
alien_channels = [team_name + "-alien/" + str(n) for n in range(1, 9)]
enginner_channels = [team_name + "-engineer/" + str(n) for n in range(1, 9)]
compound_channels = [team_name + "-compound/" + str(n) for n in range(1, 9)]

# Subscribe here to
subscribe_channels = [0, 1, 3]

# This dictionary contains the names for each topic and channel.
# Channels are accessed by using the topic name and the channel number in the form 0-7 (because of python lists)
# For example, access topic:alien and channel:1 <topics["aliens"][0]> returns the string "Team-B-alien/1"
topics = {
    "alien": alien_channels,
    "engineer": enginner_channels,
    "compound": compound_channels
}

# Start the client to enable the above events to happen
client.loop_start()

value1 = 234
value2 = -578
message = merge_integers(value1, value2)
# Send (Publish) the value continuously
while(1):

    # Start a try in case we have an error
    try:
        # Every one second
        time.sleep(1)

        # Publish the value (integer) as a string. All messages are strings
        client.publish(topics["alien"][3], message)

        # Plot in the terminal what we just did
        # print("%s %d" % (topics["alien"][3], val))

    # Capture a KeyboardInterrupt, i.e. Ctrl-C in the terminal window
    except (KeyboardInterrupt):
        # Stop the Client
        client.loop_stop()
        # Disconnect
        client.disconnect()
        # Leave the while which will stop the code
        break

    # Capture any other error from the three lines (most likely will be a publish error)
    except:
        log.error("There was an error while publishing the data.") """
