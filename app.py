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
    import threading
    c = commands()
    t = threading.Thread(target=c.start_comms)
    t.start()
    sleep(2)
    c.move("engineer", 500, 1)
    sleep(35)
    c.move("engineer", 50, 0)
    sleep(10)
    c.stop("engineer")
    sleep(10)
    # c.start_comms()
