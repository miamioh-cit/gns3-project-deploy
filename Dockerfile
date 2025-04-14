# Use a slim Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy everything from the build context into the container
COPY . /app

# Optional: install system-level dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sanity check: fail if any required files are missing
RUN test -f gns3-project-deploy.py && \
    test -f project-id && \
    test -f 281-build.py && \
    test -f 358-build.py && \
    test -f 386-build.py && \
    echo "✅ All required build scripts found."

# Give execute permissions to all .py scripts just in case
RUN chmod +x *.py

# Default command to run the deploy script
CMD ["python3", "gns3-project-deploy.py"]
