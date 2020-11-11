#!/usr/bin/env python3
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
    print("Webserver started")

# --- SEND COMMANDS ---


def send(event, data):
    sio.emit(str(event), {'data': data})

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
    cam.stream = False
    time.sleep(2 / settings.FRAMERATE)
    cam.stream = True

    return Response(cam.video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# --- WEBSOCKET ROUTES ---


@sio.on('connect_camera')
def connect_camera():
    try:
        cam.generate()
    except Exception as e:
        log.error
