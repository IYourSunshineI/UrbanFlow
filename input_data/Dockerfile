# Lightweight Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Show the logs immediately
ENV PYTHONUNBUFFERED=1

# Copy the script into the container
COPY camera_sim.py .

# Install dependencies
RUN pip install requests argparse

# Define the command to run the application
# ENTRYPOINT allows us to pass arguments to the container like a native executable
ENTRYPOINT ["python", "camera_sim.py"]