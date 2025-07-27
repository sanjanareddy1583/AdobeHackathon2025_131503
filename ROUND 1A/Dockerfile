FROM --platform=linux/amd64 python:3.10

WORKDIR /app

# Copy the processing script
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Run the script
CMD ["python", "main.py"] 