# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=16.x \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    chromium \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend dependencies and install them
COPY application-ui/package*.json application-ui/
RUN cd application-ui && npm install

# Copy the application code
COPY scripts/ scripts/
COPY config/ config/
COPY application/ application/
COPY application-ui/ application-ui/

# Build frontend for production
RUN cd application-ui && npm run build

# Expose ports
EXPOSE 5000 8080

# Set the default command
CMD ["python", "-m", "scripts.app"] 