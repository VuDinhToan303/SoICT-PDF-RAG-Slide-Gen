import os
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: str) -> Dict[str, str]:
    """Create necessary directories for the project."""
    dirs = {
        'raw': os.path.join(base_path, 'data/raw'),
        'processed': os.path.join(base_path, 'data/processed'),
        'output': os.path.join(base_path, 'data/output'),
        'chroma': os.path.join(base_path, 'chroma_db')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    return dirs

def clean_directory(directory: str) -> None:
    """Clean a directory by removing all its contents."""
    if os.path.exists(directory):
        shutil.rmtree(directory)
        os.makedirs(directory)
        logger.info(f"Cleaned directory: {directory}")

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON to: {filepath}")

def load_json(filepath: str) -> Any:
    """Load data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Loaded JSON from: {filepath}")
    return data

def get_pdf_filename(pdf_path: str) -> str:
    """Extract filename without extension from PDF path."""
    return os.path.splitext(os.path.basename(pdf_path))[0]

def ensure_directory_exists(filepath: str) -> None:
    """Ensure the directory for a file exists."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def copy_file(src: str, dst: str) -> None:
    """Copy a file from source to destination."""
    ensure_directory_exists(dst)
    shutil.copy2(src, dst)
    logger.info(f"Copied file: {src} -> {dst}") 