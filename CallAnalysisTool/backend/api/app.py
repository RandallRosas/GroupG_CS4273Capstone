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
from api.routes.dispatchers import dispatchers_bp
from api.routes.files import files_bp
from api.routes.regrade import regrade_bp
from api.routes.upload import upload_bp
from api.services.whisperx_transcriber import initialize_transcriber
from api.services.ollama_handler import initialize_ollama, check_ollama_ready


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # CORS configuration - allow frontend to connect
    # Supports both Vite (5173) and Next.js (3000) dev servers
    CORS(app, resources={
        r"/*": {  # Allow all routes
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(dispatchers_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')
    app.register_blueprint(regrade_bp, url_prefix='/api')
    
    # Add error handler to catch all unhandled errors
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        import sys
        error_traceback = traceback.format_exc()
        sys.stderr.write(f"\n{'='*60}\n")
        sys.stderr.write(f"UNHANDLED ERROR in Flask app: {str(e)}\n")
        sys.stderr.write(f"Traceback:\n{error_traceback}\n")
        sys.stderr.write(f"{'='*60}\n")
        sys.stderr.flush()
        print(f"\n{'='*60}\nUNHANDLED ERROR: {str(e)}\nTraceback:\n{error_traceback}\n{'='*60}\n", flush=True)
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'traceback': error_traceback if app.debug else None
        }), 500

    # In containerized environment, defer model initialization to avoid startup issues
    # Models will be initialized on first request if not already loaded
    if not _env_flag("DOCKER_CONTAINER"):
        try:
            # Initialize the transcriber (Preloads the WhisperX model on CPU)
            initialize_transcriber()

            # Initialize Ollama (Preloads the llama3.1:8b model)
            initialize_ollama()
        except Exception as e:
            print(f"Warning: Model initialization failed at startup: {e}")
            print("Models will be initialized on first request.")
    else:
        # In Docker, wait a bit for Ollama to start, then check readiness
        print("Waiting for Ollama to start...")
        try:
            if check_ollama_ready(max_retries=6, retry_delay=10):
                print("Ollama is ready!")
                initialize_ollama()
            else:
                print("Warning: Ollama readiness check failed. Will retry on first request.")
        except Exception as e:
            print(f"Warning: Could not check Ollama readiness: {e}")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    debug = _env_flag("FLASK_DEBUG", default=os.getenv("FLASK_ENV", "production").lower() == "development")
    
    # Only print banner once (not during reloader restart)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("=" * 60)
        print("EMS Call Analysis API Server")
        print("=" * 60)
        print(f"Running on: http://localhost:{port}")
        print(f"Dispatchers endpoint: http://localhost:{port}/api/dispatchers")
        print(f"Upload endpoint: http://localhost:{port}/api/upload")
        print(f"Files endpoint: http://localhost:{port}/api/files/<filename>")
        print("=" * 60)

        
    
    app.run(host='0.0.0.0', port=port, debug=debug)

