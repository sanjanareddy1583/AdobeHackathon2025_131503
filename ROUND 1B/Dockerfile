# Use a Python base image (you can choose a specific version like 3.10-slim)
FROM python:3.10-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script and other necessary folders into the container
# Ensure these paths match your local structure and the script's logic
COPY main.py .
COPY input/ input/
COPY persona/ persona/ 

# Command to run your Python script when the container starts
# This will depend on how your main.py is set up to handle inputs/outputs
CMD ["python", "main.py"]