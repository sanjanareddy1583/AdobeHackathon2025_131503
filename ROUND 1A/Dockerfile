# Use a newer, supported Debian distribution (bullseye instead of buster)
FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies required by PyMuPDF (fitz)
# These are crucial for faster and more reliable installation of PyMuPDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libopenjp2-7 \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Python dependencies file
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main script
COPY main.py .

# Command to run your application
CMD ["python", "main.py"]