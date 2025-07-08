# Use a slim Python base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy required files explicitly
COPY gns3-project-deploy.py /app/
COPY 181-build.py /app/
COPY 225-build.py /app/
COPY 281-build.py /app/
COPY 284-build.py /app/
COPY 325-build.py /app/
COPY 358-build.py /app/
COPY 386-build.py /app/
COPY requirements.txt /app/
COPY project-id /app/
COPY datastore /app/

# Optional: install system utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python3", "gns3-project-deploy.py"]
