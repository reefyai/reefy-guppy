"""Exercise the AMD KFD and ROCm userspace with a real HIP kernel."""

from __future__ import annotations

import json
import os
import subprocess


def run():
    seconds = float(os.getenv('REEFY_HARDWARE_PROBE_SECONDS', '0.2'))
    result = subprocess.run(
        ['/app/hip_probe', str(seconds)], capture_output=True, text=True,
        timeout=max(30, seconds + 15), check=True)
    return json.loads(result.stdout.strip().splitlines()[-1])
