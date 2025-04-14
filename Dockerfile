# Use a slim Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all Python scripts and required files into the container
COPY *.py /app/
COPY project-id /app/
COPY requirements.txt /app/

# Optional: install system-level tools if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run the deploy script
CMD ["python3", "gns3-project-deploy.py"]

