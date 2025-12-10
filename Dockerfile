# Use official Python image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /opendrift-container

# Copy requirements first for caching
COPY requirements.txt /opendrift-container/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into container
COPY *.py /opendrift-container/
COPY DATA /opendrift-container/DATA/
COPY INPUT /opendrift-container/INPUT/


# Create output folder (optional, ensures folder exists)
RUN mkdir -p /opendrift-container/OUTPUT

# Default command when container runs
CMD ["python", "main.py"]
