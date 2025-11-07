import noisereduce as nr
import soundfile as sf
import numpy as np
import os

def run_noisereduce(input_path, output_path):
    """Simple test for noisereduce spectral gating."""
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    # Load audio
    data, rate = sf.read(input_path)

    # Convert to mono if stereo
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)

    # Apply noise reduction
    reduced = nr.reduce_noise(y=data, sr=rate)

    # Save cleaned audio
    sf.write(output_path, reduced, rate)
    print(f"Noise reduced file saved as: {output_path}")

if __name__ == "__main__":
    input_wav  = r"C:\Users\orsan\groupb_capstone_cs4273\test-audio\2025_00016232_Chest Pain_Block_cleaned.wav"
    output_wav = r"C:\Users\orsan\groupb_capstone_cs4273\test-audio\2025_00016232_Chest Pain_Block_noisereduce.wav"
    run_noisereduce(input_wav, output_wav)
