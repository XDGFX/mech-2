#!/usr/bin/env python3
"""
webapp.py
Responsible for running the webserver and handling incomming HTTP and WebSocket requests.

Mechatronics 2
~ Callum Morrison, 2020
"""

import logging
import threading
import time

import redis
from flask import Flask, Response, render_template
from flask_socketio import SocketIO

from mars import cam, coords, logic, logs, settings

# --- INITIALISATION ---
log = logs.create_log(__name__)

app = Flask(__name__)
sio = SocketIO(app, async_mode='threading', log=None)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

cam = cam.camera()

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def serve():
    sio.run(app, host="0.0.0.0")


def start_server():
    thread = threading.Thread(target=serve)
    thread.start()
    log.info("Webserver started")


# --- SEND COMMANDS ---
def ws_send(event, data=None):
    sio.emit(str(event), data)


# --- WEBSERVER ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/video_feed")
def video_feed():
    """
    Return the response generated along with the specific media type (mime type)
    """

    # Terminate any existing video streams
    cam.allow_stream = False
    time.sleep(2 / settings.FRAMERATE)
    cam.allow_stream = True

    return Response(cam.video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# --- WEBSOCKET ROUTES ---
@sio.on('connect_camera')
def connect_camera():
    cam.allow_generate = False
    time.sleep(2 / settings.FRAMERATE)
    cam.allow_generate = True

    cam.generate()


@sio.on('start_engineer')
def start_engineer():
    logic.engineer().setup()
    logic.engineer().engineer_complete_tasks()


@sio.on('stop_engineer')
def stop_engineer():
    logic.engineer().setup()


@sio.on('increment_engineer_task')
def increment_engineer_task():
    r.incr("engineer_current_task")
    logic.engineer().engineer_complete_tasks()


@sio.on('decrement_engineer_task')
def decrement_engineer_task():
    r.decr("engineer_current_task")
    logic.engineer().engineer_complete_tasks()


@sio.on('start_alien')
def start_alien():
    logic.alien().setup()
    logic.alien().alien_follow()


@sio.on('stop_alien')
def stop_alien():
    logic.alien().setup()


@sio.on('initialise_doors')
def initialise_doors():
    coords.route().initialise_doors()


@sio.on('toggle_doors')
def toggle_doors(data):
    index = data["index"]
    state = data["state"]

    coords.route().doors(index, state)
