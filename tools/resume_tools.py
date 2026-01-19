"""
Resume Tools Module

This module provides tools for reading and extracting text from PDF resume files.
Uses pypdf for PDF processing and smolagents @tool decorator for agent integration.
"""

from smolagents import tool
from pypdf import PdfReader
import os


@tool
def read_resume_tool(file_path: str) -> str:
    """
    Extract all text content from a PDF resume file.

    This tool reads a PDF file at the specified path and extracts all text content
    from all pages. It handles errors gracefully and returns descriptive error messages
    if extraction fails.

    Args:
        file_path (str): The file system path to the PDF file to be read.
                        Should be a valid path to an existing .pdf file.
                        Example: "./resume.pdf" or "/path/to/resume.pdf"

    Returns:
        str: A string containing all extracted text from the PDF file, with pages
             separated by newlines. If extraction fails at any point, returns a
             descriptive error message string instead.

    Examples:
        >>> result = read_resume_tool("./resume.pdf")
        >>> print(result)
        "John Doe\nSoftware Engineer\n..."

    Error Handling:
        - Returns error message if file doesn't exist
        - Returns error message if file is not a PDF
        - Returns error message if PDF cannot be opened
        - Returns error message if text extraction fails on any page
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return f"Error: File does not exist at path: {file_path}"
    
    # Check if file is a PDF
    if not file_path.lower().endswith('.pdf'):
        return f"Error: File is not a PDF format. Expected .pdf file, got: {file_path}"
    
    # Check if it's a file (not a directory)
    if not os.path.isfile(file_path):
        return f"Error: Path is not a file: {file_path}"
    
    try:
        # Initialize PDF reader
        reader = PdfReader(file_path)
    except Exception as e:
        return f"Error: Failed to open PDF file '{file_path}': {str(e)}"
    
    # Extract text from all pages
    text_parts = []
    try:
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                else:
                    # Note if page has no extractable text
                    text_parts.append(f"[Page {page_num}: No text extracted]")
            except Exception as e:
                return f"Error: Failed to extract text from page {page_num} of '{file_path}': {str(e)}"
    except Exception as e:
        return f"Error: Failed to process pages of PDF '{file_path}': {str(e)}"
    
    # Combine all pages with newlines
    if not text_parts:
        return f"Error: No text could be extracted from PDF file '{file_path}'"
    
    full_text = "\n\n".join(text_parts)
    return full_text
