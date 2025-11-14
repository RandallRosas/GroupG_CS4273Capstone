# AI-based transcript grader using Ollama
# CS4273 Group G
# Last Updated 11/2/2025

# Requires installation of ollama from ollama.ai
# Ensure ollama is on your PATH
# Download the model: ollama pull llama3.1:8b
# Usage: python AIGrader.py <path\transcript.json>

import sys
import pandas as pd
import os
from JSONTranscriptionParser import json_to_text
from detect_naturecode import run_detection
import ollama

# Configure Ollama client to use environment variable if set
# The ollama Python client automatically uses OLLAMA_HOST env var
# Defaults to http://localhost:11434 if not set
ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Function for gathering nature codes and cleaning up file structure afterwards

# Input: path to a transcript, transcript text
# Output: nature codes
def detect_nature_codes_in_memory(transcript_path, transcript_text):
    temp_path = run_detection(transcript_path, transcript_text)
    with open(temp_path, 'r') as f:
        nature_codes = f.read()
    os.remove(temp_path)
    return nature_codes

# Function for extracting nature codes and sorting by confidence

# Input: nature codes text
# Output: array of nature code from most to least confident
def extract_all_nature_codes(text):
    nature_codes = []
    lines = text.strip().split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('- '):
            nature_code = line.strip()[2:].split(' (')[0]
            
            if i + 2 < len(lines):
                confidence_line = lines[i + 2].strip()
                if confidence_line.startswith('Confidence:'):
                    try:
                        confidence = float(confidence_line.split(': ')[1])
                        nature_codes.append((nature_code, confidence))
                    except (IndexError, ValueError):
                        continue
    
    # Sort by confidence (highest first)
    nature_codes.sort(key=lambda x: x[1], reverse=True)
    return nature_codes

# Function for loading specific nature code questions

# Input: desired nature code
# Output: dict of questions from given nature code
def load_nature_code_questions(nature_code):
    try:
        df = pd.read_csv("data/EMSQA.csv")
        nature_questions = df[df['NatureCode'] == nature_code]
        
        questions_dict = {}
        for _, row in nature_questions.iterrows():
            qid = str(row['Question_ID'])
            question_text = row['Question_Text']
            if pd.notna(question_text):
                # Add prefix based on nature code for easy separation in output
                if nature_code == "Case Entry":
                    prefixed_qid = f"CE_{qid}"
                else:
                    prefixed_qid = f"NC_{qid}"
                questions_dict[prefixed_qid] = question_text
            
        return questions_dict
    
    # Error handling
    except FileNotFoundError:
        print(f"Error: EMSQA.csv file not found in data/ directory")
        return {}
    except Exception as e:
        print(f"Error loading questions for Nature Code {nature_code}: {e}")
        return {}

# Function for calculating final grade

# Input: grades from AI and list of questions
# Output: final percentage grade
def calculate_final_grade(grades, questions_dict):
    """
    Calculate final percentage grade based on the grading scheme.
    
    Grading Key:
    1 = Asked Correctly (100%)
    2 = Not Asked (0%)
    3 = Asked Incorrectly (0%)
    4 = Not As Scripted (50% - partial credit)
    5 = N/A (exclude from calculation)
    6 = Obvious (100% - full credit)
    RC = Recorded Correctly (exclude from calculation)
    """
    
    total_points = 0
    earned_points = 0
    graded_questions = 0
    
    for qid, grade in grades.items():
        if qid not in questions_dict:
            continue
            
        # Skip questions that don't affect the numerical grade
        if grade == "5" or grade == "RC":
            continue
            
        graded_questions += 1
        
        if grade == "1":  # Asked Correctly
            earned_points += 1
            total_points += 1
        elif grade == "2":  # Not Asked
            total_points += 1
            # earned_points += 0 (implicit)
        elif grade == "3":  # Asked Incorrectly
            total_points += 1
            # earned_points += 0 (implicit)
        elif grade == "4":  # Not As Scripted
            earned_points += 0.5  # Partial credit
            total_points += 1
        elif grade == "6":  # Obvious
            earned_points += 1
            total_points += 1
        else:
            # Unknown grade code - treat as not asked
            total_points += 1
            # earned_points += 0 (implicit)
    
    if total_points == 0:
        return 0.0
    
    final_percentage = (earned_points / total_points) * 100

    return final_percentage

# Function for grading a transcript using ollama's AI

# Input: Plain text transcription for grading and list of questions to be asked
# Output AI's grade for the given transcription based on given questions
def ai_grade_transcript(transcript_text, questions_dict, nature_code):
    # Prompt for the AI
    # NOTE: asking for a JSON submission is more reliable than plain text because the model is familiar with the format
    # Therefore, we are more likely to receive coherent grades in JSON format rather than a paragraph
    prompt = f"""
    You are a 911 call quality assurance analyst. Analyze this transcript and grade it based on the questions from the given nature code below.
    
    NATURE_CODE:
    {nature_code}

    TRANSCRIPT:
    {transcript_text}
    
    GRADING QUESTIONS (use codes: 1=Asked Correctly, 2=Not Asked, 3=Asked Incorrectly, 4=Not As Scripted, 5=N/A, 6=Obvious, RC=Recorded Correctly):
    {chr(10).join([f"{qid}: {question}" for qid, question in questions_dict.items()])}
    
    Return ONLY a JSON object with this format, this is just an example format, add as many entries as necessary for grading the given questions:
    {{
        "1": "1",
        "1a": "1", 
        "1b": "5",
        "2": "4",
        "2a": "2"
    }}

    Note that the left hand side is for the question ID and the right hand side is for the grade.  Add as many entries as needed to satisfy the required grading.

    Important grading guidelines:
    - Use code "1" only if the question was asked exactly as scripted with correct wording
    - Use code "2" if the question was not asked at all
    - Use code "3" if the question was asked but with incorrect or misleading information that could impact patient care
    - Use code "4" if the question was asked with different wording but still captured the essential information correctly
    - Use code "5" only for questions that are clearly not applicable to this specific call scenario
    - Use code "6" when the information was provided voluntarily by the caller without needing to ask the question
    - Use code "RC" for administrative questions that were recorded correctly in the system
    - Be strict in your assessment as repeating the exact question is important for most cases with relatively few exceptions
    - For code "6" (Obvious), ensure the information was clearly stated by the caller without prompting (Compare exact question wording to call before determining if
      obvious is an appropriate grade, grading is meant to be strict so obvious should only be used when the question has been BEYOND A DOUBT obviously answered)
    """
    
    try:
        response = ollama.generate(model='llama3.1:8b', prompt=prompt)
        # Extract JSON from response
        import json
        import re
        
        # Find JSON in the response
        json_match = re.search(r'\{.*\}', response['response'], re.DOTALL)
        if json_match:
            grades = json.loads(json_match.group())
            return grades
        else:
            # If unable to access grades in json, send error message
            print("Could not parse AI response as JSON")
            return {}
            
    except Exception as e:
        print(f"AI grading failed: {e}")
        return {}

def main():
    # Key for grading the transcription
    KEY = {
        "1": "Asked Correctly",
        "2": "Not Asked",
        "3": "Asked Incorrectly",
        "4": "Not As Scripted", 
        "5": "N/A",
        "6": "Obvious",
        "RC": "Recorded Correctly"
    }
    
    # Check if file was provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python AIGrader.py <transcript.json>")
        sys.exit(1)
    
    # Get transcript as text
    transcript = json_to_text(sys.argv[1])
    if not transcript:
        print(f"Error: Could not load transcript")
        sys.exit(1)

    # Get nature codes
    nature_codes_text = detect_nature_codes_in_memory(sys.argv[1], transcript)
    if not nature_codes_text:
        print(f"Error: Could not determine nature codes")
        sys.exit(1)

    nature_codes = extract_all_nature_codes(nature_codes_text)

    # Grade based on nature code with highest confidence
    primary_nature_code = nature_codes[0][0]

    # Load questions for case entry and primary nature code
    case_entry_questions = load_nature_code_questions("Case Entry")
    nature_code_questions = load_nature_code_questions(primary_nature_code)

    # Combine into one dict of questions
    questions = {**case_entry_questions, **nature_code_questions}
    if not questions:
        print(f"Error: Could not determine questions")
        sys.exit(1)
    
    # Get grades from AI
    grades = ai_grade_transcript(transcript, questions, primary_nature_code)

    final_percentage = calculate_final_grade(grades, questions)
    
    # Print results
    print("=== AI Grading Results ===")
    print("--- Case Entry Questions ---")
    for qid, question in case_entry_questions.items():
        code = grades.get(qid, "2")
        meaning = KEY.get(code, "Unknown")
        display_qid = qid.replace("CE_", "")
        print(f"{display_qid}: {code} ({meaning}) - {question}")
    
    print(f"\n--- {primary_nature_code} Questions ---")
    for qid, question in nature_code_questions.items():
        code = grades.get(qid, "2")
        meaning = KEY.get(code, "Unknown")
        display_qid = qid.replace("NC_", "")
        print(f"{display_qid}: {code} ({meaning}) - {question}")

    print(f"\n=== Final Grade ===")
    print(f"Score: {final_percentage:.1f}%")

    # Return final percentage for frontend display
    return final_percentage

# Driver
if __name__ == "__main__":
    main()