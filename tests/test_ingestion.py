import pytest
from pathlib import Path
from backend.ingestion.core import ingest_text, ingest_file, handle_images

def test_ingest_text():
    raw = "  hello world  "
    assert ingest_text(raw) == "hello world"

def test_ingest_file(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("  some markdown content  ", encoding="utf-8")
    
    assert ingest_file(test_file) == "some markdown content"

def test_handle_images(tmp_path):
    img1 = tmp_path / "1.png"
    img1.write_text("fake image")
    
    img2 = tmp_path / "2.png" # doesn't exist
    
    valid_paths = handle_images([str(img1), str(img2)], "test-slug")
    assert len(valid_paths) == 1
    assert valid_paths[0] == img1
