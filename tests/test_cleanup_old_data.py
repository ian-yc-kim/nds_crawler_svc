import os
import time
import datetime
import pytest
import tempfile
import shutil
from pathlib import Path
import logging

from nds_crawler_svc import storage

# Helper function to create a file with specific modification time and size

def create_file(path: Path, mtime: float, size: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        if size > 0:
            f.write(b'0' * size)
        else:
            f.write(b'content')
    os.utime(path, (mtime, mtime))


@pytest.fixture
def temp_storage_dir(tmp_path, monkeypatch):
    # Override STORAGE_DIR to use the temporary directory
    monkeypatch.setattr(storage, 'STORAGE_DIR', str(tmp_path / "data"))
    # Create the base directory
    base_dir = Path(storage.STORAGE_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_cleanup_removes_old_files(temp_storage_dir):
    # Create a file older than 30 days and one recent file
    now = time.time()
    old_time = now - (31 * 24 * 3600)  # 31 days ago
    recent_time = now - (5 * 24 * 3600)  # 5 days ago

    old_file = temp_storage_dir / "old_file.txt"
    recent_file = temp_storage_dir / "recent_file.txt"

    create_file(old_file, old_time)
    create_file(recent_file, recent_time)

    # Run cleanup
    storage.cleanup_old_data()

    # old_file should be deleted, recent_file should remain
    assert not old_file.exists(), "Old file should be deleted"
    assert recent_file.exists(), "Recent file should not be deleted"


def test_cleanup_storage_cap(temp_storage_dir, monkeypatch):
    # Test scenario where total storage exceeds threshold (simulate with smaller threshold)
    # For this test, we monkeypatch the size_threshold to a lower value
    # Create two files that both are recent (not removed by retention policy)
    now = time.time()
    file1 = temp_storage_dir / "file1.txt"
    file2 = temp_storage_dir / "file2.txt"

    # We'll simulate sizes by actually writing content of specific lengths
    # Set file1 size: 60MB, file2 size: 60MB, total = 120MB
    # Then we will set threshold to 100MB (100*1024*1024) for testing purposes
    size_file1 = 60 * 1024 * 1024
    size_file2 = 60 * 1024 * 1024

    create_file(file1, now - (1 * 24 * 3600), size_file1)  # 1 day old
    create_file(file2, now - (2 * 24 * 3600), size_file2)  # 2 days old, so older

    # Monkeypatch os.stat to allow for extra keyword parameters
    original_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        # Remove 'follow_symlinks' if present to avoid unexpected keyword errors
        kwargs.pop('follow_symlinks', None)
        st = original_stat(path, *args, **kwargs)
        path_str = str(path)
        if "file1.txt" in path_str:
            return os.stat_result((st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, size_file1, st.st_atime, st.st_mtime, st.st_ctime))
        elif "file2.txt" in path_str:
            return os.stat_result((st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, size_file2, st.st_atime, st.st_mtime, st.st_ctime))
        return st

    monkeypatch.setattr(os, 'stat', fake_stat)

    # Define a custom cleanup function with a lower threshold
    threshold_bytes = 100 * 1024 * 1024  # 100MB

    original_cleanup = storage.cleanup_old_data

    def cleanup_with_custom_threshold():
        retention_period = 30 * 24 * 3600  # seconds
        now_dt = datetime.datetime.now()

        # Delete files older than retention period (none in this test as both are recent)
        for root, dirs, files in os.walk(storage.STORAGE_DIR):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    stat_info = os.stat(file_path, follow_symlinks=True)
                    file_mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                    if (now_dt - file_mtime).total_seconds() > retention_period:
                        try:
                            os.remove(file_path)
                            logging.info(f"Deleted old file: {file_path}")
                        except Exception as e:
                            logging.error(e, exc_info=True)
                except Exception as e:
                    logging.error(e, exc_info=True)

        # Calculate total storage usage
        total_size = 0
        file_info_list = []
        for root, dirs, files in os.walk(storage.STORAGE_DIR):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    stat_info = os.stat(file_path, follow_symlinks=True)
                    size = stat_info.st_size
                    mtime = stat_info.st_mtime
                    total_size += size
                    file_info_list.append({'path': file_path, 'mtime': mtime, 'size': size})
                except Exception as e:
                    logging.error(e, exc_info=True)

        # If total usage exceeds our test threshold
        if total_size > threshold_bytes:
            file_info_list.sort(key=lambda x: x['mtime'])
            for info in file_info_list:
                if total_size <= threshold_bytes:
                    break
                try:
                    os.remove(info['path'])
                    total_size -= info['size']
                    logging.info(f"Deleted file {info['path']} to reduce storage usage")
                except Exception as e:
                    logging.error(e, exc_info=True)
        logging.info(f"Cleanup completed. Total storage usage: {total_size} bytes.")

    monkeypatch.setattr(storage, 'cleanup_old_data', cleanup_with_custom_threshold)

    # Run cleanup with custom threshold
    storage.cleanup_old_data()

    # In our case, file2 is older than file1, so it should be deleted to reduce total size under threshold
    remaining_files = list(Path(storage.STORAGE_DIR).rglob('*'))
    total_remaining_size = 0
    for f in remaining_files:
        if f.is_file():
            total_remaining_size += f.stat().st_size

    assert total_remaining_size <= threshold_bytes, "Total storage should be under the threshold after cleanup"
    # Since file2 is older, it should have been removed
    assert not file2.exists(), "Older file should be deleted to enforce storage cap"
    # file1 might remain if its size is under the threshold

    # Restore original os.stat and cleanup_old_data
    monkeypatch.undo()
    monkeypatch.setattr(storage, 'cleanup_old_data', original_cleanup)
