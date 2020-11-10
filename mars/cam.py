#!/usr/bin/env python3
"""
The main control file for all logic functions.
Mechatronics 2

Callum Morrison, 2020
"""

import os

import cv2
import cv2.aruco as aruco
import numpy as np
import requests

from mars import logs

log = logs.create_log(__name__)


def init():
    url = "http://192.168.0.128:8080/shot.jpg"

    log.info(f"Connecting to camera at url: {url}")

    # Create two opencv named windows
    cv2.namedWindow("frame-image", cv2.WINDOW_AUTOSIZE)

    # Read and store calibration information
    Camera = np.load(os.path.join(
        "mars", "cam_data", "Sample_Calibration.npz"))
    CM = Camera['CM']  # Camera matrix
    dist_coef = Camera['dist_coef']  # Distortion coefficients from the camera

    # Load the ArUco Dictionary Dictionary 4x4_50 and set the detection parameters
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
    # pa = aruco.DetectorParameters_create()

    # Execute this continuously
    while True:

        # # Start the performance clock
        # start = time.perf_counter()

        # # Capture current frame from the camera
        # ret, frame = cap.read()

        # Read latest frame from IP camera
        try:
            resp = requests.get(url, stream=True).raw
        except Exception as e:
            log.exception("Unexpected error code when connecting to camera!")
            raise SystemError

        # Convert to openCV compatible image
        frame = np.asarray(bytearray(resp.read()), dtype="uint8")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        # # Convert the image from the camera to Gray scale
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Run the detection function
        corners, ids, rP = aruco.detectMarkers(frame, aruco_dict)

        # Draw the detected markers as an overlay on the original frame
        out = aruco.drawDetectedMarkers(frame, corners, ids)

        if ids is not None:
            # Calculate the pose of the marker based on the Camera calibration
            rvecs, tvecs, _objPoints = aruco.estimatePoseSingleMarkers(
                corners, 7, CM, dist_coef)

            for index, _ in enumerate(ids):
                out = aruco.drawAxis(out, CM, dist_coef,
                                     rvecs[index], tvecs[index], 10)

                position_string = f"X:{tvecs[0][0][0]} Y:{tvecs[0][0][1]} Z:{tvecs[0][0][2]}"
                log.debug(position_string)

        # Display the original frame in a window
        cv2.imshow('frame-image', out)

        # If the button q is pressed in one of the windows
        if cv2.waitKey(20) & 0xFF == ord('q'):
            # Exit the While loop
            break

    # close all windows
    cv2.destroyAllWindows()
    # exit the kernel
    exit(0)
