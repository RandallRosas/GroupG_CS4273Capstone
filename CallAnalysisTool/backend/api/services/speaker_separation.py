import json
import os
import whisperx
import torch
import gc
from whisperx.diarize import DiarizationPipeline
import inspect

def in_docker():
    return os.path.exists("/.dockerenv")

def normalize_dispatcher_name(name):
    """
    Normalize a dispatcher name for transcript speaker labels.

    Falls back to a generic label if the provided value is missing or looks like
    a raw audio filename.
    """
    if not name:
        return "dispatcher"

    normalized = str(name).strip()
    if not normalized:
        return "dispatcher"

    if os.path.splitext(normalized)[1].lower() == ".wav":
        normalized = os.path.splitext(os.path.basename(normalized))[0]

    return normalized or "dispatcher"

def extract_dispatcher_name(basename):
    """
    Extracts the dispatcher name from the audio/folder basename.
    Expected format: YYYYMMDD_HHMMSS_dispatchername

    Args:
        basename(str): The base name (without extension) in format YYYYMMDD_HHMMSS_dispatchername
    Returns:
        A tuple of (date_part, time_part, dispatcher_name) extracted from the basename.
    """
    parts = basename.split('_')
    if len(parts) >= 3:
        date_part = parts[0]
        time_part = parts[1]
        dispatcher_name = normalize_dispatcher_name('_'.join(parts[2:]))
        return date_part, time_part, dispatcher_name
    else:
        return "unknown", "unknown", "dispatcher"

def create_combined_transcript(
    speaker_segments,
    audio_basename,
    json_filename,
    output_path=None,
    dispatcher_name=None,
    date_str=None,
    time_str=None
):
    """
    Formats and saves the final speaker-separated transcript as JSON in the new format.

    Args:
        speaker_segments(dict): A dictionary containing the list of dispatcher and caller segments.
        audio_basename(str):    The base name of the audio file (without extension). This is used to name the output file.
        json_filename(str):     The input JSON filename (used for output directory if output_path is None).
        output_path(str):       Optional full path for output file. If None, uses directory from json_filename.
    Returns:
        Saves the final speaker-separated transcript as <audio_basename>.json in the specified directory.
    """
    if output_path is None:
        output_dir = os.path.dirname(json_filename)
        if not output_dir:
            output_dir = "."
        output_file = os.path.join(output_dir, f"{audio_basename}.json")
    else:
        output_file = output_path

    # Prefer explicit metadata from the upload pipeline. Fall back to parsing the basename.
    parsed_date, parsed_time, parsed_dispatcher_name = extract_dispatcher_name(audio_basename)
    date_str = date_str or parsed_date
    time_str = time_str or parsed_time
    dispatcher_name = normalize_dispatcher_name(dispatcher_name or parsed_dispatcher_name)

    all_segments = []
    for speaker, segments in speaker_segments.items():
        speaker_label = dispatcher_name if speaker == 'dispatcher' else 'caller'
        for segment in segments:
            all_segments.append({
                'speaker': speaker_label, 'start': segment['start'],
                'end': segment['end'], 'text': segment['text']
            })

    all_segments.sort(key=lambda x: x['start'])

    transcript_data = {
        'date': int(date_str) if date_str.isdigit() else 0,
        'time': int(time_str) if time_str.isdigit() else 0,
        'agent_name': dispatcher_name,
        'total_segments': len(all_segments),
        'speakers': [dispatcher_name, 'caller'],
        'segments': all_segments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

def speaker_separation(audio_path, transcript_path, output_dir, dispatcher_name=None, date_str=None, time_str=None):
    """
    Main function to perform speaker separation on audio and transcription data.

    Args:
        audio_file (str): Path to the audio file (.wav)
        transcription_file (str): Path to the WhisperX transcription JSON file
        output_dir (str): Directory where the output should be saved
    """
    if not os.path.exists(audio_path) or not os.path.exists(transcript_path):
        raise FileNotFoundError("Audio file or transcription file not found")

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    audio = whisperx.load_audio(audio_path)

    with open(transcript_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = {'segments': data['segments'], 'language': 'en'}

    print("Aligning audio")
    align_model, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
    result = whisperx.align(result["segments"], align_model, metadata, audio, DEVICE, return_char_alignments=False)

    del align_model
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()

    # Diarizing audio
    print("Diarizing audio")
    print("DiarizationPipeline signature: ", inspect.signature(DiarizationPipeline))
    if not in_docker():
        diarize_model = DiarizationPipeline(token=os.getenv('HF_TOKEN'), device=DEVICE)
    else:
        diarize_model = DiarizationPipeline(device=DEVICE)
    diarize_segments = diarize_model(audio, min_speakers=2, max_speakers=2)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    del diarize_model
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()

    # Classify dispatcher based on questions
    speakers = set(seg.get('speaker', 'Unknown') for seg in result['segments'] if seg.get('speaker') != 'Unknown')
    if not speakers:
        speaker_segments = {'dispatcher': [], 'caller': []}
    else:
        speaker_texts = {spk: [seg['text'] for seg in result['segments'] if seg.get('speaker') == spk] for spk in speakers}
        questions = {spk: sum(1 for text in texts if '?' in text) for spk, texts in speaker_texts.items()}
        dispatcher_speaker = max(questions, key=questions.get) if questions else list(speakers)[0]

        for seg in result['segments']:
            spk = seg.get('speaker', 'Unknown')
            if spk == dispatcher_speaker:
                seg['_predicted_speaker'] = 'dispatcher'
            else:
                seg['_predicted_speaker'] = 'caller'

        # Move long questions from caller to dispatcher
        for seg in result['segments']:
            if seg.get('_predicted_speaker') == 'caller' and '?' in seg['text']:
                word_count = len(seg['text'].split())
                if word_count >= 3:
                    seg['_predicted_speaker'] = 'dispatcher'

        speaker_segments = {
            'dispatcher': [seg for seg in result['segments'] if seg.get('_predicted_speaker') == 'dispatcher'],
            'caller': [seg for seg in result['segments'] if seg.get('_predicted_speaker') == 'caller']
        }

    # Create output filename based on audio file basename
    audio_basename = os.path.splitext(os.path.basename(audio_path))[0]

    # Use the output_dir and create the combined transcript there
    output_path = os.path.join(str(output_dir), f"{audio_basename}.json")
    create_combined_transcript(
        speaker_segments,
        audio_basename,
        transcript_path,
        output_path,
        dispatcher_name=dispatcher_name,
        date_str=str(date_str) if date_str is not None else None,
        time_str=str(time_str) if time_str is not None else None,
    )

    return output_path


def main():
    # We don't need a main method unless we intend to test via the CLI
    print("speaker_separation.main() called")

if __name__ == "__main__":
    main()
