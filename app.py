#!/usr/bin/env python3
"""
The main control file for all logic functions.
Mechatronics 2

Callum Morrison, 2020
"""

import os

from dotenv import load_dotenv

from mars import cam
from webapp import webapp

load_dotenv()

webapp.start_server()
# cam.init()

print(os.environ.get("TEST"))
