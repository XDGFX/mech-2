#!/usr/bin/env python3
"""
The main control file for all logic functions.
Mechatronics 2

Callum Morrison, 2020
"""

import os
import time

import cv2
import cv2.aruco as aruco
import numpy as np

# Select the first camera (0) that is connected to the machine
# in Laptops should be the build-in camera
cap = cv2.VideoCapture(0)

# Set the width and heigth of the camera to 640x480
cap.set(3, 640)
cap.set(4, 480)

# Create two opencv named windows
cv2.namedWindow("frame-image", cv2.WINDOW_AUTOSIZE)
cv2.namedWindow("gray-image", cv2.WINDOW_AUTOSIZE)

# Position the windows next to eachother
cv2.moveWindow("frame-image", 0, 100)
cv2.moveWindow("gray-image", 640, 100)

# Read and store calibration information
Camera = np.load(os.path.join("tutorials", "Sample_Calibration.npz"))
CM = Camera['CM']  # Camera matrix
dist_coef = Camera['dist_coef']  # Distortion coefficients from the camera

# Load the ArUco Dictionary Dictionary 4x4_50 and set the detection parameters
aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
pa = aruco.DetectorParameters_create()

# Execute this continuously
while(True):

    # # Start the performance clock
    # start = time.perf_counter()

    # Capture current frame from the camera
    ret, frame = cap.read()

    # Convert the image from the camera to Gray scale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Run the detection function
    corners, ids, rP = aruco.detectMarkers(gray, aruco_dict)

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
            print(position_string)

    # # Perform canny edge detection
    # threshold1 = 100
    # threshold2 = 200
    # blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # canny = cv2.Canny(blurred, threshold1, threshold2)

    # Display the original frame in a window
    cv2.imshow('frame-image', out)

    # # Display the grey image in another window
    # cv2.imshow('gray-image', canny)

    # # Stop the performance counter
    # end = time.perf_counter()

    # # Print to console the exucution time in FPS (frames per second)
    # print('{:4.1f}'.format(1 / (end - start)))

    # If the button q is pressed in one of the windows
    if cv2.waitKey(20) & 0xFF == ord('q'):
        # Exit the While loop
        break


# When everything done, release the capture
cap.release()
# close all windows
cv2.destroyAllWindows()
# exit the kernel
exit(0)
