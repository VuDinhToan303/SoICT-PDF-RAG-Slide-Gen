import os
import pytest
from src.main import process_pdf_to_slides
from src.utils import setup_directories

def test_setup_directories():
    """Test that directory setup works correctly"""
    test_dir = "test_output"
    dirs = setup_directories(test_dir)
    
    # Check that all required directories exist
    assert os.path.exists(dirs['raw'])
    assert os.path.exists(dirs['processed'])
    assert os.path.exists(dirs['output'])
    
    # Clean up
    for dir_path in dirs.values():
        if os.path.exists(dir_path):
            os.rmdir(dir_path)
    if os.path.exists(test_dir):
        os.rmdir(test_dir)

def test_process_pdf_to_slides_invalid_pdf():
    """Test that processing an invalid PDF raises an error"""
    with pytest.raises(Exception):
        process_pdf_to_slides("nonexistent.pdf")

# Add more tests as needed 