#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_MODULES = "1,2,3,4,5,6,7"

# Path adjustment if running inside docker container structure
COURSE_DIR = ROOT / "course" if (ROOT / "course").exists() else ROOT

@dataclass(frozen=True)
class ModuleConfig:
    number: int
    short_name: str
    filename: str
    automated: bool = True
    note: str = ""

MODULES = {
    1: ModuleConfig(1, "Wastewater", "module_1_wastewater_flat.json"),
    2: ModuleConfig(2, "Freshwater", "module_2_freshwater_baseline.json"),
    3: ModuleConfig(3, "Traffic", "module_3_traffic_modbus.json"),
    4: ModuleConfig(4, "Manufacturing", "module_4_manufacturing_risk.json"),
    5: ModuleConfig(5, "Grid", "module_5_grid_purdue_segmented.json"),
    6: ModuleConfig(6, "Rail", "module_6_rail_purdue_monitoring.json"),
    7: ModuleConfig(7, "Capstone", "module_7_capstone_purdue_template.json"),
}

def api(session: Any, method: str, base_url: str, path: str, **kwargs: Any) -> Any:
    response = session.request(method, f"{base_url.rstrip('/')}{path}", timeout=30, **kwargs)
    response.raise_for_status()
    return response.json() if response.text else None

def parse_modules(raw: str) -> list[int]:
    if raw.lower().strip() == "all":
        return [1, 2, 3, 4, 5, 6, 7]
    result = []
    for part in raw.split(","):
        if part.strip():
            number = int(part)
            if number not in MODULES:
                raise SystemExit(f"Unknown module: {number}")
            result.append(number)
    return result

def load_topology(config: ModuleConfig) -> dict[str, Any]:
    config_path = COURSE_DIR / "configs" / config.filename
    if not config_path.exists():
        config_path = ROOT / "configs" / config.filename
    return json.loads(config_path.read_text(encoding="utf-8"))

def required_templates(topology: dict[str, Any]) -> set[str]:
    return {node.get("template", "ics-node") for node in topology.get("nodes", [])}

def session_from_env() -> Any:
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise SystemExit("The requests package is required. Install via requirements.txt") from exc
    session = requests.Session()
    user = os.getenv("GNS3_USER")
    password = os.getenv("GNS3_PASSWORD")
    if user and password:
        session.auth = (user, password)
    return session

def ensure_templates(session: Any, base_url: str, all_required: set[str]) -> dict[str, dict[str, Any]]:
    existing = api(session, "GET", base_url, "/v2/templates") or []
    tmap = {item.get("name", ""): item for item in existing}

    base_image = "ubuntu:latest"
    if "ics-node" in tmap and tmap["ics-node"].get("image"):
        base_image = tmap["ics-node"]["image"]
    else:
        for t_data in tmap.values():
            if t_data.get("image"):
                base_image = t_data["image"]
                break

    for req in all_required:
        if req not in tmap:
            print(f"🛠️  Auto-creating missing GNS3 template: '{req}'")
            payload = {
                "name": req,
                "template_type": "docker",
                "image": base_image,
                "compute_id": "local",
                "adapters": 4,
            }
            try:
                created = api(session, "POST", base_url, "/v2/templates", json=payload)
                tmap[req] = created
                print(f"  └─ Created template '{req}' (ID: {created.get('template_id')})")
            except Exception as exc:
                print(f"  └─ Warning: Failed to auto-create template '{req}': {exc}")

    return tmap

def icon_for(node: dict[str, Any]) -> str:
    name = node.get("name", "").lower()
    template = node.get("template", "").lower()
    mode = (node.get("env") or {}).get("NODE_MODE", "").lower()
    if "switch" in name or "switch" in template:
        return "switch.svg"
    if name.startswith("plc") or mode == "plc":
        return "plc.svg"
    if "hmi" in name or mode == "hmi":
        return "hmi.svg"
    if "historian" in name or "collector" in name or mode == "historian":
        return "historian.svg"
    if "router" in name or "fw" in name or "firewall" in name:
        return "firewall.svg"
    if "zeek" in name or "suricata" in name or "monitoring" in template:
        return "monitoring.svg"
    return "ot_node.svg"

def project_name(config: ModuleConfig, args: argparse.Namespace, copy_number: int) -> str:
    if args.copies == 1 and not args.student_prefix:
        return f"{args.project_prefix}-M{config.number:02d}-{config.short_name}-Master"
    index = args.start_index + copy_number - 1
    label = f"{args.student_prefix}{index:02d}" if args.student_prefix else f"Copy{index:02d}"
    return f"{args.project_prefix}-M{config.number:02d}-{config.short_name}-{label}"

def create_project(session: Any, base_url: str, template_map: dict[str, dict[str, Any]], config: ModuleConfig, topology: dict[str, Any], name: str, symbol_prefix: str | None) -> dict[str, Any]:
    try:
        existing_projects = api(session, "GET", base_url, "/v2/projects") or []
        for proj in existing_projects:
            if proj.get("name") == name:
                print(f"  └─ Removing pre-existing project instance: {name}")
                api(session, "DELETE", base_url, f"/v2/projects/{proj['project_id']}")
                break
    except Exception as err:
        print(f"  └─ Warning during project cleanup check: {err}")

    project = api(session, "POST", base_url, "/v2/projects", json={"name": name})
    project_id = project["project_id"]
    node_ids = {}
    records = []

    for idx, node in enumerate(topology.get("nodes", [])):
        template_name = node.get("template", "ics-node")
        t_info = template_map.get(template_name, {})
        template_id = t_info.get("template_id")
        
        if not template_id:
            raise RuntimeError(f"Template '{template_name}' not found on GNS3 server.")

        # Step 1: Instantiate node from template endpoint (x, y, compute_id strictly allowed)
        instantiate_payload = {
            "x": 100 + 180 * (idx % 4),
            "y": 100 + 120 * (idx // 4),
            "compute_id": "local"
        }
        created = api(session, "POST", base_url, f"/v2/projects/{project_id}/templates/{template_id}", json=instantiate_payload)
        node_id = created["node_id"]

        # Step 2: Update node properties via PUT
        update_payload: dict[str, Any] = {"name": node["name"]}
        if symbol_prefix:
            update_payload["symbol"] = f"{symbol_prefix.rstrip('/')}/{icon_for(node)}"
        
        if node.get("env"):
            env_str = "\n".join(f"{k}={v}" for k, v in node["env"].items())
            update_payload["properties"] = {"environment": env_str}

        api(session, "PUT", base_url, f"/v2/projects/{project_id}/nodes/{node_id}", json=update_payload)

        node_ids[node["name"]] = node_id
        records.append({"name": node["name"], "ip": node.get("ip", ""), "env": node.get("env", {})})
        
    links = 0
    next_port: dict[str, int] = {name: 0 for name in node_ids}
    for left, right in topology.get("links", []):
        if left not in node_ids or right not in node_ids:
            print(f"Skipping missing link: {left} -- {right}")
            continue
        left_port = next_port[left]
        right_port = next_port[right]
        next_port[left] += 1
        next_port[right] += 1
        payload = {
            "nodes": [
                {"node_id": node_ids[left], "adapter_number": 0, "port_number": left_port},
                {"node_id": node_ids[right], "adapter_number": 0, "port_number": right_port},
            ]
        }
        api(session, "POST", base_url, f"/v2/projects/{project_id}/links", json=payload)
        links += 1
        
    return {
        "module": config.number,
        "name": name,
        "project_id": project_id,
        "links": links,
        "nodes": records,
        "vlans": topology.get("vlans", []),
        "allowed_modbus_conduits": topology.get("allowed_modbus_conduits", []),
        "routing_notes": topology.get("routing_notes", []),
    }

def manifest(records: list[dict[str, Any]], skipped: list[str], args: argparse.Namespace) -> str:
    lines = ["# GNS3 Course Deployment Manifest", "", f"GNS3 server: `{args.gns3_url}`", f"Modules: `{args.modules}`", f"Copies per module: `{args.copies}`", ""]
    if skipped:
        lines += ["## Manual or Skipped Items", "", *[f"- {item}" for item in skipped], ""]
    for record in records:
        lines += [f"## Module {record['module']}: {record['name']}", "", f"Project ID: `{record['project_id']}`", f"Links created: `{record['links']}`", ""]
        if record.get("vlans"):
            lines += ["### VLANs and Zones", "", "| VLAN | Zone | Subnet | Gateway |", "|---:|---|---|---|"]
            for vlan in record["vlans"]:
                lines.append(f"| `{vlan.get('vlan', '')}` | `{vlan.get('name', '')}` | `{vlan.get('subnet', '')}` | `{vlan.get('gateway', '')}` |")
            lines.append("")
        if record.get("allowed_modbus_conduits"):
            lines += ["### Allowed Modbus Conduits", "", "| Source | Destination | Port | Purpose |", "|---|---|---:|---|"]
            for conduit in record["allowed_modbus_conduits"]:
                lines.append(f"| `{conduit.get('source', '')}` | `{conduit.get('destination', '')}` | `{conduit.get('port', '')}` | {conduit.get('purpose', '')} |")
            lines.append("")
        if record.get("routing_notes"):
            lines += ["### Routing Notes", ""]
            lines.extend(f"- {note}" for note in record["routing_notes"])
            lines.append("")
        lines += ["### Nodes", "", "| Node | IP | Environment |", "|---|---|---|"]
        for node in record["nodes"]:
            env = "<br>".join(f"`{k}={v}`" for k, v in node["env"].items())
            lines.append(f"| `{node['name']}` | `{node['ip']}` | {env} |")
        lines.append("")
    lines += ["## Lab Manager Follow-Up", "", "- Confirm each node IP address in GNS3.", "- Confirm environment variables from the table above.", "- Start PLCs before HMI/historian nodes.", "- Verify Modbus/TCP traffic on TCP/502 with a GNS3 packet capture.", "- Stop master projects before cloning for students."]
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser(description="Create multiple IT/OT course GNS3 projects and write a deployment manifest.")
    parser.add_argument("--gns3-url", default=os.getenv("GNS3_URL", "http://127.0.0.1:3080"))
    parser.add_argument("--modules", default=DEFAULT_MODULES, help="Comma list, or all.")
    parser.add_argument("--copies", type=int, default=1)
    parser.add_argument("--project-prefix", default="ITOT")
    parser.add_argument("--student-prefix", default="")
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--symbol-prefix", default=None)
    parser.add_argument("--manifest", default="deployment_manifest.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    modules = parse_modules(args.modules)
    
    print("=" * 70)
    print("Running IT/OT Security Course deployment")
    print("=" * 70)
    print(f"GNS3 server: {args.gns3_url}")
    print(f"Modules: {args.modules}")
    print("=" * 70)

    if args.dry_run:
        print("Dry run only. No GNS3 projects will be created.\n")
        return

    session = session_from_env()
    api(session, "GET", args.gns3_url, "/v2/version")

    all_required = set()
    for number in modules:
        config = MODULES[number]
        if config.automated:
            topology = load_topology(config)
            all_required.update(required_templates(topology))

    template_map = ensure_templates(session, args.gns3_url, all_required)

    records = []
    skipped = []
    for number in modules:
        config = MODULES[number]
        topology = load_topology(config)
        if not config.automated:
            skipped.append(f"Module {number}: {config.note}")
            print(f"Skipping Module {number}: {config.note}")
            continue

        for copy in range(1, args.copies + 1):
            name = project_name(config, args, copy)
            print(f"Creating {name}")
            try:
                records.append(create_project(session, args.gns3_url, template_map, config, topology, name, args.symbol_prefix))
            except Exception as exc:
                print(f"❌ Failed to deploy {name}: {exc}")
                skipped.append(f"Module {number} ({name}): Failed with error: {exc}")

    manifest_path = COURSE_DIR / args.manifest if (COURSE_DIR / "configs").exists() else Path(args.manifest)
    manifest_path.write_text(manifest(records, skipped, args), encoding="utf-8")
    print(f"Deployment complete. Manifest written to {manifest_path.resolve()}")
    print("=" * 70)
    print("IT/OT Security Course deployment completed successfully.")
    print("=" * 70)

if __name__ == "__main__":
    main()
