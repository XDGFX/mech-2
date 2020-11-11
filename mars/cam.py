#!/usr/bin/env python3
"""
cam.py
Interfaces with an IP camera and provides vision system and image recognition functions.

Mechatronics 2
~ Callum Morrison, 2020
"""

import os
import time

import cv2
import cv2.aruco as aruco
import numpy as np
import requests

from mars import coords, logs, settings

coords = coords.coords()

log = logs.create_log(__name__)


class camera:
    """
    Class for all interactions with the video feed, image adjustments and recognition, aruco code identification, etc.
    """

    def __init__(self):
        self.out = ""
        self.stream = False

    def setup(self):
        """
        Used to initialise variables and create camera objects.
        """
        self.url = os.environ.get("CAM_IP")

        log.info(f"Connecting to camera at url: {self.url}")

        # # Create two opencv named windows
        # cv2.namedWindow("frame-image", cv2.WINDOW_AUTOSIZE)

        # Read and store calibration information
        Camera = np.load(os.path.join(
            "mars", "cam_data", "Sample_Calibration.npz"))
        self.CM = Camera['CM']  # Camera matrix
        # Distortion coefficients from the camera
        self.dist_coef = Camera['dist_coef']

        # Load the ArUco Dictionary Dictionary 4x4_50 and set the detection parameters
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        # pa = aruco.DetectorParameters_create()

    def generate(self):
        """
        Continuously reads the camera feed, and identifies aruco codes if required.
        """
        self.setup()

        while True:

            # # Start the performance clock
            # start = time.perf_counter()

            # # Capture current frame from the camera
            # ret, frame = cap.read()

            # Read latest frame from IP camera
            try:
                resp = requests.get(self.url, stream=True).raw
            except Exception as e:
                log.exception(
                    "Unexpected error code when connecting to camera!")
                raise SystemError

            # Convert to openCV compatible image
            frame = np.asarray(bytearray(resp.read()), dtype="uint8")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            # # Convert the image from the camera to Gray scale
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

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

                    coords.update(ids[index], rvecs[index], tvecs[index])
                    # position_string = f"X:{tvecs[0][0][0]} Y:{tvecs[0][0][1]} Z:{tvecs[0][0][2]}"
                    # log.debug(position_string)

            # # Display the original frame in a window
            # cv2.imshow('frame-image', out)

        #     # If the button q is pressed in one of the windows
        #     if cv2.waitKey(20) & 0xFF == ord('q'):
        #         # Exit the While loop
        #         break

        # # close all windows
        # cv2.destroyAllWindows()
        # # exit the kernel
        # exit(0)

    def video_feed(self):
        """
        Reads updated video feed and yields each frame to produce a live stream.
        """

        # Check that video has been started
        if self.out == "":
            return

        while self.stream:
            (flag, encodedImage) = cv2.imencode(".jpg", self.out)

            # Ensure the frame was successfully encoded
            if not flag:
                continue

            # Yield the output frame byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                  bytearray(encodedImage) + b'\r\n')

            time.sleep(1 / settings.FRAMERATE)
