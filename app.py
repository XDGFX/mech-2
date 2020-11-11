#!/usr/bin/env python3
"""
The main control file for all logic functions.
Mechatronics 2

Callum Morrison, 2020
"""

import os
from dotenv import load_dotenv

from webapp import webapp

load_dotenv()


if os.environ.get("ENVIRONMENT") == "PRODUCTION":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_WEB":
    webapp.start_server()

elif os.environ.get("ENVIRONMENT") == "DEV_COMMS":
    from mars import comms
    comms()