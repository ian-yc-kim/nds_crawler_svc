import os
import json
import pytest
from nds_crawler_svc.app import app

# The client fixture from conftest.py will be used in tests

@pytest.fixture(autouse=True)
def setup_data_dir(tmp_path):
    # Create a temporary 'data' directory in the tmp_path
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create a test job directory
    test_job_dir = data_dir / "testjob"
    test_job_dir.mkdir()
    
    # Create valid JSON files
    valid_data = {
        "url": "http://example.com",
        "title": "Example",
        "metadata": {"key": "value"},
        "content": "Some content"
    }
    file_names = ["20231010120000.json", "20231010110000.json", "20231010100000.json"]
    for fname in file_names:
        with open(test_job_dir / fname, "w") as f:
            json.dump(valid_data, f)
    
    # Create a malformed JSON file
    with open(test_job_dir / "20231010090000.json", "w") as f:
        f.write("{malformed json")
    
    # Change the current working directory to tmp_path so that the API looks for the 'data' folder there
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


def test_valid_job(client):
    response = client.get("/results/testjob")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "current_page" in data
    assert "total_pages" in data
    # Only valid files should be counted; malformed file is skipped
    # We expect 3 valid files
    assert data["current_page"] == 1
    assert data["total_pages"] == 1
    assert len(data["results"]) == 3


def test_nonexistent_job(client):
    response = client.get("/results/nonexistent")
    assert response.status_code == 404


def test_invalid_page_parameter(client):
    # Passing page value 0 should trigger validation error due to Query(gt=0)
    response = client.get("/results/testjob?page=0")
    assert response.status_code == 422


def test_page_out_of_range(client):
    # With 3 valid results, requesting page 2 should return a 400 error
    response = client.get("/results/testjob?page=2")
    assert response.status_code == 400
    resp_json = response.json()
    assert "Page number out of range" in resp_json["detail"]


def test_malformed_json_handling(client):
    # Malformed JSON file should be skipped, so valid count remains at 3
    response = client.get("/results/testjob")
    data = response.json()
    assert len(data["results"]) == 3
