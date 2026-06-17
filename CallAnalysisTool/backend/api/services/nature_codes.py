# Standard library
import json
from pathlib import Path
import re

# Local modules
from api.services.ollama_handler import chat_ollama

EMSQA_PATH = Path("data") / "EMSQA.csv"
NATURE_CODES_MASTER_PATH = Path("data") / "nature_codes_master.json"
NATURE_CODE_MAX_RETRIES = 5
FALLBACK_NATURE_CODE_ID = "0"

def get_nature_codes_master():
    # Load nature_codes_master.json
    with open(NATURE_CODES_MASTER_PATH, "r", encoding="utf-8") as f:
        nature_codes_master = json.load(f)
    
    return nature_codes_master

def load_nature_code_questions(nature_code_id, include_case_entry=True):
    nature_codes_master = get_nature_codes_master()

    nature_code_id = str(nature_code_id)

    if nature_code_id not in nature_codes_master:
        raise ValueError(f"Nature code ID {nature_code_id} not found")

    questions = []

    # Add Case Entry (ID = 0) first if requested
    if include_case_entry:
        case_entry = nature_codes_master.get("0", {})
        case_questions = case_entry.get("grading", {}).get("questions", [])

        for q in case_questions:
            q_copy = q.copy()
            if q_copy.get("Question_ID"):
                q_copy["Question_ID"] = f"CE_{q_copy['Question_ID']}"
            questions.append(q_copy)

    # Add selected nature code questions
    if nature_code_id != "0":
        code_questions = nature_codes_master[nature_code_id].get("grading", {}).get("questions", [])

        for q in code_questions:
            q_copy = q.copy()
            if q_copy.get("Question_ID"):
                q_copy["Question_ID"] = f"NC_{q_copy['Question_ID']}"
            questions.append(q_copy)

    return questions


def _extract_nature_code_response(response, nature_codes_master):
    if not response:
        return None, None, ""

    cleaned = response.strip()
    match = re.search(r"\[(\d+)\]", cleaned)
    if not match:
        return None, None, cleaned

    nature_code_id = match.group(1)
    if nature_code_id not in nature_codes_master:
        return None, None, cleaned

    nature_code_name = nature_codes_master[nature_code_id].get("nature_code_name", "Unknown")
    reasoning = cleaned[match.end():].strip()
    return nature_code_id, nature_code_name, reasoning

def detect_nature_code(transcript_path):
    # Import here to avoid circular imports
    from api.services.prompts import get_nature_code_prompt

    # Get full prompt
    nature_codes_master = get_nature_codes_master()
    prompt = get_nature_code_prompt(transcript_path, nature_codes_master)
    print("Nature code prompt: ", prompt)

    messages = [{"role": "user", "content": prompt}]

    response = ""

    for attempt in range(NATURE_CODE_MAX_RETRIES):
        response = chat_ollama(messages)
        print(f"[OLLAMA]\n{response}\n")

        nature_code_id, nature_code_name, reasoning = _extract_nature_code_response(
            response, nature_codes_master
        )

        if nature_code_id:
            assistant_reply = (response or "").strip()
            messages.append({"role": "assistant", "content": assistant_reply})
            return nature_code_id, nature_code_name, reasoning

        invalid_reply = (response or "").strip()
        if invalid_reply:
            messages.append({"role": "assistant", "content": invalid_reply})

        if attempt < NATURE_CODE_MAX_RETRIES - 1:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your last reply was invalid because it did not begin with a valid Nature Code ID in "
                        "square brackets that exists in the provided list. Reply again using this exact structure: "
                        "[ID] followed by the required Reasoning and Possible Confusions sections. "
                        "Choose exactly one Nature Code from the provided options."
                    ),
                }
            )
        print("=== RETRYING NATURE CODE DETECTION ===")

    fallback_nature_code_name = nature_codes_master.get(
        FALLBACK_NATURE_CODE_ID, {}
    ).get("nature_code_name", "Case Entry")
    fallback_reasoning = (
        "Nature code detection failed after "
        f"{NATURE_CODE_MAX_RETRIES} attempts, so the system fell back to "
        f"[{FALLBACK_NATURE_CODE_ID}] {fallback_nature_code_name}. "
        f"Last response: {response}"
    )
    print(
        "Could not get a valid nature code response after "
        f"{NATURE_CODE_MAX_RETRIES} attempts. Falling back to "
        f"[{FALLBACK_NATURE_CODE_ID}] {fallback_nature_code_name}."
    )
    return FALLBACK_NATURE_CODE_ID, fallback_nature_code_name, fallback_reasoning
