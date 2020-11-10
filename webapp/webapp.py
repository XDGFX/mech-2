#!/usr/bin/env python3
from threading import Thread

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit, send
from mars import cam, logs

log = logs.create_log(__name__)

app = Flask(__name__)

sio = SocketIO(app, async_mode='threading')

# --- INITIALISATION ---

cam = cam.camera()


def serve():
    sio.run(app, host="0.0.0.0")


def start_server():
    thread = Thread(target=serve)
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
    # return the response generated along with the specific media
    # type (mime type)
    return Response(cam.video_feed(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# --- WEBSOCKET ROUTES ---


@sio.on('connect_camera')
def connect_camera():
    try:
        cam.generate()
    except Exception as e:
        log.error
