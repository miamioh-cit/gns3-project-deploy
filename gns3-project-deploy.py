import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
ID_FILE = "project-id"

# Read project IDs from file
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
        continue  # skip empty lines
    if line.isdigit():
        project_ids.append(int(line))
    else:
        logging.warning(f"Ignoring invalid project ID entry: {line}")

if not project_ids:
    logging.info("No valid project IDs found. Exiting.")
    sys.exit(0)
logging.info(f"Found project IDs: {project_ids}")

# Execute each project build script in sequence
for pid in project_ids:
    script_name = f"{pid}-build.py"
    if not os.path.isfile(script_name):
        logging.error(f"Expected build script '{script_name}' not found. Skipping project {pid}.")
        continue
    logging.info(f"Executing build script for project {pid} ({script_name})...")
    result = subprocess.run(["python", script_name])
    if result.returncode != 0:
        logging.error(f"Build script {script_name} failed with return code {result.returncode}.")
    else:
        logging.info(f"Build script {script_name} completed successfully.")

logging.info("All specified project builds have been processed.")
