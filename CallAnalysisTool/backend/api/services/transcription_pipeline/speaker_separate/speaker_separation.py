"""
USAGE:
    python3 speaker_separation.py <audio_file.wav> <transcription.json>

    (python3 might not be necessary if running in a virtual environment)

    Arguments:
        audio_file.wav     - WAV audio file of emergency call
        transcription.json - WhisperX transcription JSON output with naming convention: YYYYMMDD_HHMMSS_dispatchername.json

    Output:
        Creates <audio_basename>.json in the same directory as the input JSON file
        Output format includes date, time, dispatcher name extracted from input filename

REQUIREMENTS:
    - Python 3.7+
    - numpy
    - librosa
"""
import numpy as np
import json
import os
import sys
import librosa

def load_whisperx_transcription(json_path):
    """
    Loads the WhisperX transcription data to get speech segments with timestamps and text.

    Args:
        json_path(str): The path to the WhisperX transcription JSON file.
    Returns:
        A list of dictionaries, each containing the start time, end time, text, and duration of a speech segment.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [{'start': s['start'], 'end': s['end'], 'text': s['text'].strip(),
             'duration': s['end'] - s['start']} for s in data['segments']]

def extract_mfcc_features(audio_path, n_mfcc=13, hop_length=512):
    """
    Extracts acoustic features (MFCCs) from the audio file.

    Args:
        audio_path(str): The path to the audio file.
        n_mfcc(int):     The number of MFCC coefficients to extract.
        hop_length(int): The hop length for the MFCC calculation.
    Returns:
        A tuple containing the MFCC matrix and the sample rate.
    """
    audio, sr = librosa.load(audio_path, sr=None)
    return librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length), sr

def analyze_mfcc_segments(mfccs, segments, sr, hop_length=512):
    """
    Aligns the transcription segments with the audio features.
    Calculates the MFCC statistics for each transcription segment.

    Args:
        mfccs(numpy.ndarray): The MFCC matrix.
        segments(list):       The list of transcription segments.
        sr(int):              The sample rate of the audio file.
        hop_length(int):      The hop length for the MFCC calculation.
    Returns:
        A list of dictionaries, each containing the start time, end time, text, duration, and MFCC statistics of a speech segment.
    """
    segment_analysis = []
    for segment in segments:
        start_frame = max(0, int(segment['start'] * sr / hop_length))
        end_frame = min(mfccs.shape[1], int(segment['end'] * sr / hop_length))

        coeffs = {}
        if start_frame < end_frame:
            segment_mfccs = mfccs[:, start_frame:end_frame]
            coeffs = {f'coeff_{i}_mean': float(np.mean(segment_mfccs[i, :])) for i in range(mfccs.shape[0])}
        else:
            coeffs = {f'coeff_{i}_mean': 0.0 for i in range(mfccs.shape[0])}

        segment_analysis.append({
            'start': segment['start'], 'end': segment['end'],
            'duration': segment['duration'], 'text': segment['text'], **coeffs
        })
    return segment_analysis

def classify_speakers(segment_analysis):
    """
    Classifies speech segments using acoustic grouping followed by linguistic assignment.

    Step 1 - Acoustic Grouping:
    - Calculate global average for each MFCC coefficient across all segments
    - For each segment, count coefficients above/below global averages
    - Group A: segments with more coefficients above global averages
    - Group B: segments with more coefficients below global averages

    Step 2 - Speaker Assignment:
    - Count questions (?) in each acoustic group
    - Group with more questions = dispatcher
    - Other group = caller
    - Long-form questions (3+ words) get moved to dispatcher

    Args:
        segment_analysis(list): The list of transcription segments with MFCC statistics.
    Returns:
        A dictionary containing the list of dispatcher and caller segments.
    """
    if not segment_analysis:
        return {'dispatcher': [], 'caller': []}

    global_averages = {}
    for i in range(13):
        coeff_name = f'coeff_{i}_mean'
        values = [segment[coeff_name] for segment in segment_analysis]
        global_averages[coeff_name] = sum(values) / len(values)

    group_a_segments = []
    group_b_segments = []

    for segment in segment_analysis:
        above_count = 0
        below_count = 0

        for i in range(13):
            coeff_name = f'coeff_{i}_mean'
            if segment[coeff_name] > global_averages[coeff_name]:
                above_count += 1
            else:
                below_count += 1

        if above_count > below_count:
            group_a_segments.append(segment)
            segment['_acoustic_group'] = 'A'
        else:
            group_b_segments.append(segment)
            segment['_acoustic_group'] = 'B'

    questions_a = sum(1 for s in group_a_segments if '?' in s['text'])
    questions_b = sum(1 for s in group_b_segments if '?' in s['text'])

    if questions_a >= questions_b:
        dispatcher_group = 'A'
    else:
        dispatcher_group = 'B'

    for segment in segment_analysis:
        segment['_predicted_speaker'] = 'dispatcher' if segment['_acoustic_group'] == dispatcher_group else 'caller'

    for segment in segment_analysis:
        if (segment.get('_predicted_speaker') == 'caller' and
            '?' in segment['text']):
            word_count = len(segment['text'].split())
            if word_count >= 3:
                segment['_predicted_speaker'] = 'dispatcher'

    return {
        'dispatcher': [s for s in segment_analysis if s.get('_predicted_speaker') == 'dispatcher'],
        'caller': [s for s in segment_analysis if s.get('_predicted_speaker') == 'caller']
    }

def kmeans_clustering(data, k=2, max_iters=100):
    """
    Implements the K-means clustering algorithm to group similar acoustic features.

    Args:
        data(numpy.ndarray): The data points to cluster.
        k(int):              The number of clusters to create.
        max_iters(int):      The maximum number of iterations to run.
    Returns:
        A tuple containing the cluster labels and the centroids.
    """
    n_samples = data.shape[0]
    centroids = data[np.random.choice(n_samples, k, replace=False)]

    for _ in range(max_iters):
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.sum((data - centroids[i])**2, axis=1)
        labels = np.argmin(distances, axis=1)

        new_centroids = np.zeros_like(centroids)
        for i in range(k):
            cluster_points = data[labels == i]
            new_centroids[i] = np.mean(cluster_points, axis=0) if len(cluster_points) > 0 else centroids[i]

        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids

    return labels, centroids

def extract_dispatcher_name(json_filename):
    """
    Extracts the dispatcher name from the JSON filename.
    Expected format: YYYYMMDD_HHMMSS_dispatchername.json

    Args:
        json_filename(str): The JSON filename.
    Returns:
        The dispatcher name extracted from the filename.
    """
    basename = os.path.splitext(os.path.basename(json_filename))[0]
    parts = basename.split('_')
    if len(parts) >= 3:
        date_part = parts[0]
        time_part = parts[1]
        dispatcher_name = '_'.join(parts[2:])  
        return date_part, time_part, dispatcher_name
    else:
        return "unknown", "unknown", "dispatcher"

def create_combined_transcript(speaker_segments, audio_basename, json_filename, output_path=None):
    """
    Formats and saves the final speaker-separated transcript as JSON in the new format.

    Args:
        speaker_segments(dict): A dictionary containing the list of dispatcher and caller segments.
        audio_basename(str):    The base name of the audio file (without extension). This is used to name the output file.
        json_filename(str):     The input JSON filename to extract dispatcher info from.
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

    date_str, time_str, dispatcher_name = extract_dispatcher_name(json_filename)

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
        'total_segments': len(all_segments),
        'speakers': [dispatcher_name, 'caller'],
        'segments': all_segments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

def speaker_separation(audio_file, transcription_file, output_dir):
    """
    Main function to perform speaker separation on audio and transcription data.

    Args:
        audio_file (str): Path to the audio file (.wav)
        transcription_file (str): Path to the WhisperX transcription JSON file
        output_dir (str): Directory where the output should be saved
    """
    if not os.path.exists(audio_file) or not os.path.exists(transcription_file):
        raise FileNotFoundError("Audio file or transcription file not found")

    mfccs, sr = extract_mfcc_features(audio_file)
    segments = load_whisperx_transcription(transcription_file)
    segment_analysis = analyze_mfcc_segments(mfccs, segments, sr)
    speaker_segments = classify_speakers(segment_analysis)

    # Create output filename based on audio file basename
    audio_basename = os.path.splitext(os.path.basename(audio_file))[0]

    # Use the output_dir and create the combined transcript there
    output_path = os.path.join(str(output_dir), f"{audio_basename}.json")
    create_combined_transcript(speaker_segments, audio_basename, transcription_file, output_path)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 speaker_separation.py <audio_file> <json_file>")
        return

    audio_file, json_file = sys.argv[1], sys.argv[2]
    if not os.path.exists(audio_file) or not os.path.exists(json_file):
        print("Error: File not found")
        return

    mfccs, sr = extract_mfcc_features(audio_file)
    segments = load_whisperx_transcription(json_file)
    segment_analysis = analyze_mfcc_segments(mfccs, segments, sr)
    speaker_segments = classify_speakers(segment_analysis)

    create_combined_transcript(speaker_segments, os.path.splitext(os.path.basename(audio_file))[0], json_file)

if __name__ == "__main__":
    main()