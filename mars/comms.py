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
    # Constructor to start the communication path
    def __init__(self):
        # Here is the list of properties of the class
        self.enabled = False
        self.acknowledged = False
        self.message_recieved_event = threading.Event()
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
            self.client.subscribe("Team-B-alien/5")
        else:
            log.error("Something went wrong - exit code: " + str(rc))

    # callback function for client class
    def __on_message(self, client, userdata, msg):
        self.message_recieved_event.set()
        self.acknowledged = True
        log.info(msg.topic + " Updated to " +
                 str(int(msg.payload.rstrip(b'\x00'))))

    # Function to enable listening and publishing data from the server
    def start_listening(self):
        self.client.loop_start()
        self.enabled = True
        log.info("Starting listening function")

    # Function to disable listening and publishing data from the server
    def stop_listening(self):
        self.client.loop_stop()
        self.enabled = False

    # Function to publish data to the desired channel
    def execute(self, command):
        channel = cmd.topics[command["dest"]
                             ][cmd.command_channels[command["command"]]]
        payload = command["payload"]
        self.client.publish(channel, payload)
        log.info("Data_published = " + payload + " On channel: " + channel)

    # Sender must be on a different thread to other commands

    def sender(self):
        self.start_listening()

        while self.enabled == True:
            # wait until there is data available by calling one of the commands
            cmd.data_avaliable.wait()

            self.execute(cmd.callstack[0])

            self.message_recieved_event.wait(timeout=3.0)
            # remove command from the callstack if signal message_recieved_event
            if self.message_recieved_event:
                cmd.callstack.pop(0)
                self.acknowledge = False
                self.message_recieved_event.clear()

            # Reset data_available if callstack is empty
            if not cmd.callstack:
                cmd.data_avaliable.clear()

        self.stop_listening()

    def run(self):
        t = threading.Thread(target=self.sender, name="Test sender")
        t.start()
