import os
import json
import datetime
import logging

# Base directory for storing JSON files. This can be overridden for tests.
STORAGE_DIR = "data"


def store_crawled_data(job_id: str, data: dict) -> str:
    """Stores crawled data as a JSON file in a job-specific directory.

    Args:
        job_id (str): A non-empty string identifier for the job.
        data (dict): A dictionary containing the data to store; must be JSON serializable.

    Returns:
        str: The file path if the data is stored successfully, or an error message if failed.
    """
    # Validate job_id
    if not isinstance(job_id, str) or not job_id.strip():
        return "Error: job_id must be a non-empty string."

    # Validate that data is JSON serializable
    try:
        json_str = json.dumps(data)
    except (TypeError, ValueError) as e:
        logging.error(e, exc_info=True)
        return f"Error: data is not JSON serializable: {e}"

    # Generate a timestamp-based filename (format: YYYYMMDDHHMMSS.json)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}.json"

    # Create the directory structure STORAGE_DIR/<job_id>/
    directory = os.path.join(STORAGE_DIR, job_id)
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logging.error(e, exc_info=True)
        return f"Error: failed to create directory {directory}: {e}"

    file_path = os.path.join(directory, filename)

    # Write JSON data to the file with proper exception handling
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_str)
    except Exception as e:
        logging.error(e, exc_info=True)
        return f"Error: failed to write data to file {file_path}: {e}"

    return file_path
