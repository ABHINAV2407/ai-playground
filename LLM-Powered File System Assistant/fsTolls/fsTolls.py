import os
from datetime import datetime
from typing import Dict, Any

from docx import Document
import PyPDF2

def read_file(filepath: str) -> Dict[str, Any]:
    """
    Reads a file (PDF, DOCX, TXT) and returns structured content.

    Returns:
        {
            "success": bool,
            "content": str,
            "metadata": {...},
            "error": str (if any)
        }
    """

    try:
        if not os.path.exists(filepath):
            return {
                "success": False,
                "content": "",
                "metadata": {},
                "error": f"File not found: {filepath}"
            }

        file_extension = os.path.splitext(filepath)[1].lower()

        # Route to specific handler
        if file_extension == ".txt":
            content = _read_txt(filepath)

        elif file_extension == ".docx":
            content = _read_docx(filepath)

        elif file_extension == ".pdf":
            content = _read_pdf(filepath)

        else:
            return {
                "success": False,
                "content": "",
                "metadata": {},
                "error": f"Unsupported file type: {file_extension}"
            }

        metadata = _get_file_metadata(filepath)

        return {
            "success": True,
            "content": content,
            "metadata": metadata,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "content": "",
            "metadata": {},
            "error": str(e)
        }
    


def _read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
    

def _read_docx(filepath: str) -> str:
    doc = Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])


def _read_pdf(filepath: str) -> str:
    text = ""

    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""

    return text

def _get_file_metadata(filepath: str) -> Dict[str, Any]:
    stats = os.stat(filepath)

    return {
        "filename": os.path.basename(filepath),
        "size_bytes": stats.st_size,
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "file_type": os.path.splitext(filepath)[1].lower()
    }


def list_files(directory: str, extension: str = None) -> list:
    """
    Recursively lists files in a directory.

    Args:
        directory (str): Root directory
        extension (str, optional): Filter by file extension (e.g., '.pdf')

    Returns:
        List of file metadata dictionaries
    """

    files_data = []

    try:
        if not os.path.exists(directory):
            return []

        # normalize extension
        if extension:
            extension = extension.lower()

        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.normpath(os.path.join(root, file))

                file_ext = os.path.splitext(file)[1].lower()

                # filter by extension if provided
                if extension:
                            extension = extension.lower()
                if not extension.startswith("."):
                                extension = "." + extension

                if file_ext != extension:
                                continue

                try:
                    stats = os.stat(filepath)

                    files_data.append({
                        "filename": file,
                        "filepath": filepath,
                        "id": hash(filepath),
                        "size_bytes": stats.st_size,
                        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        "file_type": file_ext
                    })

                except Exception:
                    # skip problematic files but don't crash
                    continue

        return files_data

    except Exception:
        return []
    

def write_file(filepath: str, content: str, mode: str = "overwrite") -> dict:
    """
    Writes content to a file.

    Args:
        filepath (str): Target file path
        content (str): Content to write
        mode (str): 'overwrite' or 'append'

    Returns:
        {
            "success": bool,
            "filepath": str,
            "bytes_written": int,
            "error": str (if any)
        }
    """

    try:
        # validate mode
        if mode not in ["overwrite", "append"]:
            return {
                "success": False,
                "filepath": filepath,
                "bytes_written": 0,
                "error": "Invalid mode. Use 'overwrite' or 'append'"
            }

        # create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # choose file mode
        file_mode = "w" if mode == "overwrite" else "a"

        with open(filepath, file_mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "filepath": filepath,
            "bytes_written": len(content.encode("utf-8")),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "filepath": filepath,
            "bytes_written": 0,
            "error": str(e)
        }


import re


def search_in_file(filepath: str, keyword: str, context_chars: int = 50) -> dict:
    """
    Search for a keyword in file content with hybrid context:
    - Sentence-level context
    - Character window context

    Args:
        filepath (str): File path
        keyword (str): Search keyword
        context_chars (int): Character window size

    Returns:
        {
            "success": bool,
            "matches": [
                {
                    "keyword": str,
                    "match_text": str,
                    "char_context": str,
                    "position": int
                }
            ],
            "total_matches": int,
            "error": str (if any)
        }
    """

    try:
        # reuse read_file
        file_data = read_file(filepath)

        if not file_data["success"]:
            return {
                "success": False,
                "matches": [],
                "total_matches": 0,
                "error": file_data["error"]
            }

        content = file_data["content"]

        content = _clean_text(content)

        matches = []

        # case-insensitive search
        for match in re.finditer(re.escape(keyword), content, re.IGNORECASE):
            start, end = match.start(), match.end()

            # ---- Character Context ----
            char_start = max(0, start - context_chars)
            char_end = min(len(content), end + context_chars)
            char_context = content[char_start:char_end].strip()

            # ---- Sentence Context ----
            sentence = _extract_sentence(content, start, end)

            matches.append({
                "keyword": keyword,
                "match_text": sentence.strip(),
                "char_context": char_context.strip(),
                "position": start
            })

        return {
            "success": True,
            "matches": matches,
            "total_matches": len(matches),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "matches": [],
            "total_matches": 0,
            "error": str(e)
        }
    

def _extract_sentence(text: str, start: int, end: int) -> str:
    """
    Extract meaningful sentence-like context using multiple delimiters.
    """

    # look for nearest separators
    delimiters = r"[.\n•\-]"

    left = re.search(delimiters, text[:start][::-1])
    right = re.search(delimiters, text[end:])

    sentence_start = start - left.start() if left else 0
    sentence_end = end + right.start() if right else len(text)

    return text[sentence_start:sentence_end]



def _clean_text(text: str) -> str:
    """
    Cleans extracted resume text:
    - Fix broken words (Pro- gramming → Programming)
    - Remove extra spaces/newlines
    """

    # fix hyphen line breaks (common in PDFs)
    text = re.sub(r"-\s*\n\s*", "", text)

    # replace newlines with space
    text = re.sub(r"\n+", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()