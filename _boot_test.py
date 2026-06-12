#!/usr/bin/env python
"""Minimal boot test for SANSKAR"""
import time
import json
import os
from datetime import datetime


print(f"SANSKAR process started - PID: {os.getpid()}")
print(f"Timestamp: {datetime.utcnow().isoformat()}Z")


time.sleep(0.5)


health = {
    "status": "healthy",
    "pid": os.getpid(),
    "timestamp": datetime.utcnow().isoformat() + "Z"
}
print(f"Health: {json.dumps(health)}")


time.sleep(1)
print("SANSKAR boot test complete")
