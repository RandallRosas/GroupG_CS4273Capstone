# Standard library
import json
from datetime import datetime
from pathlib import Path

# Third-party
from flask import Blueprint, jsonify, request
from urllib.parse import unquote

dispatchers_bp = Blueprint('dispatchers', __name__)

# Root of output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

FILENAME_DATE_FORMAT = "%Y%m%d"


def parse_query_date(value, param_name):
    """
    Parse a query-string date in YYYYMMDD format.
    """
    if value is None:
        return None

    try:
        return datetime.strptime(value, FILENAME_DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(
            f'Invalid {param_name}. Expected YYYYMMDD format, for example "20260326".'
        ) from exc


def get_requested_date_range():
    """
    Read and validate optional inclusive date range query params.
    """
    start_date = parse_query_date(request.args.get("start_date"), "start_date")
    end_date = parse_query_date(request.args.get("end_date"), "end_date")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date.")

    return start_date, end_date


def extract_date_from_filename(filename):
    """
    Extract the YYYYMMDD date token from filenames like
    {agent}_{date}_{time}_{nature}_grades.json.
    """
    stem = Path(filename).stem
    parts = stem.split("_")
    if len(parts) < 5:
        return None

    try:
        return datetime.strptime(parts[1], FILENAME_DATE_FORMAT).date()
    except ValueError:
        return None


def is_date_in_range(record_date, start_date, end_date):
    if record_date is None:
        return False
    if start_date and record_date < start_date:
        return False
    if end_date and record_date > end_date:
        return False
    return True


def get_grades_in_date_range(record_dir, start_date=None, end_date=None):
    """
    Return grade files in a record that match the optional inclusive date range.
    """
    matching_files = []

    for file in record_dir.iterdir():
        if not file.is_file() or not file.name.endswith("grades.json"):
            continue

        if start_date is None and end_date is None:
            matching_files.append(file)
            continue

        file_date = extract_date_from_filename(file.name)
        if is_date_in_range(file_date, start_date, end_date):
            matching_files.append(file)

    return matching_files


def is_visible_folder(path):
    """
    Ignore temporary/hidden folders that start with an underscore.
    """
    return path.is_dir() and not path.name.startswith("_")

@dispatchers_bp.route('/dispatchers', methods=['GET'])
def get_dispatchers():
    """
    Returns a list of all dispatchers in the system.

    Dispatchers contain the following:
    `name`
    `overallGrade`
    `numRecords`
    `numTranscripts`
    `numGrades`

    **Returns:**
    - `Dispatcher[] dispatchers`
    """
    try:
        start_date, end_date = get_requested_date_range()

        # Base output directory
        base_dir = Path(OUTPUT_DIR)

        # Initialize response
        response = {
            "dispatchers": [],
            "stationGrade": None,
        }

        # Iterate over dispatcher folders
        for agent_dir in base_dir.iterdir():
            if not is_visible_folder(agent_dir):
                continue

            dispatcher = {
                "name": agent_dir.name,
                "overallGrade": 0,
                "numRecords": 0,
                "numTranscripts": 0,
                "numGrades": 0
            }

            total_grade = 0
            grade_count = 0

            # Iterate over records (subfolders)
            for record_dir in agent_dir.iterdir():
                if not is_visible_folder(record_dir):
                    continue

                matching_grade_files = get_grades_in_date_range(
                    record_dir,
                    start_date,
                    end_date
                )
                if not matching_grade_files:
                    continue

                dispatcher["numRecords"] += 1

                # Iterate over files in each record
                for file in record_dir.iterdir():
                    if not file.is_file():
                        continue

                    filename = file.name

                    if filename.endswith("transcript.json"):
                        dispatcher["numTranscripts"] += 1

                    elif file in matching_grade_files:
                        dispatcher["numGrades"] += 1

                        # Try to read grade_percentage
                        try:
                            with open(file, "r", encoding="utf-8") as f:
                                data = json.load(f)

                            grade = data.get("grade_percentage")
                            if isinstance(grade, (int, float)):
                                total_grade += grade
                                grade_count += 1
                        except Exception:
                            # Skip bad files silently
                            continue

            # Compute average grade
            if grade_count > 0:
                dispatcher["overallGrade"] = round(total_grade / grade_count, 2)
            else:
                dispatcher["overallGrade"] = 0

            if dispatcher["numGrades"] == 0:
                continue

            response["dispatchers"].append(dispatcher)

        if response["dispatchers"]:
            dispatcher_grade_total = sum(
                dispatcher["overallGrade"] for dispatcher in response["dispatchers"]
            )
            response["stationGrade"] = round(
                dispatcher_grade_total / len(response["dispatchers"]),
                2
            )

        # Sort by overall grade
        response["dispatchers"].sort(key=lambda x: x["overallGrade"])

        return jsonify(response), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@dispatchers_bp.route('/dispatchers/<string:name>', methods=['GET'])
def get_dispatcher_records(name):
    """
    Returns a list of all records for a given dispatcher.

    **Returns:**
    - `str[] records`
    """
    try:
        start_date, end_date = get_requested_date_range()

        # Base output directory
        base_dir = Path(OUTPUT_DIR)

        # Check that url is not whitespace
        if not name.strip():
            return jsonify({'error': 'Invalid name'}), 400

        # Check dispatcher folder exists
        agent_dir = base_dir / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return jsonify({'error': f'Agent "{name}" not found'}), 404
        
        # Initialize response
        response = {
            "records": []
        }

        # List subdirectories (call records)
        for item in agent_dir.iterdir():
            if not is_visible_folder(item):
                continue

            matching_grade_files = get_grades_in_date_range(
                item,
                start_date,
                end_date
            )
            if start_date is not None or end_date is not None:
                if not matching_grade_files:
                    continue

            response["records"].append(item.name)
        response["records"].sort()

        return jsonify(response), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@dispatchers_bp.route('/dispatchers/<string:name>/<string:record_name>', methods=['GET'])
def get_record_details(name, record_name):
    """
    Returns all the files (names only) for a given record.
    
    **Returns:**
    - `str[] audioFiles` 
    - `str[] cdrFiles` 
    - `str[] transcriptFiles` 
    - `str[] gradeFiles` 
    - `str[] otherFiles` 
    """
    try:
        record_name = unquote(record_name)

        # Base output directory
        base_dir = Path(OUTPUT_DIR)

        # Check that url is not whitespace
        if not name.strip() or not record_name.strip():
            return jsonify({'error': 'Invalid name or record_name'}), 400

        # Check dispatcher folder exists
        agent_dir = base_dir / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return jsonify({'error': f'Agent "{name}" not found'}), 404

        # Check record folder exists
        record_dir = agent_dir / record_name
        if not record_dir.exists() or not record_dir.is_dir():
            return jsonify({'error': f'Record "{record_name}" not found for agent "{name}"'}), 404

        # Initialize response
        response = {
            "audioFiles": [],
            "cdrFiles": [],
            "transcriptFiles": [],
            "gradeFiles": [],
            "otherFiles": [],
        }

        # Scan directory
        for file in record_dir.iterdir():
            if not file.is_file():
                continue

            filename = file.name

            # Categorize based on naming + extension
            if filename.endswith("audio.wav"):
                response["audioFiles"].append(filename)

            elif filename.endswith("cdr.txt"):
                response["cdrFiles"].append(filename)

            elif filename.endswith("transcript.json"):
                response["transcriptFiles"].append(filename)

            elif filename.endswith("grades.json"):
                response["gradeFiles"].append(filename)

            else:
                response["otherFiles"].append(filename)

        return jsonify(response), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
