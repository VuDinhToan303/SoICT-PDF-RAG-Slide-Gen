import os
import subprocess
import json
from typing import List, Dict, Any, Tuple
from .utils import logger, get_pdf_filename, ensure_directory_exists

def extract_pdf(pdf_file_path: str, output_base: str = "/kaggle/working") -> None:
    """
    Extract content from a PDF file using minerU CLI.
    
    Args:
        pdf_file_path (str): Path to the input PDF file.
        output_base (str): Base directory to save outputs.
    """
    cmd = f"mineru -p {pdf_file_path} -o {output_base} --source local"
    logger.info(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def split_chunks_by_title(data: List[Dict[str, Any]], max_chunk_len: int = 1000) -> List[str]:
    """
    Split content into chunks based on titles and maximum length.
    
    Args:
        data (List[Dict]): List of content items from JSON.
        max_chunk_len (int): Maximum length for each chunk.
    
    Returns:
        List[str]: List of text chunks.
    """
    chunks = []
    current_title = ""
    current_chunk_texts = []
    i = 0

    def get_text_len(text_list: List[str]) -> int:
        return sum(len(t.strip()) for t in text_list)

    def flush_chunk() -> None:
        nonlocal current_chunk_texts
        if not current_chunk_texts:
            return

        full_text = "\n".join(current_chunk_texts).strip()
        if not full_text:
            return

        if "reference" in current_title.lower() or "tài liệu tham khảo" in current_title.lower():
            lines = full_text.split("\n")
            buffer = []
            buffer_len = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if buffer_len + len(line) > max_chunk_len:
                    chunks.append(f"{current_title.strip()}\n" + "\n".join(buffer).strip())
                    buffer = [line]
                    buffer_len = len(line)
                else:
                    buffer.append(line)
                    buffer_len += len(line)
            if buffer:
                chunks.append(f"{current_title.strip()}\n" + "\n".join(buffer).strip())
        else:
            chunks.append(f"{current_title.strip()}\n{full_text}")

        current_chunk_texts.clear()

    while i < len(data):
        entry = data[i]
        temp_texts = []

        if entry["type"] == "text" and entry.get("text_level") == 1:
            new_title = entry["text"].strip()
            i += 1
            while i < len(data) and data[i].get("text_level") == 1:
                new_title += "\n" + data[i]["text"].strip()
                i += 1
            flush_chunk()
            current_title = new_title
            continue

        if entry["type"] == "equation":
            if i > 0 and data[i-1]["type"] == "text":
                prev_text = data[i-1]["text"].strip()
                if not current_chunk_texts or current_chunk_texts[-1] != prev_text:
                    temp_texts.append(prev_text)
            temp_texts.append(entry["text"].strip())
            if i + 1 < len(data) and data[i+1]["type"] == "text":
                temp_texts.append(data[i+1]["text"].strip())
                i += 1

        elif entry["type"] == "text":
            text = entry["text"].strip()
            if text:
                temp_texts.append(text)

        current_chunk_texts.extend(temp_texts)

        if get_text_len(current_chunk_texts) > max_chunk_len:
            j = i + 1
            while j < len(data):
                next_entry = data[j]
                if next_entry.get("text_level") == 1:
                    break

                lookahead_temp = []

                if next_entry["type"] == "equation":
                    if j > 0 and data[j-1]["type"] == "text":
                        prev_text = data[j-1]["text"].strip()
                        if not current_chunk_texts or current_chunk_texts[-1] != prev_text:
                            lookahead_temp.append(prev_text)
                    lookahead_temp.append(next_entry["text"].strip())
                    if j + 1 < len(data) and data[j+1]["type"] == "text":
                        lookahead_temp.append(data[j+1]["text"].strip())
                        j += 1
                elif next_entry["type"] == "text":
                    lookahead_temp.append(next_entry["text"].strip())

                if get_text_len(lookahead_temp) + get_text_len(current_chunk_texts) <= max_chunk_len:
                    current_chunk_texts.extend(lookahead_temp)
                    j += 1
                    i = j
                else:
                    break

            flush_chunk()

        i += 1

    flush_chunk()
    return chunks

def process_json_data(content_list_json: str, images_root: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Process JSON data and generate summaries for images and tables.
    
    Args:
        content_list_json (str): Path to content list JSON file.
        images_root (str): Root directory for images.
    
    Returns:
        Tuple containing:
        - List of document summaries
        - List of image captions
        - List of table captions
    """
    from .slide_generator import summarize_image_with_gemini, summarize_table_with_gemini
    import uuid
    from langchain.schema import Document

    with open(content_list_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = split_chunks_by_title(data)

    # Process images
    image_summaries = []
    image_captions = []
    for item in data:
        if item['type'] == 'image':
            full_path = os.path.join(images_root, item['img_path'])
            caption = item.get('img_caption', '')
            try:
                response = summarize_image_with_gemini(full_path, caption)
                description = ""
                short_caption = ""
                for line in response.splitlines():
                    if line.startswith("**Image Description**:"):
                        description = line.replace("**Image Description**:", "").strip()
                    elif line.startswith("**Image Caption**:"):
                        short_caption = line.replace("**Image Caption**:", "").strip()
                image_summaries.append(description)
                image_captions.append(short_caption)
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                image_summaries.append(str(e))
                image_captions.append("")

    # Process tables
    table_summaries = []
    table_captions = []
    for item in data:
        if item['type'] == 'table':
            caption = item.get('table_caption', '')
            html = item['table_body']
            try:
                response = summarize_table_with_gemini(caption, html)
                description = ""
                short_caption = ""
                for line in response.splitlines():
                    if line.startswith("**Table Description**:"):
                        description = line.replace("**Table Description**:", "").strip()
                    elif line.startswith("**Table Caption**:"):
                        short_caption = line.replace("**Table Caption**:", "").strip()
                table_summaries.append(description)
                table_captions.append(short_caption)
            except Exception as e:
                logger.error(f"Error processing table: {e}")
                table_summaries.append(str(e))
                table_captions.append("")

    def create_summary_documents(summaries: List[str], data_type: str) -> List[Document]:
        return [
            Document(page_content=summary, metadata={"type": data_type, "doc_id": str(uuid.uuid4())})
            for summary in summaries
        ]

    text_summary_docs = create_summary_documents(chunks, "text_summary")
    image_summary_docs = create_summary_documents(image_summaries, "image_summary")
    table_summary_docs = create_summary_documents(table_summaries, "table_summary")
    all_docs_summary = text_summary_docs + image_summary_docs + table_summary_docs

    return all_docs_summary, image_captions, table_captions 