"""AI-based transcript grading helpers with a single file-based entrypoint."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from api.services.prompts import get_grading_system_prompt, get_single_question_prompt
from api.services.ollama_handler import chat_ollama
from api.services.nature_codes import load_nature_code_questions, get_nature_codes_master
from api.services.text_handler import json_to_text

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
PER_QUESTION_MAX_RETRIES = 3
FALLBACK_REASONING = "No valid bracketed grade was returned after the maximum retry attempts."

GRADE_KEY = {
    "1": "Asked Correctly",
    "2": "Not Asked",
    "3": "Asked Incorrectly",
    "4": "Not As Scripted",
    "5": "Not Applicable",
    "6": "Obvious",
    "RC": "Recorded Correctly",
}


def _questions_list_to_dict(questions: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {q["Question_ID"]: q for q in questions if q.get("Question_ID")}


def _extract_grade_and_reasoning(response: str) -> Tuple[str | None, str]:
    if not response:
        return None, ""

    cleaned = response.strip()
    match = re.search(r"\[([1-6])\]", cleaned)
    if not match:
        return None, cleaned

    grade_code = match.group(1)
    reasoning = re.sub(r"\[[1-6]\]", "", cleaned, count=1).strip()
    return grade_code, reasoning


def calculate_final_grade(grades: Dict[str, str], questions_dict: Dict[str, Dict[str, Any]]) -> float:
    total_points = 0
    earned_points = 0.0

    for qid, grade in grades.items():
        if qid not in questions_dict or grade in {"5", "RC"}:
            continue

        total_points += 1
        if grade in {"1", "6"}:
            earned_points += 1.0
        elif grade == "4":
            earned_points += 0.5

    if total_points == 0:
        return 0.0

    return (earned_points / total_points) * 100


def ai_grade_per_question(
    transcript_text: str,
    questions_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, str]]:
    """Grade a transcript one question at a time using a persistent chat."""
    system_prompt = get_grading_system_prompt(transcript_text, questions_dict)

    print(f"[SYSTEM]\n{system_prompt}\n")

    messages = [{"role": "system", "content": system_prompt}]
    grade_details: Dict[str, Dict[str, str]] = {}

    for question_id, question in questions_dict.items():
        # Set skipped questions to N/A (5)
        if question.get("Skip_AI_Grading", False):
            grade_details[question_id] = {
                "code": "5",
                "reasoning": "This question was set to be skipped for AI grading.",
            }
            continue

        user_message = get_single_question_prompt(question)
        print(f"==============================\n[USER]\n{user_message}\n")
        messages.append({"role": "user", "content": user_message})

        grade_code = None
        reasoning = ""

        for attempt in range(PER_QUESTION_MAX_RETRIES):
            response = chat_ollama(messages)
            print(f"[OLLAMA]\n{response}\n")

            grade_code, reasoning = _extract_grade_and_reasoning(response)

            if grade_code:
                assistant_reply = response.strip()
                messages.append({"role": "assistant", "content": assistant_reply})
                grade_details[question_id] = {
                    "code": grade_code,
                    "reasoning": reasoning,
                }
                break

            invalid_reply = (response or "").strip()
            if invalid_reply:
                messages.append({"role": "assistant", "content": invalid_reply})

            if attempt < PER_QUESTION_MAX_RETRIES - 1:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your last reply was invalid because it did not include a grade in square brackets "
                            "at the beginning. Reply again using this exact structure: [X] reasoning text with "
                            "direct quote(s). Also remember that transcript labels may be incorrect, including "
                            "cases where the dispatcher appears to talk to themself or does not wait for a proper response."
                        ),
                    }
                )
            print("=== RETRYING ===")

        if not grade_code:
            fallback_reply = "[5] " + FALLBACK_REASONING
            messages.append({"role": "assistant", "content": fallback_reply})
            grade_details[question_id] = {
                "code": "5",
                "reasoning": FALLBACK_REASONING,
            }

    return grade_details


def format_grades(
    ai_grades: Dict[str, Dict[str, str]],
    questions_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, str]]:
    """Format AI grade details for API/storage responses."""
    formatted = {}

    for q_id, q_data in questions_dict.items():
        code = ai_grades.get(q_id, {}).get("code", "2")
        formatted[q_id] = {
            "code": code,
            "label": q_data.get("Question_Text", ""),
            "status": GRADE_KEY.get(code, "Unknown"),
            "reasoning": ai_grades.get(q_id, {}).get("reasoning", ""),
        }

    return formatted


def calculate_percentage(grades: Dict[str, Any], questions_dict: Dict[str, Dict[str, Any]]) -> float:
    if not grades or not questions_dict:
        return 0.0

    grade_codes = {q_id: grade_data.get("code", "2") for q_id, grade_data in grades.items()}
    return round(calculate_final_grade(grade_codes, questions_dict), 1)


def _get_nature_code_name(nature_code_id: str) -> str:
    nature_codes_master = get_nature_codes_master()
    return nature_codes_master.get(str(nature_code_id), {}).get("nature_code_name", "Unknown")


def grade_transcript_file(
    nature_code_id: str,
    transcript_path: Path,
    output_path: Path,
    nature_code_reasoning: str = "",
) -> Tuple[Dict[str, Any], Path]:
    """Grade a transcript JSON file and write grades.json to output_path."""
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    if not isinstance(transcript_data, dict) or "segments" not in transcript_data:
        raise ValueError("Invalid transcript format")

    transcript_text = json_to_text(json_data=transcript_data)

    questions_list = load_nature_code_questions(nature_code_id, include_case_entry=True)
    questions_dict = _questions_list_to_dict(questions_list)

    print("Running AI grading...", flush=True)
    ai_grades = ai_grade_per_question(transcript_text, questions_dict)

    if not ai_grades:
        raise RuntimeError("AI grading returned empty results")

    grades = format_grades(ai_grades, questions_dict)
    print(f"Grade transcript completed. Got {len(grades)} grades.", flush=True)

    percentage = calculate_percentage(grades, questions_dict)
    total_questions = len(grades)
    case_entry_count = sum(1 for q_id in grades if q_id.startswith("CE_"))
    nature_code_count = sum(1 for q_id in grades if q_id.startswith("NC_"))
    questions_asked_correctly = sum(1 for grade in grades.values() if grade.get("code") in {"1", "6"})
    questions_missed = total_questions - questions_asked_correctly

    nature_code_name = _get_nature_code_name(nature_code_id)

    response = {
        "grader_type": "ai",
        "grade_percentage": percentage,
        "detected_nature_code": {
            "id": str(nature_code_id),
            "name": nature_code_name,
        },
        "nature_code_reasoning": nature_code_reasoning,
        "total_questions": total_questions,
        "case_entry_questions": case_entry_count,
        "nature_code_questions": nature_code_count,
        "questions_asked_correctly": questions_asked_correctly,
        "questions_missed": questions_missed,
        "timestamp": datetime.now().isoformat() + "Z",
        "grades": grades,
        "metadata": {
            "language": transcript_data.get("language", "unknown"),
            "segment_count": len(transcript_data.get("segments", [])),
            "grader_version": "2.0.0",
            "model": OLLAMA_MODEL,
            "questions_source": f"EMSQA.csv (Case Entry + {nature_code_name})",
        },
    }

    grades_path = output_path / "grades.json"
    with open(grades_path, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2)

    return response, grades_path
