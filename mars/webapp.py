#!/usr/bin/env python3
"""
webapp.py
Responsible for running the webserver and handling incomming HTTP and WebSocket requests.

Mechatronics 2
~ Callum Morrison, 2020
"""

import os
import threading
import time

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit, send
from mars import cam, logs, settings

log = logs.create_log(__name__)

app = Flask(__name__)

sio = SocketIO(app, async_mode='threading')


# --- INITIALISATION ---
cam = cam.camera()


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
