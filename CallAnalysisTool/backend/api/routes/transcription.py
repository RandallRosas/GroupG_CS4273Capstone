"""
Transcription endpoints for audio processing and transcription management
"""

from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import os
import sys
import json
from datetime import datetime

from api.services.transcription_pipeline.transcription.whisperx_transcriber import TranscriptionConfig, transcribe_to_json, WhisperXTranscriber
from api.services.transcription_pipeline.speaker_separate.speaker_separation import speaker_separation
from api.services.transcription_pipeline.zip_processor import process_zip


transcription_bp = Blueprint('transcription', __name__)

# Output directory for transcriptions
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# Global transcriber instance (preloaded at startup)
_global_transcriber = None
_transcriber_config = None


def initialize_transcriber():
    """
    Initialize and preload the WhisperX transcriber model.
    This should be called once at Flask startup.
    """
    global _global_transcriber, _transcriber_config
    
    if _global_transcriber is None:
        print("=" * 60)
        print("Preloading WhisperX model on CPU...")
        print("=" * 60)
        
        _transcriber_config = TranscriptionConfig()
        _global_transcriber = WhisperXTranscriber(_transcriber_config)
        _global_transcriber.load_model()
        
        print("=" * 60)
        print("WhisperX model preloaded successfully!")
        print("=" * 60)
    
    return _global_transcriber


def get_transcriber():
    """
    Get the global transcriber instance.
    If not initialized, creates a new one (fallback).
    """
    global _global_transcriber
    if _global_transcriber is None:
        print("Warning: Transcriber not preloaded, initializing now...")
        initialize_transcriber()
    return _global_transcriber


@transcription_bp.route('/home', methods=['GET'])
def return_home():
    """
    Health check endpoint for transcription service
    
    Returns:
        JSON response confirming connection
    """
    return jsonify({
        'message': "Successfully connected to flask server"
    })


@transcription_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribes an incoming audio file using WhisperX and speaker separation.
    
    Request: multipart/form-data with 'file' field (zip file containing audio)
    Response: JSON with success message and filename
    """
    try:
        ######################### Transcription Pipeline #########################
        print("=" * 60)
        print("Starting transcription pipeline...")
        print("=" * 60)
        # Check if file exists in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was actually selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Received file: {file.filename}")
        file_path = OUTPUT_DIR / file.filename
        file.save(str(file_path))

        print(f"Extracting file to: {file_path}")
        folder_name = process_zip(file_path, output_dir=str(OUTPUT_DIR))
        os.remove(file_path)
        file_path = OUTPUT_DIR / folder_name
        audio_file = file_path / f"{folder_name}.wav"
        print(f"Audio file located at: {audio_file}")

        # ######################### Transcribe audio to JSON #########################

        # Create config for transcription
        config = TranscriptionConfig()
        print('### Transcribing Audio: ((dispatch audio).wav -> (transcription).json ###')

        # Call transcribe_to_json with correct parameters
        # audio_files: list, output_dir: string, config: TranscriptionConfig
        transcriber = get_transcriber()
        result = transcriber.transcribe(str(audio_file))

        # Get output transcription path
        model_size = config.model_size.replace('-', '')
        transcription_file = file_path / f"WhisperX_{model_size}_{folder_name}.json"

        with open(transcription_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Saved transcription to: {transcription_file}")

        # ######################### Speaker Separation #########################
        
        print('### Separating Speaker: ((transcription).json -> (transcription w/ separated speakers).json ###')
        speaker_separation(str(audio_file), transcription_file, file_path)
        os.remove(transcription_file)  # Removes old transcription file since new separated speakers transcription file is created
        print('### Finished Transcription Pipeline(Single): (transcription w/ separated speakers).json ###')

        #### Return ####
        return jsonify({
            'message': f'Finished transcription pipeline for: {file.filename}',
            'foldername': folder_name,
            'file_path': f"output/{folder_name}/{folder_name}.json"
        })
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Server error processing file', 'details': str(e)}), 500


@transcription_bp.route('/transcriptions', methods=['GET'])
def transcriptions_list():
    """
    Get all transcriptions in the output directory
    
    Returns:
        JSON response with list of all transcriptions and metadata
    """
    transcriptions = []
    # Loops over all transcriptions within output path
    for folder_path in OUTPUT_DIR.iterdir():
        # Skip if it's not a directory
        if not folder_path.is_dir():
            continue
        for file in folder_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                og_name = file.name.replace(".json", "")
                name = og_name.split('_')
                date = name[0]
                timestamp = name[1]
                dispatcher = '_'.join(name[2:])  # Join remaining parts for dispatcher name

                formatted_date = f"{date[:4]}/{date[4:6]}/{date[6:8]}"
                formatted_time = f"{timestamp[:2]}:{timestamp[2:4]}:{timestamp[4:6]}"

                print(formatted_date, formatted_time, dispatcher)
                # Transcription metadata
                transcription_info = {
                    'name': formatted_date + " " + formatted_time + " " + dispatcher,
                    'filename': og_name[:-5],
                    'file_path': str(file),
                    'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                    'file_size': file.stat().st_size,
                    'metadata': {
                        'total_segments': len(data.get('segments', [])),
                        'language': data.get('language', 'unknown'),
                        'audio_file': data.get('audio_file', 'unknown')
                    }
                }
                # Add to list of recent transcriptions
                transcriptions.append(transcription_info)
            except Exception as e:
                print(f"Error reading {file}: {e}")
                continue
    # Sort by creation date
    transcriptions.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({
        'success': True,
        'total_count': len(transcriptions),
        'transcriptions': transcriptions,
    })


@transcription_bp.route('/transcriptions/<filename>', methods=['GET'])
def get_transcription_by_filename(filename):
    """
    Get a specific transcription by filename
    
    Args:
        filename: The transcription filename (without extension)
    
    Returns:
        JSON response with transcription data and metadata
    """
    try:
        # Look for the file in output directory
        file_path = OUTPUT_DIR / filename / f"{filename}.json"
        audio_file = f"{filename}/{filename}.wav"
        print(file_path)
        
        if not file_path.exists():
            return jsonify({'error': 'Transcription file not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Returns transcription file + metadata
        return jsonify({
            'success': True,
            'filename': filename,
            'file_path': str(file_path),
            'audio_file': str(audio_file),
            'data': data  # Transcription.json stored here
        })
        
    except Exception as e:
        print(f"Error reading transcription {filename}: {str(e)}")
        return jsonify({'error': f'Failed to read transcription: {str(e)}'}), 500


@transcription_bp.route('/output/<path:filename>')
def serve_audio(filename):
    """
    Serve audio files from the output directory
    
    Args:
        filename: Path to the audio file relative to output directory
        Example: "20251017_123101_bjones/20251017_123101_bjones.wav"
    
    Returns:
        Audio file response
    """
    print(f"Serving audio file: {filename}")
    
    # Convert to absolute path
    output_dir = OUTPUT_DIR.resolve()
    
    # Split the filename into directory and file parts
    # filename is like "20251017_123101_bjones/20251017_123101_bjones.wav"
    path_parts = filename.split('/')
    
    if len(path_parts) > 1:
        # Has subdirectory: "20251017_123101_bjones/20251017_123101_bjones.wav"
        subdir = '/'.join(path_parts[:-1])  # "20251017_123101_bjones"
        file_name = path_parts[-1]  # "20251017_123101_bjones.wav"
        file_dir = output_dir / subdir
    else:
        # Just a filename
        file_name = filename
        file_dir = output_dir
    
    # Use send_from_directory with the directory and filename
    return send_from_directory(str(file_dir), file_name)