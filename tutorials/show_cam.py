import urllib.request
import cv2
import numpy as np
import time
import requests

url = "http://192.168.0.128:8080/shot.jpg"

while True:
    resp = requests.get(url, stream=True).raw
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # img_arr = np.array(bytearray(urllib.request.urlopen(URL).read()), dtype=np.uint8)
    # # img = cv2.imdecode(img_arr, -1)
    # cv2.imshow('IPWebcam', img)

    cv2.imshow('image', image)

    if cv2.waitKey(20) & 0xFF == ord('q'):
        # Exit the While loop
        break
