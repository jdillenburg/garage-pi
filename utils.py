import subprocess
from datetime import datetime


def last_boot() -> datetime:
    """Returns the last time the system was booted."""
    p = subprocess.run(["uptime","-s"], capture_output=True)
    return datetime.fromisoformat(p.stdout.decode().strip())

