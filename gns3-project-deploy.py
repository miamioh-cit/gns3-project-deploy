#!/usr/bin/env python3
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
ID_FILE = "project-id"

try:
    with open(ID_FILE, 'r') as f:
        lines = f.readlines()
    logging.info(f"Opened '{ID_FILE}' successfully. Reading project IDs...")
except FileNotFoundError:
    logging.error(f"Project ID file '{ID_FILE}' not found. Exiting.")
    sys.exit(1)

project_ids = []
for line in lines:
    line = line.strip()
    if not line:
        continue

    if os.path.isfile(f"{line}-build.py"):
        project_ids.append(line)
    else:
        logging.warning(
            f"Ignoring project ID '{line}': "
            f"build script '{line}-build.py' not found."
        )

if not project_ids:
    logging.info("No valid project IDs found. Exiting.")
    sys.exit(0)

logging.info(f"Found project IDs: {project_ids}")

failed_projects = []
for pid in project_ids:
    script_name = f"{pid}-build.py"
    if not os.path.isfile(script_name):
        logging.error(f"Expected build script '{script_name}' not found. Skipping project {pid}.")
        failed_projects.append(pid)
        continue

    logging.info(f"Executing build script for project {pid} ({script_name})...")
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        logging.error(f"Build script {script_name} failed with return code {result.returncode}.")
        failed_projects.append(pid)
    else:
        logging.info(f"Build script {script_name} completed successfully.")

if failed_projects:
    logging.error(f"Deployment finished with errors in project(s): {', '.join(failed_projects)}")
    sys.exit(1)

logging.info("All specified project builds have been processed successfully.")
