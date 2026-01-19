"""
File Tools Module

This module provides tools for file operations, such as saving reports and documents.
"""

from smolagents import tool
import os
from pathlib import Path


@tool
def save_report_tool(content: str, filename: str = "career_plan.md") -> str:
    """
    Save content to a local file.

    This tool saves the provided content string into a file with the specified filename
    in the current working directory. Uses UTF-8 encoding to ensure proper handling of
    special characters and multilingual content.

    Args:
        content (str): The text content to save to the file.
                      Should be a string containing the full report/document content.
                      Example: "# Career Plan\n\n## Summary\n..."
        
        filename (str, optional): The name of the file to save. Defaults to 'career_plan.md'.
                                Should include the file extension (e.g., '.md', '.txt').
                                Example: "my_career_plan.md", "report.txt"

    Returns:
        str: A success message indicating the file was saved, or an error message if saving failed.
             Success format: "Report successfully saved to {filename}"
             Error format: "Error: {description of the error}"

    Examples:
        >>> result = save_report_tool("# My Report\n\nContent here", "report.md")
        >>> print(result)
        "Report successfully saved to report.md"

    Error Handling:
        - Returns error message if filename is invalid
        - Returns error message if file cannot be written (permissions, disk space, etc.)
        - Returns error message if content encoding fails
        - Handles directory creation if needed
    """
    try:
        # Validate filename
        if not filename or not isinstance(filename, str):
            return "Error: Invalid filename. Filename must be a non-empty string."
        
        # Sanitize filename to prevent directory traversal attacks
        filename = os.path.basename(filename)
        if not filename:
            return "Error: Invalid filename. Cannot be empty after sanitization."
        
        # Get current working directory
        current_dir = Path.cwd()
        file_path = current_dir / filename
        
        # Ensure the directory exists (should already exist, but just in case)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Return success message with absolute path
        abs_path = file_path.resolve()
        return f"Report successfully saved to {filename} (full path: {abs_path})"
        
    except PermissionError as e:
        return f"Error: Permission denied. Cannot write to file '{filename}': {str(e)}"
    except OSError as e:
        return f"Error: File system error while saving '{filename}': {str(e)}"
    except UnicodeEncodeError as e:
        return f"Error: Content encoding error while saving '{filename}': {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error while saving '{filename}': {str(e)}"
