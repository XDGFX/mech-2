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
    from mars import comms, commands
    from time import sleep
    c = comms.communications()
    c.run()
    sleep(1)
    time = 0
    while time < 10:
        commands.function("alien")
        sleep(5)
        commands.function("alien")
        time = time + 1
