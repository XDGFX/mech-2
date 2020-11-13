#!/usr/bin/env python3
"""
The communications file to send and recieve data from embedded robots
Mechatronics 2

Alberto Guerra Martinuzzi, 2020
"""
from mars import logs, settings
from mars import commands as cmd
import paho.mqtt.client as mqtt  # This is the library to do the MQTT communications
import time  # This is the library that will allow us to use the sleep function
import threading

log = logs.create_log(__name__)


class communications:

    def __init__(self, topics_to_listen, cmd_to_execute):
        """
        Constructor of the class
        """
        self.sent = False
        self.topics = topics_to_listen
        self.commands = cmd_to_execute
        self.acknowledged = False
        self.message_recieved_event = threading.Event()
        self.client = mqtt.Client()
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        self.client.username_pw_set("student", password="smartPass")
        self.client.connect(
            "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com", 31415, 60)
        log.info("Comms object created")

        self.message_interpretation = {
            "stopped": 0b000000001,   # Device is not moving
            "moving":  0b000000010   # Device is moving
        }

        self.moving = {
            "alien": False,
            "engineer": False
        }

    def release(self):
        """
        Stop any ocurring processes
        """
        log.warning("Class object deleted")
        self.client.loop_stop()
        self.client.disconnect()

    def __on_connect(self, client, userdata, flags, rc):
        """
        Callback function upon connection to the mqtt server
        """
        if rc == 0:
            log.info("Connection succesful")
            # Subscribe to all channels
            for t in self.topics:
                self.client.subscribe(self.topics[t][5])
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
        if msg.topic in self.topics["alien"]:
            log.info("message type alien")
            self.interpreter("alien", data)

        elif msg.topic in self.topics["engineer"]:
            log.info("message type engineer")
            self.interpreter("engineer", data)

        elif msg.topic in self.topics["compound"]:
            log.info("message type compound")
            self.interpreter("compound", data)

        else:
            log.error("channel error")

    def start_listening(self):
        """
        Enable the communication path with the mqtt server
        """
        self.client.loop_start()
        log.info("Starting listening function")

    # Function to disable listening and publishing data from the server
    def stop_listening(self):
        """
        Disable the communication path with the mqtt server
        """
        self.client.loop_stop()

    # Function to publish data to the desired channel
    def execute(self, channel, payload):
        """
        Publish commands to the mqtt server
        """
        self.client.publish(channel, payload)
        self.sent = True
        log.info("Data_published = " + payload + " On channel: " + channel)

    def interpreter(self, device, data):
        if data == self.message_interpretation["stopped"]:
            log.info(device + " has stopped")
            self.moving[device] = False
        elif data == self.message_interpretation["moving"]:
            log.info(device + " is moving")
            self.moving[device] = True
        else:
            log.error("Unknown message from: " +
                      device + " data = " + str(data))


class commands:
    def __init__(self):
        """
        Class constructor
        """
        self.alien_channels = [settings.TEAM_NAME +
                               "-alien/" + str(n) for n in range(1, 9)]
        self.enginner_channels = [settings.TEAM_NAME +
                                  "-engineer/" + str(n) for n in range(1, 9)]
        self.compound_channels = [settings.TEAM_NAME +
                                  "-compound/" + str(n) for n in range(1, 9)]
        self.topics = {
            "alien": self.alien_channels,
            "engineer": self.enginner_channels,
            "compound": self.compound_channels
        }
        self.command_channels = {
            "MV": 1,
            "STP": 3,
            "FNC": 5

        }

        # start up communications object
        self.comms = communications(self.topics, self.command_channels)

    def __merge_data(self, high_word, low_word):
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
        self.comms.start_listening()
        time.sleep(2)

    def stop_comms(self):
        time.sleep(2)
        self.comms.stop_listening()

    def send_command(self, device, instruction, payload):
        channel = self.topics[device][self.command_channels[instruction]]
        self.comms.execute(channel, payload)

    def move(self, device, distance, angle):
        if not self.comms.moving[device]:
            payload = self.__merge_data(distance, angle)
            self.send_command(device, "MV", payload)
        else:
            log.warning("Device already moving")
            pass

    def stop(self, device):
        if self.comms.moving[device]:
            payload = "0"
            self.send_command(device, "STP", payload)
        else:
            log.warning("Device not supposed to be moving")
            pass

    def function(self, device):
        value = 1
