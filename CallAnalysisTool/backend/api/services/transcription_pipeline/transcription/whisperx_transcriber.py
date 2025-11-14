"""
WhisperX Transcription Module
"""

import os
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import sys
import json
import argparse

@dataclass
class TranscriptionConfig:
    """Configuration for WhisperX transcription"""
    implementation: str = "whisperx"
    model_size: str = "base"
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    language: Optional[str] = "en"  # Defaulted to English
    initial_prompt: Optional[str] = None
    word_timestamps: bool = True
    vad_filter: bool = False
    fp16: bool = False  # Always False for CPU
    condition_on_previous_text: bool = True
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    align_model: Optional[str] = None
    batch_size: int = 16

    def to_dict(self):
        return asdict(self)


class WhisperXTranscriber:
    """WhisperX transcription wrapper - CPU only"""

    def __init__(self, config: TranscriptionConfig = None):
        self.config = config or TranscriptionConfig()
        self.model = None
        self.device = "cpu"  # Always CPU
        self.whisperx = None

    def load_model(self):
        """Load WhisperX model on CPU."""
        try:
            import whisperx
            self.whisperx = whisperx
        except ImportError:
            raise ImportError(
                "WhisperX not installed."
            )

        print(f"Loading WhisperX-{self.config.model_size} on CPU...")

        self.model = whisperx.load_model(
            self.config.model_size,
            "cpu",
            compute_type="int8"  # Always int8 for CPU
        )
        print("Model loaded successfully!")

    def transcribe(self, audio_file: str) -> Dict:
        """
        Transcribe audio file

        Args:
            audio_file: Path to audio file

        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            self.load_model()

        print(f"Transcribing: {audio_file}")
        start_time = time.time()

        # Load audio
        audio = self.whisperx.load_audio(audio_file)

        # Transcribe
        result = self.model.transcribe(
            audio,
            batch_size=self.config.batch_size,
            language=self.config.language
        )

        # Align for word-level timestamps
        if self.config.word_timestamps:
            model_a, metadata = self.whisperx.load_align_model(
                language_code=result["language"],
                device=self.device
            )
            result = self.whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

        duration = time.time() - start_time

        # Format results to match test file structure
        return self._format_result(audio_file, result, duration)

    def _format_result(self, audio_file: str, result: Dict, duration: float) -> Dict:
        """Format transcription result to match test file structure exactly."""
        segments = []
        total_speech_duration = 0

        for seg in result.get("segments", []):
            segment_data = {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "confidence": 0.0,
                "no_speech_prob": 0.0,
                "compression_ratio": 0.0,
            }

            if "words" in seg:
                segment_data["words"] = seg["words"]

            segments.append(segment_data)
            total_speech_duration += (seg["end"] - seg["start"])

        return {
            "audio_file": os.path.basename(audio_file),
            "implementation": "whisperx",
            "config": self.config.to_dict(),
            "language": result.get("language", "unknown"),
            "language_confidence": 0.0,
            "transcription_time": round(duration, 2),
            "total_speech_duration": round(total_speech_duration, 2),
            "real_time_factor": round(total_speech_duration / duration, 2) if duration > 0 else 0,
            "num_segments": len(segments),
            "segments": segments,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "avg_no_speech_prob": 0.0,
                "avg_compression_ratio": 0.0,
            }
        }

    def transcribe_batch(self, audio_files: list) -> list:
        """Transcribe multiple audio files."""
        if self.model is None:
            self.load_model()

        results = []
        for audio_file in audio_files:
            try:
                result = self.transcribe(audio_file)
                results.append(result)
            except Exception as e:
                print(f"Error transcribing {audio_file}: {e}")
                results.append({
                    "audio_file": os.path.basename(audio_file),
                    "error": str(e)
                })

        return results


"""
Audio Transcription Script
Takes .wav files and outputs JSON transcriptions.

Usage:
  python whisperx_transcriber.py input.wav
  python whisperx_transcriber.py folder/
  python whisperx_transcriber.py file1.wav file2.wav file3.wav
"""

import os
import sys
import json
import argparse
from pathlib import Path

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
  python whisperx_transcriber.py audio.wav

  # Transcribe all .wav files in a directory
  python whisperx_transcriber.py test-audio/

  # Transcribe multiple files
  python whisperx_transcriber.py file1.wav file2.wav file3.wav

  # Specify output directory
  python whisperx_transcriber.py audio.wav --output-dir transcriptions/

  # Use different model size
  python whisperx_transcriber.py audio.wav --model small
        """
    )

    parser.add_argument('inputs', nargs='+',
                        help='Audio file(s) or directory containing .wav files')
    parser.add_argument('--output-dir', '-o',
                        help='Output directory for JSON files (default: same as input)')
    parser.add_argument('--model', default='large-v3',
                        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                        help='WhisperX model size (default: large-v3)')
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
