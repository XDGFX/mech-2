#!/usr/bin/env python3
"""
The communications file to send and recieve data from embedded robots
Mechatronics 2

Alberto Guerra Martinuzzi, 2020
"""
import json
from logging import warning
import math
import threading
import time  # This is the library that will allow us to use the sleep function

import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import redis

from mars import logs, settings

# Initialise the logs class for debugging and data logging
log = logs.create_log(__name__)

# Create threading event to check when connected to the MQTT server
connected = threading.Event()

# Initialise the local database for file handling
db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


class communications:

    def __init__(self):
        """
        Constructor of the class communication
        Creates all the necessary variables for operation
        """

        # Initialise the topics + channels
        # Channel names based on TEAM_NAME + TOPICS + CHANNELS(1-8)
        # This creates a dictionary with names determined by the topics and an array with all the channel names
        self.channels = {}

        for item in settings.TOPICS:
            self.channels[item] = [settings.TEAM_NAME +
                                   "-" + item + "/" + str(n) for n in range(1, 9)]

        # Dictionary containing the function calls to be used with the message interpreter
        self.device_functions = {
            "connected": self.device_connection_status,
            "stopped": self.device_stop_status,
            "moving":  self.device_move_status,
            "action":  self.device_action_status
        }

        # Create the MQTT client object class
        self.client = mqtt.Client()

        # Assign the MQTT callback functions from the communications class
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message

        # Setup the username and password for the MQTT client
        self.client.username_pw_set(
            settings.USERNAME, password=settings.PASSWORD)

    def __on_connect(self, client, userdata, flags, rc):
        """
        Callback function upon connection to the mqtt server
        """
        # Recieve code of 0 means no issues were encountered, otherwise, throw an error

        if rc == 0:

            # Subscribe to reciever channels for each device
            for item in self.channels:

                # Recieve channel used for communication from the arduino to python
                self.client.subscribe(
                    self.channels[item][settings.DATA_CHANNELS["recieve"]])

                # Connected channel used to check if the arduino is still connected and listening
                self.client.subscribe(
                    self.channels[item][settings.DATA_CHANNELS["connected"]])

            # Finished connecting, set the connected flag to true
            connected.set()

        else:
            # If recieved code is not zero, log an error with the exit code
            log.error("Something went wrong - exit code: " + str(rc))

    def __on_message(self, client, userdata, msg):
        """
        Callback function upon message from the mqtt server

        Interpret messages and update the status of the devices on the database
        """

        # convert recieved data into an integer
        data = int(msg.payload.rstrip(b'\x00'))

        # log the recieved change in data
        log.info(msg.topic + " Updated to " +
                 str(data))

        # Check the message topic to identify device
        for item in self.channels:
            if msg.topic in self.channels[item]:
                log.info("Message type: " + item)

                # Send the message and the device name to the message interpreter
                self.message_interpreter(item, data)
                return

        # If message topic not found an error must have occurred
        log.critical(
            "Channel error! message recieved does not match devices channels stored | channel type: " + msg.topic)

    def start(self):
        """
        Enable the communication path with the mqtt server

        This is a blocking function used to handle communications with the MQTT server
        """

        # Connect to the given server
        self.client.connect(settings.SERVER_IP, settings.PORT, 60)

        # Log that communications have started
        log.info("Communications have started")

        prev_count = {}

        # Main loop for checking incoming messages in the MQTT server
        # This is a blocking loop, it needs to be placed on a separate thread
        # The loop will break when the database "comms_enabled" variable is set to 0
        while int(db.get("comms_enabled")):

            # Check the counter before checking messages from the server
            for device in settings.TOPICS:
                prev_count[device] = db.get(device + "-counter")

            # Read messages from the server
            self.client.loop(timeout=settings.DATARATE)

            # Check for the connection counters again
            for device in settings.TOPICS:
                new_count = int(db.get(device + "-counter"))
                if (int(prev_count[device]) + 1) > new_count:
                    log.warning(f"{device} not connected!")

    def execute(self, device, instruction, payload):
        """
        Publish commands to the mqtt server
        """

        # Select channel to which to send the payload, instruction must match the data channels defined
        ch = self.channels[device][settings.DATA_CHANNELS[instruction]]

        # Publish to the MQTT server
        self.client.publish(ch, payload)

        # Log the data published for debugging
        log.info("Data published = " + payload + " On channel: " + ch)

    def device_move_status(self, device):
        """
        Function to change the "moving" database status of a given device to true
        """
        # Load status from the database
        status = json.loads(db.get(device))

        # Change moving status to True
        status["moving"] = True

        # Save status to database
        db.set(device, json.dumps(status))

    def device_stop_status(self, device):
        """
        Function to change the "moving" database status of a given device to false
        """

        # Load status from the database
        status = json.loads(db.get(device))

        # Change moving status to False
        status["moving"] = False

        # Save status to database
        db.set(device, json.dumps(status))

    def device_action_status(self, device):
        """
        Function to change the "action" database status of a given device
        Customizable action
        """

        log.info("action ocurred")

    def device_connection_status(self, device):

        # select counter to be incremented
        key = device + "-counter"

        # Increment device counter
        db.incr(key)

    def message_interpreter(self, device, data):
        """
        Message recieved interpretation to update the status of devices
        """

        # Alien and Engineer recieve the same type of messages, compound recieved other types of messages

        if device == "compound":

            # load the door status from the database
            status = json.loads(db.get(device))

            # Loop through each type of message to identify the door
            for key in settings.COMPOUND_MESSAGES:

                if data == settings.DEVICE_MESSAGES[key]:
                    # Flip status of door if message recieved
                    status[key] = not status[key]
                    db.set(device, json.dumps(status))
                    return

            log.error("Key not found for: " + device)

        else:
            # Check message recieved with all the message types
            for key in settings.DEVICE_MESSAGES:

                if data == settings.DEVICE_MESSAGES[key]:
                    # If message recieved identified, perform function according to the type of message
                    func = self.device_functions.get(key)
                    func(device)

                    # log device message interpretation
                    log.info(device + " status is: " + key)
                    return


class commands:
    def __init__(self):
        """
        Class constructor
        """
        self.comms = communications()
        thread = threading.Thread(target=self.comms.start)
        thread.start()

    def merge_data(self, high_word, low_word):
        """
        Function to combine 2 numbers in a 32 bit integer
        """
        # Mask for signed 32bit integers to get a signed 16bit integer
        bitmask = 0x0000FFFF
        # Shifts the high_word 16 bits and takes only the lower 16bits from the low_word
        msg = str((high_word << 16) + (low_word & bitmask))
        return msg

    def start_comms(self):
        """
        Start the communication with the server
        """

        # connected.clear()
        db.set("comms_enabled", 0)
        time.sleep(1)
        db.set("comms_enabled", 1)

        # Create the status dictionaries for the alien engineer and compount
        alien = {
            "moving": False,
            "action": False
        }

        engineer = {
            "moving": False,
            "action": False
        }

        compound = {}
        for key in settings.COMPOUND_MESSAGES:
            # Start with all the doors open
            compound[key] = True

        # Create a counter for each device to check their connection status
        db.incr("engineer-counter")
        db.incr("alien-counter")
        db.incr("compound-counter")

        # Store the stauses in the database
        db.set("alien", json.dumps(alien))
        db.set("engineer", json.dumps(engineer))
        db.set("compound", json.dumps(compound))

        # Start the communications objects
        self.comms = communications()
        self.comms.start()

    def move(self, device, distance, angle):
        """
        Sends a move command to the selected device
        ```device``` is a string representing the the robot to communicate with
        ```distance``` is a positive integer with the distance (mm) to move
        ```angle``` is a signed float in radians with the relative angle to turn
        """

        # Check current device status stored
        status = json.loads(db.get(device))

        # IF device IS NOT moving then send the command
        if not status["moving"]:

            # combine angle and distance information in one message
            payload = self.merge_data(distance, angle)

            self.comms.execute(device, "move", payload)

        else:

            log.warning("Device already moving")

    def stop(self, device):
        """
        Sends a stop command to the selected device
        ```device``` is a string representing the the robot to communicate with
        """

        # Check current device status stored
        status = json.loads(db.get(device))

        # If device IS moving then send the command
        if status["moving"]:

            payload = "0"
            self.comms.execute(device, "stop", payload)

        else:

            log.warning("Device not supposed to be moving")

    def action(self, device, select):
        """
        Sends a command to trigger an action
        ```device``` is a string representing the the robot to communicate with
        ```select``` is a string representing the action to perform by the robot
        """
        pass

    def simple_alien_move(self, magnitude, direction):
        """
        Simple communication for direct Python to C code for the Arduino.

        Send commands:
        direction:
        0: Stop
        1: Left
        2: Right
        3: Forward
        """

        # # Create the mqtt client object
        # client = mqtt.Client()
        client = self.comms.client

        # # Set the username and password
        # client.username_pw_set("student", password="smartPass")

        # # Connect to the server using a specific port with a timeout delay (in seconds)
        # client.connect(
        #     "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com", 31415, 60)

        # Create your main topic string. Everything else should be fields with values 1-8
        MainTopic = "ALIEN_SELF_ISOLATION-alien/7"

        # # Start the client to enable the above events to happen
        # client.loop_start()

        # Calculate angle threshold based on exponential function
        # threshold_angle = 0.4
        threshold_angle = 0.6 * math.exp(-0.1 * (magnitude + 2)) + 0.1
        threshold_magitude = 0.1

        # Turn right
        if direction < (0 - threshold_angle):
            log.info("Turn left")
            client.publish(MainTopic, str(2))

        # Turn left
        elif direction > (0 + threshold_angle):
            log.info("Turn right")
            client.publish(MainTopic, str(1))

        # Forward
        elif magnitude > threshold_magitude:
            log.info("Forwards")
            client.publish(MainTopic, str(3))

        # Stop
        else:
            log.info("Stop")
            client.publish(MainTopic, str(0))

    def door(self, door, state):
        client = self.comms.client

        # Create your main topic string. Everything else should be fields with values 1-8
        MainTopic = "ALIEN_SELF_ISOLATION-compound/7"

        # // 0: Door A Open
        # // 1: Door A Close
        # // 2: Door B Open
        # // 3: Door B Close
        # // 4: Door C Open
        # // 5: Door C Close
        # // 6: Door D Open
        # // 7: Door D Close

        if door == 0:
            cmd = 0

        elif door == 1:
            cmd = 2

        elif door == 2:
            cmd = 4

        elif door == 3:
            cmd = 6

        else:
            log.error(f"Invalid door: {door}")
            return

        if state == False:
            cmd += 1

        client.publish(MainTopic, str(cmd))
