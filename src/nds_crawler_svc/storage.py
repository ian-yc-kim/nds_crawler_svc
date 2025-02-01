import os
import json
import datetime
import logging
from datetime import timedelta

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


def cleanup_old_data() -> None:
    """Cleanup mechanism for stored crawled data.

    1. Delete files older than 30 days based on file modification time.
    2. If total storage usage exceeds 100GB, delete the oldest files until usage is below the threshold.

    All file system operations are wrapped in try/except blocks with appropriate logging.
    """
    retention_period = timedelta(days=30)
    size_threshold = 100 * 1024**3  # 100GB in bytes
    now = datetime.datetime.now()

    # First, delete files older than retention period
    for root, dirs, files in os.walk(STORAGE_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                stat = os.stat(file_path)
                file_mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                if now - file_mtime > retention_period:
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logging.error(e, exc_info=True)
            except Exception as e:
                logging.error(e, exc_info=True)

    # After old file cleanup, check total storage usage
    total_size = 0
    file_info_list = []
    for root, dirs, files in os.walk(STORAGE_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                mtime = stat.st_mtime
                total_size += size
                file_info_list.append({'path': file_path, 'mtime': mtime, 'size': size})
            except Exception as e:
                logging.error(e, exc_info=True)

    # If storage exceeds threshold, delete oldest files until under limit
    if total_size > size_threshold:
        # Order files by modification time (oldest first)
        file_info_list.sort(key=lambda x: x['mtime'])
        for info in file_info_list:
            if total_size <= size_threshold:
                break
            try:
                os.remove(info['path'])
                total_size -= info['size']
                logging.info(f"Deleted file {info['path']} to reduce storage usage")
            except Exception as e:
                logging.error(e, exc_info=True)

    logging.info(f"Cleanup completed. Total storage usage: {total_size} bytes.")
