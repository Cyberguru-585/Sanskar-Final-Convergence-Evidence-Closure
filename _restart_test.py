#!/usr/bin/env python
"""Restart test for SANSKAR"""
import time
import json
import os
from datetime import datetime


print(f"SANSKAR process started - PID: {os.getpid()}")
print(f"Boot timestamp: {datetime.utcnow().isoformat()}Z")


time.sleep(1)
print("SANSKAR operational")


import signal

def handle_shutdown(signum, frame):
    print(f"SANSKAR graceful shutdown at {datetime.utcnow().isoformat()}Z")
    exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("SANSKAR interrupted")
