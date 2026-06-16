# Jaiden Sizemore
# CS4273 Group G
# Last Updated 03/28/2026: Consolidated transcript and CDR text helpers

# Usage: python text_handler.py <filepath.json>

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any


def json_to_text(file_path = None, json_data = None):
    """
    Parse a JSON transcription file into plain text lines.

    Output format:
    [Timestamp][Speaker]: Text
    """
    try:
        if json_data is not None:
            data = json_data
        else:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return ""
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' is not valid JSON.")
        return ""
    except Exception as exc:
        print(f"Error reading file: {exc}")
        return ""

    text_output = ""

    if "segments" in data and isinstance(data["segments"], list):
        for segment in data["segments"]:
            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", 0.0)
            speaker = segment.get("speaker", "UNKNOWN")
            transcript_text = segment.get("text", "").strip()

            start_minutes = int(start_time // 60)
            start_seconds = start_time % 60
            end_minutes = int(end_time // 60)
            end_seconds = end_time % 60

            start_timestamp = f"{start_minutes:02d}:{start_seconds:04.1f}"
            end_timestamp = f"{end_minutes:02d}:{end_seconds:04.1f}"
            text_output += f"[{start_timestamp}-{end_timestamp}] {speaker}: {transcript_text}\n"
    else:
        print("Error: JSON file does not contain 'segments' array or has unexpected structure.")
        return ""

    return text_output


def extract_info_from_cdr(cdr_path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract date (YYYYMMDD), time (HHMMSS), and dispatcher name from a CDR text file.
    """
    cdr_content = cdr_path.read_text(encoding="utf-8", errors="ignore")

    start_match = re.search(
        r"\bStart:\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",
        cdr_content,
    )
    if not start_match:
        return None, None, None

    year, month, day, hour, minute, second = start_match.groups()
    date_str = f"{year}{month}{day}"
    time_str = f"{hour}{minute}{second}"

    agent_match = re.search(r"\bAGENT_NAME:\s*([^,\s]+)", cdr_content)
    if not agent_match:
        agent_match = re.search(r"\bAGENT:\s*([^,\s]+)", cdr_content)

    agent_name = agent_match.group(1).strip() if agent_match else None
    if not agent_name:
        return None, None, None

    return date_str, time_str, agent_name

IGNORE_LIST = [
    "CE_1b",
    "CE_2a",
    "CE_FT1",
]


def _format_parent_question_id(question_id: str, parent_question_id: str) -> str:
    if parent_question_id.startswith(("CE_", "NC_")):
        return parent_question_id

    prefix = "CE" if question_id.startswith("CE_") else "NC"
    return f"{prefix}_{parent_question_id}"


def format_questions_for_prompt(questions_dict):
    lines = []

    for qid, q in questions_dict.items():
        parts = [f"{qid}: {q['text']}"]

        if (qid in IGNORE_LIST):
            parts.append("[PROTOCOL QUESTION: ALWAYS GRADE AS N/A (5)]")

        if q["parent"]:
            parts.append(f"[Follows: {_format_parent_question_id(qid, q['parent'])}]")

        if q["alternatives"]:
            parts.append(f"[Alt: {q['alternatives']}]")

        if q["condition"]:
            parts.append(f"[Condition: {q['condition']}]")

        if q["condition_type"]:
            parts.append(f"[Condition Type: {q['condition_type']}]")

        if q["age_min_f"] or q["age_min_m"]:
            parts.append(f"[Age: F>{q['age_min_f']} M>{q['age_min_m']}]")

        if q["clarification_allowed"]:
            parts.append(f"[Clarification Allowed: {q['clarification_allowed']}]")

        if q["macros"]:
            parts.append(f"[Macro: {q['macros']}]")

        if q["echo"]["level"] or q["echo"]["number"] or q["echo"]["letter"] or q["echo"]["response"]:
            parts.append(
                f"[ECHO: level={q['echo']['level']} number={q['echo']['number']} letter={q['echo']['letter']} response={q['echo']['response']}]"
            )

        if q["scenario"]:
            parts.append(f"[Scenario: {q['scenario']}]")

        lines.append(" ".join(parts))

    return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print("Usage: python text_handler.py <filepath.json>")
        print("Example: python text_handler.py transcriptions/example.json")
        sys.exit(1)

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)

    return json_to_text(file_path=filename)


if __name__ == "__main__":
    result = main()
    if result:
        print(result)
