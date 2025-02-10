# Use an official Python image as base
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy your script and requirements
COPY requirements.txt .
COPY 281build-new.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python", "281build-new.py"]
