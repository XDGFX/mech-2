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

webapp.start_server()

print(os.environ.get("TEST"))
