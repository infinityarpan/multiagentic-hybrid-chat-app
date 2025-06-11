# Use an official Python runtime as a parent image
FROM python:3.11.13-bullseye

# Set the working directory in the container
WORKDIR /app

# Install PostgreSQL client utilities and Tesseract OCR
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for the setup scripts
ENV PYTHONUNBUFFERED=1

# Expose the port FastAPI will run on
EXPOSE 8000