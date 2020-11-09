# This is the vision library OpenCV
import cv2
# This is a library for mathematical functions for python (used later)
import numpy as np
# This is a library to get access to time-related functionalities
import time


# Select the first camera (0) that is connected to the machine
# in Laptops should be the build-in camera
cap = cv2.VideoCapture(0)

# Set the width and heigth of the camera to 640x480
cap.set(3,640)
cap.set(4,480)

#Create two opencv named windows
cv2.namedWindow("frame-image", cv2.WINDOW_AUTOSIZE)
cv2.namedWindow("gray-image", cv2.WINDOW_AUTOSIZE)

#Position the windows next to eachother
cv2.moveWindow("frame-image",0,100)
cv2.moveWindow("gray-image",640,100)

# Execute this continuously
while(True):
    
    # Start the performance clock
    start = time.perf_counter()
    
    # Capture current frame from the camera
    ret, frame = cap.read()
    
    # Convert the image from the camera to Gray scale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Display the original frame in a window
    cv2.imshow('frame-image',frame)

    # Display the grey image in another window
    cv2.imshow('gray-image',gray)
    
    # Stop the performance counter
    end = time.perf_counter()
    
    # Print to console the exucution time in FPS (frames per second)
    print ('{:4.1f}'.format(1/(end - start)))

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