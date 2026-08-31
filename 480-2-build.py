#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth


COURSE_DIR = Path("/app/course")
DEPLOY_SCRIPT = COURSE_DIR / "deploy-gns3-course.py"

GNS3_URL = os.getenv("GNS3_URL", "http://127.0.0.1:3080")
GNS3_USER = os.getenv("GNS3_USER")
GNS3_PASSWORD = os.getenv("GNS3_PASSWORD")


def ensure_templates_exist(gns3_url: str) -> None:
    """Check for required GNS3 templates and create them dynamically if missing."""
    base_url = gns3_url.rstrip("/")
    api_url = f"{base_url}/v2/templates"
    
    # Configure auth if environment variables are present
    auth = HTTPBasicAuth(GNS3_USER, GNS3_PASSWORD) if GNS3_USER and GNS3_PASSWORD else None
    
    try:
        response = requests.get(api_url, auth=auth, timeout=10)
        response.raise_for_status()
        existing_templates = [t.get("name") for t in response.json()]
    except Exception as err:
        print(f"⚠️ Warning: Failed to query GNS3 templates API: {err}")
        return

    # 1. Provision Ethernet switch template if missing
    switch_names = ["Ethernet switch", "GNS3 Ethernet switch"]
    if not any(name in existing_templates for name in switch_names):
        print("🛠️ Creating missing 'Ethernet switch' template...")
        payload = {
            "name": "Ethernet switch",
            "template_type": "ethernet_switch",
            "category": "switch",
            "builtin": True
        }
        res = requests.post(api_url, json=payload, auth=auth)
        if res.status_code in (200, 201):
            print("  └─ Created 'Ethernet switch'")
        else:
            print(f"  └─ Failed to create 'Ethernet switch': {res.text}")

    # 2. Provision ics-node Docker template if missing
    if "ics-node" not in existing_templates:
        print("🛠️ Creating missing 'ics-node' template...")
        payload = {
            "name": "ics-node",
            "template_type": "docker",
            "image": "ics-node:latest",  # Update tag/repo if pulling from a registry
            "category": "guest",
            "adapters": 2
        }
        res = requests.post(api_url, json=payload, auth=auth)
        if res.status_code in (200, 201):
            print("  └─ Created 'ics-node'")
        else:
            print(f"  └─ Failed to create 'ics-node': {res.text}")


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

    # Auto-provision templates before running module build
    ensure_templates_exist(GNS3_URL)

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
