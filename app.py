#!/usr/bin/env python3
"""
app.py
Starts and runs the main program code, boots up the webserver for access.

Mechatronics 2
~ Callum Morrison, 2020
"""

from dotenv import load_dotenv
import os
from mars import webapp


load_dotenv()


if os.environ.get("ENVIRONMENT") == "PRODUCTION":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_WEB":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_COMMS":
    from mars.comms import commands
    from time import sleep
    c = commands()
    c.start_comms()
    sleep(2)
    c.move("alien", 200, -54)
    sleep(20)
    c.stop_comms()
