import os
import json
import pytest
import datetime

from nds_crawler_svc.storage import store_crawled_data, STORAGE_DIR


# Fixture to override the STORAGE_DIR to a temporary directory during tests
@pytest.fixture(autouse=True)
def override_storage_dir(tmp_path, monkeypatch):
    # Set STORAGE_DIR to the temporary directory provided by tmp_path
    monkeypatch.setattr("nds_crawler_svc.storage.STORAGE_DIR", str(tmp_path))
    return tmp_path


def test_store_crawled_data_success(tmp_path):
    job_id = "test_job"
    data = {"key": "value", "number": 123}
    
    # Call the function
    result = store_crawled_data(job_id, data)

    # Verify that the returned result is a file path
    # Since the filename is timestamp based, we check that the file exists
    assert os.path.exists(result), f"File {result} should exist"

    # Read the file and verify its content
    with open(result, "r", encoding="utf-8") as f:
        content = json.load(f)
    assert content == data


def test_store_crawled_data_invalid_job_id():
    # Test with an empty job_id
    job_id = ""
    data = {"key": "value"}

    result = store_crawled_data(job_id, data)
    assert "Error: job_id must be a non-empty string." == result


def test_store_crawled_data_non_serializable_data():
    # Test with non-serializable data (e.g., including a lambda function)
    job_id = "test_job"
    data = {"key": lambda x: x}

    result = store_crawled_data(job_id, data)
    assert result.startswith("Error: data is not JSON serializable:"), "Should return an error about JSON serialization"


# Optionally, simulate a file write error by monkeypatching open

def test_store_crawled_data_file_write_error(monkeypatch):
    job_id = "test_job"
    data = {"key": "value"}

    def fake_open(*args, **kwargs):
        raise IOError("Simulated file write error")

    monkeypatch.setattr("builtins.open", fake_open)

    result = store_crawled_data(job_id, data)
    assert "Error: failed to write data to file" in result
