#!/usr/bin/env python3
"""
The communications file to send and recieve data from embedded robots
Mechatronics 2

~ Alberto Guerra Martinuzzi, 2020
"""
import json
import math
import time  # This is the library that will allow us to use the sleep function

import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import redis

from mars import logs, settings

# Initialise the logs class for debugging and data logging
log = logs.create_log(__name__)

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
        log.debug(msg.topic + " Updated to " +
                  str(data))

        # Check the message topic to identify device
        for item in self.channels:
            if msg.topic in self.channels[item]:
                #log.info("Message type: " + item)

                # Send the message and the device name to the message interpreter
                self.message_interpreter(item, data)
                return

        # If message topic not found an error must have occurred
        log.critical(
            "Channel error! message recieved does not match devices channels stored | channel type: " + msg.topic)

    def start_recieveing(self):
        """
        Enable the communication path with the mqtt server

        This is a blocking function used to handle communications with the MQTT server

        It recieves the connection staus of the devices
        """
        from mars.webapp import ws_send

        # Create the MQTT client object class
        self.client = mqtt.Client()

        # Assign the MQTT callback functions from the communications class
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message

        # Setup the username and password for the MQTT client
        self.client.username_pw_set(
            settings.USERNAME, password=settings.PASSWORD)

        # Connect to the given server
        self.client.connect(settings.SERVER_IP, settings.PORT, 60)

        # Log that communications have started
        log.info("Communications have started")

        prev_count = {}
        for device in settings.TOPICS:
            prev_count[device] = int(db.get(device + "-counter"))

            ws_send(f"status_{device}", "not connected")

        start_time = time.time()
        elapsed_time = 0

        # Main loop for checking incoming messages in the MQTT server
        # This is a blocking loop, it needs to be placed on a separate thread
        # The loop will break when the database "comms_enabled" variable is set to 0
        while int(db.get("comms_enabled")):

            # Update the elapsed time
            elapsed_time = time.time() - start_time

            # Every 5 seconds check the status of the counters, if a number has changed, the device must be connected
            if elapsed_time > 5:

                # Reset the elapsed time counter
                start_time = time.time()

                # Check the current count in every device
                for device in settings.TOPICS:
                    new_count = int(db.get(device + "-counter"))

                    # If the previous count + 1 is bigger than the new count, the counters have not changed
                    if (int(prev_count[device])+1) > new_count:
                        #log.warning(f"{device} not connected!")
                        ws_send(f"status_{device}", "not connected")
                    else:
                        ws_send(f"status_{device}", "connected")

                    # Reset the counters
                    prev_count[device] = db.get(device + "-counter")

            # Read messages from the server
            self.client.loop(timeout=settings.DATARATE)

            time.sleep(0.2)

    def start_sending_device(self):
        # Create the MQTT client object class
        self.client = mqtt.Client()

        # Setup the username and password for the MQTT client
        self.client.username_pw_set(
            settings.USERNAME, password=settings.PASSWORD)

        # Connect to the given server
        self.client.connect(settings.SERVER_IP, settings.PORT, 60)

        # Non blocking loop function
        self.client.loop_start()

    def start_sending_doors(self):
        # Create the MQTT client object class
        self.client = mqtt.Client()

        # Setup the username and password for the MQTT client
        self.client.username_pw_set(
            settings.USERNAME, password=settings.PASSWORD)

        # Connect to the given server
        self.client.connect(settings.SERVER_IP, settings.PORT, 60)

        # Log that communications have started
        log.info("Sending communications have started - Doors")

        prev_doors_state = json.loads(db.get("doors_state"))

        # set all the doors to initial state
        for index, _ in enumerate(prev_doors_state):
            self.change_door_state(index, prev_doors_state[index])
            time.sleep(1)

        # Main loop for checking incoming messages in the MQTT server
        # This is a blocking loop, it needs to be placed on a separate thread
        # The loop will break when the database "comms_enabled" variable is set to 0
        while True:
            # Read messages from the server
            self.client.loop(timeout=0.1)

            time.sleep(0.2)

            # Check the database for the door status, if changed, publish the data
            doors_state = json.loads(db.get("doors_state"))

            if doors_state != prev_doors_state:
                for index, _ in enumerate(doors_state):
                    if doors_state[index] != prev_doors_state[index]:
                        # send message to arduino to change state if door status has changed
                        self.change_door_state(index, doors_state[index])

                        time.sleep(1)

                prev_doors_state = doors_state

    def change_door_state(self, door, state):

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

        self.client.publish(MainTopic, str(cmd))

    def execute(self, device, instruction, payload):
        """
        Publish commands to the mqtt server
        """

        # Select channel to which to send the payload, instruction must match the data channels defined
        ch = self.channels[device][settings.DATA_CHANNELS[instruction]]

        # Publish to the MQTT server
        self.client.publish(ch, payload)

        # Log the data published for debugging
        log.debug("Data published = " + payload + " On channel: " + ch)

    def device_move_status(self, device):
        """
        Function to change the "moving" database status of a given device to true
        """
        # Load status from the database
        status = json.loads(db.get(f"{device}_current_status"))

        # Change moving status to True
        status["moving"] = True

        # Save status to database
        db.set(f"{device}_current_status", json.dumps(status))

    def device_stop_status(self, device):
        """
        Function to change the "moving" database status of a given device to false
        """

        # Load status from the database
        status = json.loads(db.get(f"{device}_current_status"))

        # Change moving status to False
        status["moving"] = False

        # Save status to database
        db.set(f"{device}_current_status", json.dumps(status))

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

        # Check message recieved with all the message types
        for key in settings.DEVICE_MESSAGES:

            if data == settings.DEVICE_MESSAGES[key]:
                # If message recieved identified, perform function according to the type of message
                func = self.device_functions.get(key)
                func(device)

                # log device message interpretation
                log.debug(device + " status is: " + key)
                return


class commands:
    def __init__(self):
        """
        Class constructor
        """
        self.forward_start_time = time.time()
        # self.comms = communications()
        # thread = threading.Thread(target=self.comms.start)
        # thread.start()

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

        db.set("comms_enabled", 0)
        time.sleep(1)
        db.set("comms_enabled", 1)

        # Create the status dictionaries for the alien, engineer
        alien = {
            "moving": False,
            "action": False
        }

        engineer = {
            "moving": False,
            "action": False
        }

        # Create a counter for each device to check their connection status
        db.incr("engineer-counter")
        db.incr("alien-counter")
        db.incr("compound-counter")

        # Store the stauses in the database
        db.set("alien_current_status", json.dumps(alien))
        db.set("engineer_current_status", json.dumps(engineer))

        # Start the communications objects
        self.comms = communications()
        self.comms.start_recieveing()

    def device_send(self):
        """
        Start the communication with the server
        """

        # Start the communications objects
        self.comms = communications()
        self.comms.start_sending_device()

        # Log that communications have started
        log.info(f"Sending communications have started")

    def doors_send(self):
        """
        Start the communication with the server
        """

        # Start the communications objects
        self.comms = communications()
        self.comms.start_sending_doors()

    def move(self, device, distance, angle):
        """
        Sends a move command to the selected device
        ```device``` is a string representing the the robot to communicate with
        ```distance``` is a positive integer with the distance (mm) to move
        ```angle``` is a signed float in radians with the relative angle to turn
        """

        # Change the angle from radians to degrees and send the inverse negative angle
        angle = -int(math.degrees(angle))

        # multiply the distance by a calibration factor to get approximate distance in mm
        distance = distance * settings.DIST_MULTIPLIER

        if distance > settings.MAX_DISTANCE:
            distance = settings.MAX_DISTANCE
        else:
            # Change the distance to an integer
            distance = int(distance)

        # combine angle and distance information in one message
        payload = self.merge_data(distance, angle)

        self.comms.execute(device, "move", payload)

    def stop(self, device):
        """
        Sends a stop command to the selected device
        ```device``` is a string representing the the robot to communicate with
        """

        payload = "0"
        self.comms.execute(device, "stop", payload)

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

        # Create your main topic string. Everything else should be fields with values 1-8
        MainTopic = "ALIEN_SELF_ISOLATION-alien/7"

        # Calculate angle threshold based on exponential function
        # threshold_angle = 0.4
        threshold_angle = 0.6 * math.exp(-0.1 * (magnitude + 2)) + 0.1
        threshold_magitude = 0.1

        # Turn right
        if direction < (0 - threshold_angle):
            log.debug("Turn left")
            self.comms.client.publish(MainTopic, str(2))

        # Turn left
        elif direction > (0 + threshold_angle):
            log.debug("Turn right")
            self.comms.client.publish(MainTopic, str(1))

        # Forward
        elif magnitude > threshold_magitude:
            log.debug("Forwards")
            self.comms.client.publish(MainTopic, str(3))

        # Stop
        else:
            log.debug("Stop")
            self.comms.client.publish(MainTopic, str(0))

    def simple_engineer_move(self, magnitude, direction):
        """
        Simple communication for direct Python to C code for the Arduino.

        Send commands:
        direction:
        0: Stop
        1: Left
        2: Right
        3: Forward
        """

        # Create your main topic string. Everything else should be fields with values 1-8
        MainTopic = "ALIEN_SELF_ISOLATION-engineer/7"

        # Calculate angle threshold based on exponential function
        # threshold_angle = 0.4
        threshold_angle = 0.6 * math.exp(-0.1 * (magnitude + 2)) + 0.1
        threshold_magitude = 0.1

        # Turn right
        if direction < (0 - threshold_angle):
            log.debug("Turn left")
            self.comms.client.publish(MainTopic, str(2))

        # Turn left
        elif direction > (0 + threshold_angle):
            log.debug("Turn right")
            self.comms.client.publish(MainTopic, str(1))

        # Forward
        elif magnitude > threshold_magitude:
            # Only if time delay has been met
            time_remain = self.forward_start_time + 1 / settings.FORWARD_RATE - time.time()

            # if time_remain < 0:
            #     log.debug("Forwards")
            self.comms.client.publish(MainTopic, str(3))

                # self.forward_start_time = time.time()

        # Stop
        else:
            log.debug("Stop")
            self.comms.client.publish(MainTopic, str(0))
