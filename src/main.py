import os
import argparse
from typing import Optional
from .utils import setup_directories, logger, get_pdf_filename
from .data_processing import extract_pdf, process_json_data
from .slide_generator import create_presentation

def process_pdf_to_slides(
    pdf_path: str,
    output_dir: Optional[str] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    Process a PDF file and generate presentation slides.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_dir (str, optional): Directory to save output files
        output_filename (str, optional): Name for the output PowerPoint file
    
    Returns:
        str: Path to the generated PowerPoint file
    """
    # Setup directories
    base_path = output_dir or os.path.dirname(pdf_path)
    dirs = setup_directories(base_path)
    
    # Get PDF filename without extension
    pdf_filename = get_pdf_filename(pdf_path)
    
    # Define output paths
    output_base = os.path.join(base_path, pdf_filename)
    markdown_file = os.path.join(output_base, "auto", f"{pdf_filename}.md")
    middle_json = os.path.join(output_base, "auto", f"{pdf_filename}_middle.json")
    content_list_json = os.path.join(output_base, "auto", f"{pdf_filename}_content_list.json")
    
    # Extract PDF content
    logger.info(f"Extracting content from PDF: {pdf_path}")
    extract_pdf(pdf_path, output_base)
    
    # Process JSON data
    logger.info("Processing JSON data and generating summaries")
    all_docs_summary, image_captions, table_captions = process_json_data(
        content_list_json,
        os.path.join(output_base, "auto")
    )
    
    # Generate slides
    output_file = output_filename or os.path.join(dirs['output'], f"{pdf_filename}.pptx")
    logger.info(f"Generating slides: {output_file}")
    create_presentation(
        all_docs_summary,
        pdf_filename,
        output_file
    )
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to presentation slides")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("--output-dir", help="Directory to save output files")
    parser.add_argument("--output-filename", help="Name for the output PowerPoint file")
    
    args = parser.parse_args()
    
    try:
        output_file = process_pdf_to_slides(
            args.pdf_path,
            args.output_dir,
            args.output_filename
        )
        logger.info(f"Successfully generated slides: {output_file}")
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise

if __name__ == "__main__":
    main() 