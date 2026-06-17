import json
import shutil
import uuid
from pathlib import Path
from urllib.parse import unquote

from flask import Blueprint, jsonify
from pathvalidate import sanitize_filepath, sanitize_filename

from api.services.ai_grader import grade_transcript_file
from api.services.nature_codes import get_nature_codes_master

regrade_bp = Blueprint("regrade", __name__)

# Root of output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def extract_nature_code_id(nature_code_value):
    """
    Normalize a stored nature code value to its string ID.
    Supports both {"id": "...", "name": "..."} and plain string IDs.
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


def decode_filename_parts(filename):
    """
    Decode a filename from the route and split it into its base name, extension,
    and underscore-delimited parts.
    """
    decoded_filename = unquote(filename)
    name_part, ext = decoded_filename.rsplit(".", 1)
    parts = name_part.split("_")
    return decoded_filename, name_part, ext, parts


def decode_record_identifier(agent, record_identifier):
    """
    Record identifier format: {date}_{time}_{nature}
    where nature may contain additional underscores/spaces after URL decoding.
    """
    decoded_agent = unquote(agent)
    decoded_identifier = unquote(record_identifier)
    parts = decoded_identifier.split("_", 2)

    if len(parts) < 3:
        raise ValueError("Invalid record identifier format")

    date, time, nature = parts
    return decoded_agent, decoded_identifier, date, time, nature


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

        _, _, file_ext, parts = decode_filename_parts(existing_file.name)
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


@regrade_bp.route("/regrade/<string:agent>/<string:record_identifier>", methods=["POST"])
def regrade_record(agent, record_identifier):
    """
    Re-run grading for an existing record using its current transcript and stored nature code.

    URL format: /regrade/{agent}/{date}_{time}_{nature}
    """
    temp_dir = None

    try:
        agent, _, date, time, nature = decode_record_identifier(agent, record_identifier)

        record_dir = OUTPUT_DIR / agent / f"{date}_{time}_{nature}"
        if not record_dir.exists() or not record_dir.is_dir():
            return jsonify({"error": "Record not found"}), 404

        transcript_path = None
        grade_file_path = None
        for file in record_dir.iterdir():
            if not file.is_file():
                continue

            if file.name.endswith("transcript.json"):
                transcript_path = file
            elif file.name.endswith("grades.json"):
                grade_file_path = file

        if transcript_path is None or grade_file_path is None:
            return jsonify({
                "error": "Record must contain both transcript.json and grades.json to regrade"
            }), 400

        with open(grade_file_path, "r", encoding="utf-8") as f:
            existing_grades = json.load(f)

        nature_code_id = extract_nature_code_id(existing_grades.get("detected_nature_code"))
        if not nature_code_id:
            return jsonify({"error": "Existing grades.json is missing detected_nature_code"}), 400

        nature_code_name = get_nature_code_name(nature_code_id)
        if not nature_code_name:
            return jsonify({"error": f"Unknown nature code '{nature_code_id}' in grades.json"}), 400

        temp_dir = OUTPUT_DIR / "_tmp" / uuid.uuid4().hex
        temp_dir.mkdir(parents=True, exist_ok=True)

        nature_code_changed = (nature_code_name != nature)
        nature_code_reasoning = existing_grades.get("nature_code_reasoning", "")
        if nature_code_changed:
            nature_code_reasoning = (
                "This Nature Code was manually selected before regrading."
            )

        response, _ = grade_transcript_file(
            nature_code_id=nature_code_id,
            transcript_path=transcript_path,
            output_path=temp_dir,
            nature_code_reasoning=nature_code_reasoning,
        )

        final_record_dir = record_dir
        final_grade_path = grade_file_path
        rename_result = None

        if nature_code_changed:
            rename_result = rename_record_files(
                agent_name=agent,
                date=date,
                time=time,
                old_record_dir=record_dir,
                nature_code_name=nature_code_name,
            )

            if not rename_result or grade_file_path.name not in rename_result["renamed_files"]:
                return jsonify({"error": "Failed to rename record files during regrade"}), 500

            final_record_dir = Path(rename_result["record_dir"])
            final_grade_path = final_record_dir / rename_result["renamed_files"][grade_file_path.name]

        with open(final_grade_path, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        result = {
            "outputDestination": str(final_record_dir),
            "dispatcherName": agent,
            "grades": response,
        }

        if rename_result:
            result["renamed_files"] = rename_result["renamed_files"]

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
