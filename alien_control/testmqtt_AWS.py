import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import time  # This is the library that will allow us to use the sleep function

# The callback for when we connect to the rerver. The meaning of the return code (rc) can be found here:
# https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901079
# A zero is good.
# After we connect we subsribe to one (or more) topics in this case the topic number 1


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MainTopic)


# The callback for when a PUBLISH message is received from the server. I.e. when a new value for the topic we subscribed to above updates
# the expression str(int(msg.payload.rstrip(b'\x00'))) converts the message from the server to an integer and then a string for printing.
# Specifically:
#   msg.payload.rstrip(b'\x00') This is getting all the bytes from the server (should be 11 in our case) and removes bytes with the value \x00 from the right
#   int() converts the remaining bytes into an integer, it threats them as a string
#   str() converts the integer into a string for the purpose of printing it. See below (l.56) for an alternative way to do this
def on_message(client, userdata, msg):
    print(str(time.time())+" In topic: "+msg.topic +
          " the value was " + str(int(msg.payload.rstrip(b'\x00'))))


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

# Create your main topic string. Everything else should be fields with values 1-8
MainTopic = "ALIEN_SELF_ISOLATION-alien/7"

# Start the client to enable the above events to happen
client.loop_start()

# Pick a value
val = 1

# Send (Publish) the value continuously
while(1):

    # Start a try in case we have an error
    try:
        # Every one second
        time.sleep(1)

        # Publish the value (integer) as a string. All messages are strings
        client.publish(MainTopic, str(val))

        # Plot in the terminal what we just did
        print("%s %d" % (MainTopic, val))

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
