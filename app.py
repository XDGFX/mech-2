#!/usr/bin/env python3
"""
app.py
Starts and runs the main program code, boots up the webserver for access.

Mechatronics 2
~ Callum Morrison, 2020
"""

import os

from dotenv import load_dotenv

from mars import webapp

load_dotenv()


if os.environ.get("ENVIRONMENT") == "PRODUCTION":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_WEB":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_COMMS":
    from time import sleep

    from mars.comms import commands
    c = commands()
    c.start_comms()
    c.move("alien", 200, -54)
    sleep(20)
    c.start_comms()
