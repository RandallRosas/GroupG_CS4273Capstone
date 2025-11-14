# Use Python 3.9+ base image
FROM python:3.13.7

# Install system dependencies for audio processing and ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Note: PyTorch and WhisperX are large - this will take time
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port
EXPOSE 5001

# Run the Flask application
CMD ["python", "api/app.py"]