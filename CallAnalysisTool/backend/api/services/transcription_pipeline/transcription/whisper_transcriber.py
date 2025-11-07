"""
WhisperX Transcription Module
"""

import os
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Optional


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