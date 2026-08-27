#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


COURSE_DIR = Path("/app/course")
DEPLOY_SCRIPT = COURSE_DIR / "deploy-gns3-course.py"

GNS3_URL = os.getenv(
    "GNS3_URL",
    "http://127.0.0.1:3080"
)


def main() -> None:

    if not DEPLOY_SCRIPT.exists():
        raise RuntimeError(
            f"Course deployment script not found: {DEPLOY_SCRIPT}"
        )

    print("=" * 70)
    print("Running IT/OT Security Course deployment")
    print("=" * 70)
    print(f"GNS3 server: {GNS3_URL}")
    print("Modules: 1,2,3,4,5,6,7")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            str(DEPLOY_SCRIPT),
            "--gns3-url",
            GNS3_URL,
            "--modules",
            "all",
        ],
        cwd=COURSE_DIR,
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Course deployment failed with return code "
            f"{result.returncode}"
        )

    print("=" * 70)
    print("IT/OT Security Course deployment completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
