# Use an official Python image as base
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy your script and requirements
COPY requirements.txt .
COPY gns3-project-deploy.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python", "gns3-project-deploy.py"]
