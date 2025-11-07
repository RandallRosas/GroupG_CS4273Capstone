"""
Audio Transcription Script
Takes .wav files and outputs JSON transcriptions.

Usage:
  python transcribe_audio.py input.wav
  python transcribe_audio.py folder/
  python transcribe_audio.py file1.wav file2.wav file3.wav
"""

import os
import sys
import json
import argparse
from pathlib import Path
from whisper_transcriber import WhisperXTranscriber, TranscriptionConfig


def find_wav_files(paths):
    """Find all .wav files from given paths (files or directories)."""
    wav_files = []

    for path in paths:
        path_obj = Path(path)

        if path_obj.is_file() and path_obj.suffix.lower() == '.wav':
            wav_files.append(str(path_obj))
        elif path_obj.is_dir():
            # Find all .wav files in directory
            wav_files.extend([str(f) for f in path_obj.glob('*.wav')])
            wav_files.extend([str(f) for f in path_obj.glob('*.WAV')])

    return wav_files


def transcribe_to_json(audio_files, output_dir=None, config=None):
    """
    Transcribe audio files and save as JSON.

    Args:
        audio_files: List of audio file paths
        output_dir: Output directory (default: same as input file)
        config: TranscriptionConfig object
    """
    if not audio_files:
        print("No audio files found!")
        return

    print(f"Found {len(audio_files)} audio file(s) to transcribe\n")

    # Initialize transcriber
    transcriber = WhisperXTranscriber(config)

    # Process each file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {audio_file}")

        try:
            # Transcribe
            result = transcriber.transcribe(audio_file)

            original_stem = Path(audio_file).stem
            model_size = config.model_size.replace('-', '')  # Remove hyphens from model name
            new_filename = f"WhisperX_{model_size}_{original_stem}.json"

            # Determine output path
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                output_file = output_path / new_filename
            else:
                output_file = Path(audio_file).parent / new_filename

            # Save JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"[SUCCESS] Saved: {output_file}")
            print(f"  Language: {result['language']}")
            print(f"  Duration: {result['transcription_time']}s")
            print(f"  Segments: {result['num_segments']}")

        except Exception as e:
            print(f"[ERROR] Failed: {e}")

    print(f"\n{'=' * 80}")
    print(f"Completed! Processed {len(audio_files)} file(s)")
    print(f"{'=' * 80}")


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe .wav files to JSON using WhisperX (CPU only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe single file
  python transcribe_audio.py audio.wav

  # Transcribe all .wav files in a directory
  python transcribe_audio.py test-audio/

  # Transcribe multiple files
  python transcribe_audio.py file1.wav file2.wav file3.wav

  # Specify output directory
  python transcribe_audio.py audio.wav --output-dir transcriptions/

  # Use different model size
  python transcribe_audio.py audio.wav --model small
        """
    )

    parser.add_argument('inputs', nargs='+',
                        help='Audio file(s) or directory containing .wav files')
    parser.add_argument('--output-dir', '-o',
                        help='Output directory for JSON files (default: same as input)')
    parser.add_argument('--model', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                        help='WhisperX model size (default: base)')
    parser.add_argument('--language', default='en',
                        help='Language code (default: en)')
    parser.add_argument('--no-word-timestamps', action='store_true',
                        help='Disable word-level timestamps')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Batch size for processing (default: 16)')

    args = parser.parse_args()

    # Find all wav files
    audio_files = find_wav_files(args.inputs)

    if not audio_files:
        print("Error: No .wav files found!")
        sys.exit(1)

    # Create configuration
    config = TranscriptionConfig(
        model_size=args.model,
        language=args.language,
        word_timestamps=not args.no_word_timestamps,
        batch_size=args.batch_size
    )

    # Transcribe
    transcribe_to_json(audio_files, args.output_dir, config)


if __name__ == "__main__":
    main()