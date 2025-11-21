# Use Python 3.9+ base image
FROM python:3.13.7

# Install system dependencies for audio processing, ML libraries, and Ollama
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Note: PyTorch and WhisperX are large - this will take time
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download WhisperX models during build time
# This prevents downloads at runtime
RUN python -c "import whisperx; \
    print('Downloading WhisperX model: large-v3'); \
    whisperx.load_model('large-v3', 'cpu', compute_type='int8'); \
    print('Downloading alignment model for English'); \
    whisperx.load_align_model('en', 'cpu'); \
    print('All models downloaded successfully!')"

# Pre-download SentenceTransformer model for nature code detection
RUN python -c "from sentence_transformers import SentenceTransformer; \
    print('Downloading SentenceTransformer model: all-MiniLM-L6-v2'); \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    print('SentenceTransformer model downloaded successfully!')"

# Pre-download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Pre-download Ollama model during build time
# This makes the container completely self-contained
RUN ollama serve & \
    sleep 5 && \
    echo 'Downloading Ollama model: llama3.1:8b...' && \
    ollama pull llama3.1:8b && \
    echo 'Ollama model downloaded successfully!' && \
    pkill ollama

# Copy backend code
COPY . .

# Expose ports
EXPOSE 5001 11434

# Create startup script to run both Ollama and Flask
RUN echo '#!/bin/bash\n\
echo "Starting Ollama server..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
sleep 3\n\
echo "Starting Flask application..."\n\
python api/app.py &\n\
FLASK_PID=$!\n\
echo "Both services started. PIDs: Ollama=$OLLAMA_PID, Flask=$FLASK_PID"\n\
wait $OLLAMA_PID $FLASK_PID' > /app/start.sh && chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]