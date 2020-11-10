import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import time  # This is the library that will allow us to use the sleep function


# Defining the client class callback functions

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
    recieve_time = time.strftime("%Y/%m/%d, %H:%M:%S |", time.localtime())
    print(recieve_time + " In topic: " + msg.topic +
          " | Value: " + str(int(msg.payload.rstrip(b'\x00'))))


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

# Values to send
# The commands will be translated into a 32 bit integer
# since 32 bit is more resolution that the robot will ever use, changing the information to x2 16 bit integers
# then combining both to generate a 32 bit integer
top_value = 345
bot_value = -254

# bitmask used to select only 16 bits from the bottom value (for signed integers)
bitmask = 0x0000FFFF

# In order to do this shift the top value 16 bits and add it to the bottom value
val = (top_value << 16) + (bot_value & bitmask)

# Send (Publish) the value continuously
while(1):

    # Start a try in case we have an error
    try:
        # Every one second
        time.sleep(1)

        # Publish the value (integer) as a string. All messages are strings
        client.publish(topics["alien"][3], str(val))

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
        print("There was an error while publishing the data.")
