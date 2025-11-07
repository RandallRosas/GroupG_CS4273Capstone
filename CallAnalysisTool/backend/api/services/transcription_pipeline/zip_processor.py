#!/usr/bin/env python3
"""
Zip file processor that unzips files and renames based on CDR text content.
"""

import sys
import tempfile
import zipfile
import re
import shutil
from pathlib import Path


def extract_info_from_cdr(cdr_content):
    """
    Extract date, time, and agent name from CDR text content.

    Args:
        cdr_content (str): The content of the CDR text file

    Returns:
        tuple: (date_str, time_str, agent_name) or (None, None, None) if not found
    """
    # Find Start field (format: Start: 2025-10-17 12:31:01)
    start_match = re.search(r'Start:\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', cdr_content)
    if not start_match:
        return None, None, None

    year, month, day, hour, minute, second = start_match.groups()

    # Format date as YYYYMMDD and time as HHMMSS
    date_str = f"{year}{month}{day}"
    time_str = f"{hour}{minute}{second}"

    # Find Agent_Name field
    agent_match = re.search(r'AGENT_NAME:\s*([^,\s]+)', cdr_content)
    if not agent_match:
        return None, None, None

    return date_str, time_str, agent_match.group(1).strip()


def find_cdr_file(extract_path):
    """
    Find the CDR text file in the extracted contents.

    Args:
        extract_path (Path): Path to the extracted zip contents

    Returns:
        Path: Path to the CDR file, or None if not found
    """
    cdr_files = list(extract_path.glob("*-CDR.txt"))
    return cdr_files[0] if cdr_files else None


def process_zip(zip_path, output_dir=None):
    """
    Process a zip file: unzip, extract info from CDR, and rename files/folders.

    Args:
        zip_path (str or Path): Path to the zip file
        output_dir (str or Path, optional): Directory to place the renamed folder.
                                          Defaults to the same directory as the zip file.

    Returns:
        str: The new folder name, or None if processing failed
    """
    zip_path = Path(zip_path).resolve()
    if not zip_path.exists():
        print(f"Error: Zip file '{zip_path}' does not exist.")
        return None

    # Determine output directory
    output_dir = Path(output_dir or zip_path.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary extraction directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_extract_dir = Path(temp_dir)

        try:
            # Extract the zip file
            print(f"Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            # Find the CDR file
            cdr_file = find_cdr_file(temp_extract_dir)
            if not cdr_file:
                print("Error: Could not find CDR text file in the zip archive.")
                return None

            # Read and parse CDR content
            print(f"Reading CDR file: {cdr_file}")
            cdr_content = cdr_file.read_text(encoding='utf-8', errors='ignore')

            date_str, time_str, agent_name = extract_info_from_cdr(cdr_content)
            if not all([date_str, time_str, agent_name]):
                print("Error: Could not extract required information from CDR file.")
                print(f"Date: {date_str}, Time: {time_str}, Agent: {agent_name}")
                return None

            # Create the new name
            new_name = f"{date_str}_{time_str}_{agent_name}"
            print(f"New name will be: {new_name}")

            # Create the final folder (remove if it already exists)
            final_folder_path = output_dir / new_name
            if final_folder_path.exists():
                shutil.rmtree(final_folder_path)
            final_folder_path.mkdir()

            # Move all files from temp directory to final folder
            for item in temp_extract_dir.iterdir():
                if item.is_file():
                    shutil.move(str(item), str(final_folder_path / item.name))

            # Find and rename the audio file (assuming it's a .wav file)
            wav_files = list(final_folder_path.glob("*.wav"))
            if wav_files:
                wav_file = wav_files[0]
                new_wav_path = final_folder_path / f"{new_name}.wav"
                print(f"Renaming audio file to: {new_name}.wav")
                wav_file.rename(new_wav_path)

            print(f"Successfully processed zip file. Final folder: {final_folder_path}")
            return new_name

        except Exception as e:
            print(f"Error processing zip file: {e}")
            return None

def extract_zip_file(zip_file):
    result = process_zip(zip_file)

    if result:
        print(f"\nSuccess! Processed as: {result}")
    else:
        print("\nFailed to process the zip file.")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python zip_processor.py <zip_file>")
        print("Example: python zip_processor.py 2025_Test.zip")
        sys.exit(1)

    zip_file = sys.argv[1]
    result = process_zip(zip_file)

    if result:
        print(f"\nSuccess! Processed as: {result}")
    else:
        print("\nFailed to process the zip file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
