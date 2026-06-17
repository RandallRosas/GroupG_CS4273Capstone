import json
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from flask import Blueprint, jsonify, request, send_from_directory
from api.services.ai_grader import calculate_final_grade
from api.services.nature_codes import get_nature_codes_master, load_nature_code_questions
from pathvalidate import sanitize_filepath, sanitize_filename

files_bp = Blueprint('files', __name__)

# Root of output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

GRADE_KEY = {
    "1": "Asked Correctly",
    "2": "Not Asked",
    "3": "Asked Incorrectly",
    "4": "Not As Scripted",
    "5": "Not Applicable",
    "6": "Obvious",
    "RC": "Recorded Correctly",
}


def decode_filename_parts(filename):
    """
    Decode a filename from the route and split it into its base name, extension,
    and underscore-delimited parts.
    """
    decoded_filename = unquote(filename)
    name_part, ext = decoded_filename.rsplit('.', 1)
    parts = name_part.split('_')
    return decoded_filename, name_part, ext, parts


def extract_nature_code_id(nature_code_value):
    """
    Normalize a stored nature code value to its string ID.
    Supports both modern object form {"id": "...", "name": "..."} and plain string IDs.
    """
    if isinstance(nature_code_value, dict):
        nature_code_id = nature_code_value.get("id")
        return str(nature_code_id) if nature_code_id is not None else ""

    if nature_code_value is None:
        return ""

    return str(nature_code_value)


def get_nature_code_name(nature_code_id):
    nature_codes_master = get_nature_codes_master()
    return nature_codes_master.get(str(nature_code_id), {}).get("nature_code_name", "")


def build_record_paths(agent_name, date, time, nature_code_name, filename_suffixes):
    """
    Build destination directory and filenames using the same logic as the upload endpoint.
    """
    base_dir = Path(OUTPUT_DIR)
    safe_agent = sanitize_filename(agent_name, replacement_text="-")
    safe_folder = sanitize_filename(f"{date}_{time}_{nature_code_name}", replacement_text="-")
    dest_dir = Path(
        sanitize_filepath(base_dir / safe_agent / safe_folder, replacement_text="-")
    )

    base_name = sanitize_filename(
        f"{agent_name}_{date}_{time}_{nature_code_name}",
        replacement_text="-"
    )

    return {
        key: dest_dir / sanitize_filename(
            f"{base_name}_{suffix}{extension}",
            replacement_text="-"
        )
        for key, (suffix, extension) in filename_suffixes.items()
    }


def rename_record_files(agent_name, date, time, old_record_dir, nature_code_name):
    """
    Move the whole record into its new nature-code-based folder/file names.
    """
    file_mapping = {}
    for existing_file in old_record_dir.iterdir():
        if not existing_file.is_file():
            continue

        _, file_stem, file_ext, parts = decode_filename_parts(existing_file.name)
        if len(parts) < 5:
            continue

        suffix = "_".join(parts[4:])
        file_mapping[existing_file.name] = (suffix, f".{file_ext}")

    if not file_mapping:
        return None

    new_paths = build_record_paths(agent_name, date, time, nature_code_name, file_mapping)
    new_record_dir = next(iter(new_paths.values())).parent
    new_record_dir.mkdir(parents=True, exist_ok=True)

    renamed_files = {}
    for old_name, new_path in new_paths.items():
        old_path = old_record_dir / old_name
        shutil.move(str(old_path), str(new_path))
        renamed_files[old_name] = new_path.name

    if old_record_dir.exists() and old_record_dir != new_record_dir:
        try:
            old_record_dir.rmdir()
        except OSError:
            pass

    return {
        "record_dir": str(new_record_dir),
        "renamed_files": renamed_files,
    }

def serve_audio(relative_path):
    """
    Serve audio files from the output directory.
    """
    #print(f"Serving audio file: {relative_path}")

    output_dir = OUTPUT_DIR.resolve()
    file_path = output_dir / relative_path

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    file_dir = file_path.parent
    file_name = file_path.name

    return send_from_directory(str(file_dir), file_name)

@files_bp.route('/files/<string:filename>', methods=['GET'])
def get_file(filename):
    """
    Returns or serves a given file in the system.

    Expects file to be named like `{agent}_{date}_{time}_{nature}_{desc}.{ext}`

    Example: `lchey_032626_093424_Case Entry_audio.wav`
    """
    try:
        base_dir = Path(OUTPUT_DIR)

        # Split into parts
        filename, name_part, ext, parts = decode_filename_parts(filename)

        #print(f"Serving file:\nDecoded: {filename}\nParts: {parts}")

        if len(parts) < 4:
            return jsonify({'error': 'Invalid filename format'}), 400

        # Get info from parts
        agent = parts[0]
        date = parts[1]
        time = parts[2]
        nature = parts[3]

        # Check that file exists
        record_dir = base_dir / agent / f"{date}_{time}_{nature}"
        file_path = record_dir / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        ext = ext.lower()

        # If wav, serve audio
        if ext == "wav":
            relative_path = f"{agent}/{date}_{time}_{nature}/{filename}"
            return serve_audio(relative_path)

        # If json, jsonify and return
        if ext == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))

        # If txt, return plaintext
        if ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read(), 200, {"Content-Type": "text/plain"}

        return jsonify({'error': 'Unsupported file type'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@files_bp.route('/files/<string:filename>', methods=['PUT'])
def put_file(filename):
    """
    Updates a given file in the system. 

    Expects file to be named like `{agent}_{date}_{time}_{nature}_{desc}.{ext}`

    Example: `lchey_032626_093424_Case Entry_audio.wav`
    """
    try:
        base_dir = Path(OUTPUT_DIR)

        # Split into parts
        filename, name_part, ext, parts = decode_filename_parts(filename)

        #print(f"Updating file:\nDecoded: {filename}\nParts: {parts}")

        if len(parts) < 5:
            return jsonify({'error': 'Invalid filename format'}), 400

        # Get info from parts
        agent = parts[0]
        date = parts[1]
        time = parts[2]
        nature = parts[3]
        description = "_".join(parts[4:]).lower()

        # Check that file exists
        record_dir = base_dir / agent / f"{date}_{time}_{nature}"
        file_path = record_dir / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        ext = ext.lower()

        # If not grades or transcript, don't update
        if ext != "json" or description not in {"grades", "transcript"}:
            return jsonify({'error': 'Unsupported file type'}), 400

        if not request.is_json:
            return jsonify({'error': 'No replacement file or JSON body provided'}), 400

        replacement_payload = request.get_json(silent=True)
        if replacement_payload is None:
            return jsonify({'error': 'Invalid JSON body'}), 400
        
        if description == "transcript" and "segments" not in replacement_payload:
            return jsonify({"error": "Transcript must include 'segments'"}), 400

        if description == "grades" and not any(
            key in replacement_payload for key in ("grades", "per_question")
        ):
            return jsonify({"error": "Grades file must include 'grades' or 'per_question'"}), 400

        if description == "grades":
            print(f"Original grade: {replacement_payload.get('grade_percentage')}")

            grades_payload = replacement_payload.get("grades") or replacement_payload.get("per_question") or {}
            nature_code = extract_nature_code_id(replacement_payload.get("detected_nature_code"))

            if not nature_code:
                return jsonify({"error": "Grades file must include 'detected_nature_code'"}), 400

            questions_list = load_nature_code_questions(nature_code)
            if not questions_list:
                return jsonify({"error": f"Could not load questions for nature code '{nature_code}'"}), 400

            questions_dict = {
                question["Question_ID"]: question
                for question in questions_list
                if question.get("Question_ID")
            }

            normalized_grades_payload = {}
            for qid, grade_data in grades_payload.items():
                grade_data = grade_data or {}
                code = str(grade_data.get("code", "2"))
                if code not in GRADE_KEY:
                    code = "2"

                normalized_grades_payload[qid] = {
                    **grade_data,
                    "code": code,
                    "status": grade_data.get("status") or GRADE_KEY[code],
                    "reasoning": grade_data.get("reasoning", ""),
                }

            grade_codes = {
                qid: grade_data["code"]
                for qid, grade_data in normalized_grades_payload.items()
            }

            percentage = round(calculate_final_grade(grade_codes, questions_dict), 1)
            print(f"New grade: {percentage}")
            total_questions = len(normalized_grades_payload)
            case_entry_count = sum(1 for qid in normalized_grades_payload if qid.startswith("CE_"))
            nature_code_count = sum(1 for qid in normalized_grades_payload if qid.startswith("NC_"))
            questions_asked_correctly = sum(
                1 for grade_data in normalized_grades_payload.values()
                if grade_data.get("code") in {"1", "6"}
            )
            questions_missed = total_questions - questions_asked_correctly

            replacement_payload["detected_nature_code"] = nature_code
            replacement_payload["grades"] = normalized_grades_payload
            if "per_question" in replacement_payload:
                replacement_payload["per_question"] = normalized_grades_payload
            replacement_payload["grade_percentage"] = percentage
            replacement_payload["total_questions"] = total_questions
            replacement_payload["case_entry_questions"] = case_entry_count
            replacement_payload["nature_code_questions"] = nature_code_count
            replacement_payload["questions_asked_correctly"] = questions_asked_correctly
            replacement_payload["questions_missed"] = questions_missed
            replacement_payload["timestamp"] = datetime.now().isoformat() + "Z"

            new_nature_code_name = get_nature_code_name(nature_code)
            if new_nature_code_name and new_nature_code_name != nature:
                replacement_payload["nature_code_reasoning"] = (
                    "This Nature Code was manually selected before regrading.."
                )
            rename_result = None
            if new_nature_code_name and new_nature_code_name != nature:
                rename_result = rename_record_files(
                    agent_name=agent,
                    date=date,
                    time=time,
                    old_record_dir=record_dir,
                    nature_code_name=new_nature_code_name,
                )

                if rename_result and filename in rename_result["renamed_files"]:
                    filename = rename_result["renamed_files"][filename]
                    file_path = Path(rename_result["record_dir"]) / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(replacement_payload, f, indent=2, ensure_ascii=False)

        response_payload = {
            'message': 'File updated successfully',
            'filename': filename,
            'new_grade': replacement_payload.get('grade_percentage'),
        }

        if description == "grades" and 'rename_result' in locals() and rename_result:
            response_payload['record_dir'] = rename_result["record_dir"]
            response_payload['renamed_files'] = rename_result["renamed_files"]

        return jsonify(response_payload), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@files_bp.route('/files/nature-codes', methods=['GET'])
def get_nature_codes():
    try:
        nature_codes_master = get_nature_codes_master()

        # Return array of nature code IDs and names in a dict
        nature_codes = [
            {
                "id": nature_code_id,
                "name": nature_code_data.get("nature_code_name", ""),
            }
            for nature_code_id, nature_code_data in nature_codes_master.items()
            if nature_code_id != "0"
        ]

        return jsonify(nature_codes), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@files_bp.route('/files/nature-codes/<nature_code_id>', methods=['GET'])
def get_nature_code_questions(nature_code_id):
    try:
        nature_codes_master = get_nature_codes_master()
        nature_code_id = str(nature_code_id)

        if nature_code_id not in nature_codes_master:
            return jsonify({'error': 'Nature code not found'}), 404

        # Return a grade scaffold that can be swapped into an existing graded payload
        questions = load_nature_code_questions(nature_code_id, include_case_entry=True)
        grades = {
            question_id: {
                "code": "5",
                "label": question.get("Question_Text", ""),
                "status": "",
                "reasoning": "",
            }
            for question in questions
            if (question_id := question.get("Question_ID"))
        }

        return jsonify({
            "detected_nature_code": nature_code_id,
            "nature_code_name": nature_codes_master[nature_code_id].get("nature_code_name", ""),
            "grades": grades,
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

