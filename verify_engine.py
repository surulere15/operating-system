#!/usr/bin/env python3
import sys
import platform
import json

def report():
    data = {
        "status": "success",
        "message": "Python Engine Operational",
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "node": platform.node()
    }
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    report()
