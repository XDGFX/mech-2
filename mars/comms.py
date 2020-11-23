#!/usr/bin/env python3
"""
The communications file to send and recieve data from embedded robots
Mechatronics 2

Alberto Guerra Martinuzzi, 2020
"""
import json
import math
import threading
import time  # This is the library that will allow us to use the sleep function

import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import redis

from mars import logs, settings

log = logs.create_log(__name__)

connected = threading.Event()

db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


class communications:

    def __init__(self):
        """
        Constructor of the class
        """
        self.channels = {}
        for item in settings.TOPICS:
            self.channels[item] = [settings.TEAM_NAME +
                                   "-" + item + "/" + str(n) for n in range(1, 9)]

        self.device_functions = {
            "stopped": self.device_stop_status,
            "moving":  self.device_move_status,
            "action":  self.device_action_status
        }

        self.client = mqtt.Client()
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        self.client.username_pw_set("student", password="smartPass")

    def __on_connect(self, client, userdata, flags, rc):
        """
        Callback function upon connection to the mqtt server
        """
        if rc == 0:
            # Subscribe to reciever channels for each device
            for item in self.channels:
                self.client.subscribe(
                    self.channels[item][settings.DATA_CHANNELS["recieve"]])

            # Finished connecting
            connected.set()

        else:
            log.error("Something went wrong - exit code: " + str(rc))

    def __on_message(self, client, userdata, msg):
        """
        Callback function upon message from the mqtt server
        Interpret messages and understand if robot has stopped moving or has recieved the message
        """
        data = int(msg.payload.rstrip(b'\x00'))
        log.info(msg.topic + " Updated to " +
                 str(data))

        for item in self.channels:
            if msg.topic in self.channels[item]:
                log.info("Message type: " + item)
                self.message_interpreter(item, data)
                return
        # If message topic not found an error must have occurred
        log.critical(
            "Channel error! message recieved does not match devices channels stored | channel type: " + msg.topic)

    def start(self):
        """
        Enable the communication path with the mqtt server
        """
        self.client.connect(
            "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com", 31415, 60)
        log.info("Communications have started")
        while int(db.get("comms_enabled")):
            self.client.loop(timeout=0.1)

    def restart(self):
        """
        Restart the communication path with the mqtt server
        """
        self.client.loop_stop()
        self.client.reconnect()
        self.client.loop_start()
        log.warning("Restarting communications ...")
        log.info("Communications have restarted")

    def execute(self, device, instruction, payload):
        """
        Publish commands to the mqtt server
        """
        ch = self.channels[device][settings.DATA_CHANNELS[instruction]]
        self.client.publish(ch, payload)
        log.info("Data published = " + payload + " On channel: " + ch)

    def device_move_status(self, device):
        status = json.loads(db.get(device))
        status["moving"] = True
        db.set(device, json.dumps(status))

    def device_stop_status(self, device):
        status = json.loads(db.get(device))
        status["moving"] = False
        db.set(device, json.dumps(status))

    def device_action_status(self, device):
        log.info("action ocurred")

    def message_interpreter(self, device, data):
        """
        Message recievd interpretation to update the status of devices
        """
        if device == "compound":
            status = json.loads(db.get(device))
            for key in settings.COMPOUND_MESSAGES:
                if data == settings.DEVICE_MESSAGES[key]:
                    # Flip status of door if message recieved
                    status[key] = not status[key]
                    db.set(device, json.dumps(status))
                    return
            log.error("Key not found for: " + device)

        else:
            for key in settings.DEVICE_MESSAGES:
                if data == settings.DEVICE_MESSAGES[key]:
                    func = self.device_functions.get(key)
                    func(device)
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
            # Start with all the doors closed
            compound[key] = False

        db.set("alien", json.dumps(alien))
        db.set("engineer", json.dumps(engineer))
        db.set("compound", json.dumps(compound))

        self.comms = communications()
        self.comms.start()

    def move(self, device, distance, angle):
        """
        Sends a move command to the selected device
        ```device``` is a string representing the the robot to communicate with
        ```distance``` is a positive integer with the distance (mm) to move
        ```angle``` is a signed float in radians with the relative angle to turn
        """
        status = json.loads(db.get(device))
        if not status["moving"]:
            payload = self.merge_data(distance, angle)
            self.comms.execute(device, "move", payload)
        else:
            log.warning("Device already moving")

    def stop(self, device):
        """
        Sends a stop command to the selected device
        ```device``` is a string representing the the robot to communicate with
        """
        status = json.loads(db.get(device))
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
