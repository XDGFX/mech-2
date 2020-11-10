#!/usr/bin/env python3
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from threading import Thread

app = Flask(__name__)

sio = SocketIO(app, async_mode='threading')

# --- INITIALISATION ---


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

# --- WEBSOCKET ROUTES ---


@sio.on('connect_camera')
def test_message():
    emit('my response', {'data': 'got it!'})
