#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

GNS3_URL = os.getenv("GNS3_URL", "http://127.0.0.1:3080")
GNS3_USER = os.getenv("GNS3_USER", "")
GNS3_PASSWORD = os.getenv("GNS3_PASSWORD", "")

TOPOLOGY_FILE = Path("configs/module_2_freshwater_baseline.json")


# ============================================================
# GNS3 API HELPER
# ============================================================

def api(
    session: requests.Session,
    method: str,
    path: str,
    **kwargs
):
    url = f"{GNS3_URL.rstrip('/')}{path}"

    response = session.request(
        method,
        url,
        timeout=30,
        **kwargs
    )

    response.raise_for_status()

    if response.text:
        return response.json()

    return None


# ============================================================
# LOAD TOPOLOGY
# ============================================================

def load_topology():
    if not TOPOLOGY_FILE.exists():
        raise RuntimeError(
            f"Freshwater topology file not found: {TOPOLOGY_FILE}"
        )

    with TOPOLOGY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# CREATE PROJECT
# ============================================================

def build_freshwater():

    print("============================================================")
    print("480-2 Freshwater Treatment Deployment")
    print("============================================================")
    print(f"GNS3 Server: {GNS3_URL}")
    print(f"Topology:    {TOPOLOGY_FILE}")
    print("============================================================")

    topology = load_topology()

    session = requests.Session()

    if GNS3_USER and GNS3_PASSWORD:
        session.auth = (
            GNS3_USER,
            GNS3_PASSWORD
        )

    # --------------------------------------------------------
    # Verify GNS3
    # --------------------------------------------------------

    version = api(
        session,
        "GET",
        "/v2/version"
    )

    print(
        f"[OK] Connected to GNS3 "
        f"{version.get('version', 'unknown')}"
    )

    # --------------------------------------------------------
    # Get templates
    # --------------------------------------------------------

    templates = api(
        session,
        "GET",
        "/v2/templates"
    )

    template_map = {
        template["name"]: template["template_id"]
        for template in templates
    }

    required_templates = {
        node.get("template", "ics-node")
        for node in topology.get("nodes", [])
    }

    print("[INFO] Required templates:")

    for template_name in sorted(required_templates):
        print(f"       {template_name}")

        if template_name not in template_map:
            raise RuntimeError(
                f"Required GNS3 template not found: {template_name}"
            )

    # --------------------------------------------------------
    # Create project
    # --------------------------------------------------------

    project_name = topology["project_name"]

    project = api(
        session,
        "POST",
        "/v2/projects",
        json={
            "name": project_name
        }
    )

    project_id = project["project_id"]

    print(
        f"[OK] Created project "
        f"'{project_name}'"
    )

    print(
        f"[OK] Project ID: {project_id}"
    )

    # --------------------------------------------------------
    # Create nodes
    # --------------------------------------------------------

    node_ids = {}

    nodes = topology.get("nodes", [])

    for index, node in enumerate(nodes):

        name = node["name"]

        template_name = node.get(
            "template",
            "ics-node"
        )

        template_id = template_map[
            template_name
        ]

        x = 150 + 220 * (index % 3)
        y = 100 + 150 * (index // 3)

        payload = {
            "name": name,
            "template_id": template_id,
            "x": x,
            "y": y
        }

        created = api(
            session,
            "POST",
            f"/v2/projects/{project_id}/templates/{template_id}",
            json=payload
        )

        node_id = created["node_id"]

        node_ids[name] = node_id

        print(
            f"[OK] Created node "
            f"{name} "
            f"({template_name})"
        )

        if node.get("ip"):
            print(
                f"     IP: {node['ip']}"
            )

        if node.get("env"):
            for key, value in node["env"].items():
                print(
                    f"     {key}={value}"
                )

    # --------------------------------------------------------
    # Create links
    # --------------------------------------------------------

    link_count = 0

    next_port = {
        name: 0
        for name in node_ids
    }

    for left, right in topology.get("links", []):

        if left not in node_ids:
            print(
                f"[WARN] Missing node: {left}"
            )
            continue

        if right not in node_ids:
            print(
                f"[WARN] Missing node: {right}"
            )
            continue

        left_port = next_port[left]
        right_port = next_port[right]

        next_port[left] += 1
        next_port[right] += 1

        payload = {
            "nodes": [
                {
                    "node_id": node_ids[left],
                    "adapter_number": 0,
                    "port_number": left_port
                },
                {
                    "node_id": node_ids[right],
                    "adapter_number": 0,
                    "port_number": right_port
                }
            ]
        }

        api(
            session,
            "POST",
            f"/v2/projects/{project_id}/links",
            json=payload
        )

        link_count += 1

        print(
            f"[OK] Linked "
            f"{left} <-> {right}"
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("============================================================")
    print("Freshwater deployment complete")
    print("============================================================")
    print(f"Project: {project_name}")
    print(f"Project ID: {project_id}")
    print(f"Nodes: {len(node_ids)}")
    print(f"Links: {link_count}")
    print("Subnet: 10.10.20.0/24")
    print("============================================================")


# ============================================================
# MAIN
# ============================================================

def main():

    try:
        build_freshwater()

    except Exception as exc:

        print("============================================================")
        print("[FAIL] Freshwater deployment failed")
        print("============================================================")
        print(str(exc))
        raise


if __name__ == "__main__":
    main()
