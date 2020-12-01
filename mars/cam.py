#!/usr/bin/env python3
"""
cam.py
Interfaces with an IP camera and provides vision system and image recognition functions.

Mechatronics 2
~ Callum Morrison, 2020
"""

import math
import os
import time

import cv2
from cv2 import aruco
import numpy as np
import requests

from mars import logs, settings

log = logs.create_log(__name__)


class camera:
    """
    Class for all interactions with the video feed, image adjustments and recognition, aruco code identification, etc.
    """

    def __init__(self):
        self.out = ""
        self.allow_stream = False
        self.allow_generate = False

    def setup(self):
        """
        Used to initialise variables and create camera objects.
        """
        from mars import coords
        self.coords = coords.coords()

        self.url = os.environ.get("CAM_IP")

        log.info(f"Using camera url: {self.url}")

        # Read and store calibration information
        Camera = np.load(os.path.join(
            "mars", "cam_data", "Calibration.npz"))
        self.CM = Camera['CM']

        # Distortion coefficients from the camera
        self.dist_coef = Camera['dist_coef']

        # Load the ArUco Dictionary Dictionary 4x4_50 and set the detection parameters
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

    def generate(self):
        """
        Continuously reads the camera feed, and identifies aruco codes if required.
        """

        # Perform camera setup if not already complete
        self.setup()

        while self.allow_generate:
            # Save start time to synchronise framerate
            start_time = time.time()

            # Toggle to allow connection to a USB camera
            if os.environ.get("REAL_CAM"):
                try:
                    _, frame = cv2.VideoCapture(0).read()
                except Exception as e:
                    log.exception("Unable to connect to physical camera!")
                    raise

            else:
                # Read latest frame from IP camera
                try:
                    resp = requests.get(self.url, stream=True).raw
                except Exception as e:
                    log.exception(
                        "Unexpected error code when connecting to IP camera!")
                    raise

                # Convert to openCV compatible image
                frame = np.asarray(bytearray(resp.read()), dtype="uint8")
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            # Run the detection function
            corners, ids, rP = aruco.detectMarkers(frame, self.aruco_dict)

            # Draw the detected markers as an overlay on the original frame
            self.out = aruco.drawDetectedMarkers(frame, corners, ids)

            if ids is not None:
                # Calculate the pose of the marker based on the Camera calibration
                rvecs, tvecs, _objPoints = aruco.estimatePoseSingleMarkers(
                    corners, 7, self.CM, self.dist_coef)

                for index, _ in enumerate(ids):
                    self.out = aruco.drawAxis(self.out, self.CM, self.dist_coef,
                                              rvecs[index], tvecs[index], 10)

                    # Convert Rodriguez's angles to rotation matrix
                    R = cv2.Rodrigues(rvecs[index][0])[0]

                    # Convert rotation matrix to yaw (Euler angles)
                    # Adapted from @kangaroo on stackoverflow.com
                    cosine_for_pitch = math.sqrt(R[0][0] ** 2 + R[1][0] ** 2)

                    is_singular = cosine_for_pitch < 10**-6
                    if not is_singular:
                        yaw = math.atan2(R[1][0], R[0][0])
                    else:
                        yaw = math.atan2(-R[1][2], R[1][1])

                    self.coords.update(ids[index], tvecs[index], yaw)

            # Wait until the next frame is required
            end_time = time.time()
            time_remain = start_time + 1 / settings.FRAMERATE - end_time

            if time_remain > 0:
                time.sleep(time_remain)

    def video_feed(self):
        """
        Reads updated video feed and yields each frame to produce a live stream.
        """

        # Check that video has been started
        if self.out == "":
            return

        # Loop until a new session is created
        while self.allow_stream:
            # Save start time to synchronise framerate
            start_time = time.time()

            # Encode image in .jpg format
            (flag, encodedImage) = cv2.imencode(".jpg", self.out)

            # Ensure the frame was successfully encoded
            if not flag:
                continue

            # Yield the output frame byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                  bytearray(encodedImage) + b'\r\n')

            # Wait until the next frame is required
            end_time = time.time()
            time_remain = start_time + 1 / settings.FRAMERATE - end_time

            if time_remain > 0:
                time.sleep(time_remain)
