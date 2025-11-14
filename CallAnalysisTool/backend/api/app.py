#!/usr/bin/env python3
"""
Backend API for EMS Call Analysis Tool
Flask server that provides grading endpoints for 911 call transcripts
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from flask import Flask, jsonify
from flask_cors import CORS
from api.routes.grading import grading_bp
from api.routes.health import health_bp
from api.routes.transcription import transcription_bp, initialize_transcriber
from AIGrader import initialize_ollama

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # CORS configuration - allow frontend to connect
    # Supports both Vite (5173) and Next.js (3000) dev servers
    CORS(app, resources={
        r"/*": {  # Allow all routes
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(grading_bp, url_prefix='/api')
    app.register_blueprint(transcription_bp, url_prefix='/api')

    # Initialize the transcriber (Preloads the WhisperX model on CPU)
    initialize_transcriber()

    # Initialize Ollama (Preloads the llama3.1:8b model)
    initialize_ollama()
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Only print banner once (not during reloader restart)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("=" * 60)
        print("EMS Call Analysis API Server")
        print("=" * 60)
        print("Running on: http://localhost:5001")
        print("Health check: http://localhost:5001/api/health")
        print("Grade endpoint: http://localhost:5001/api/grade")
        print("Transcription endpoint: http://localhost:5001/api/transcription")
        print("=" * 60)

        
    
    app.run(host='0.0.0.0', port=5001, debug=True)

