"""
Database Tools Module

This module provides tools for local job database management using JSON file storage.
Enables caching of job descriptions to save tokens and reduce redundant online searches.
"""

from smolagents import tool
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


# Database file path
DB_FILE = "jd_database.json"


def _ensure_db_file() -> None:
    """Ensure the database file exists, create it if it doesn't."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_db() -> List[Dict[str, Any]]:
    """Load the database from JSON file."""
    _ensure_db_file()
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_db(data: List[Dict[str, Any]]) -> None:
    """Save the database to JSON file."""
    _ensure_db_file()
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def query_local_db_tool(tags: str) -> str:
    """
    Query the local job database for jobs matching the given tags.

    This tool searches the local JSON database for job descriptions that match
    any of the provided tags. It filters jobs based on tags and returns formatted
    results with company, role, salary, location, and JD content.

    Args:
        tags (str): A string of keywords/tags separated by commas or spaces.
                   Examples:
                   - "Python, Junior, Beijing"
                   - "Java Shanghai Intern"
                   - "AI Engineer Remote"

    Returns:
        str: A formatted string containing matched jobs with their details.
             Format: "Found {count} matching job(s):\n\n1. Company: {company}\n   Role: {role}\n   Location: {location}\n   Salary: {salary}\n   Tags: {tags}\n   JD Content: {content}\n   Date: {date}\n\n..."
             Returns "No match found" if no jobs match the tags.

    Examples:
        >>> result = query_local_db_tool("Python, Beijing")
        >>> print(result)
        "Found 2 matching job(s):\n\n1. Company: ByteDance\n   Role: AI Engineer\n   ..."
    """
    try:
        # Load database
        db = _load_db()
        
        if not db:
            return "No match found. Database is empty."
        
        # Parse tags - split by comma or space, and normalize
        tag_list = [tag.strip().lower() for tag in tags.replace(',', ' ').split() if tag.strip()]
        
        if not tag_list:
            return "No match found. Invalid tags provided."
        
        # Filter jobs that match ANY of the tags
        matched_jobs = []
        for job in db:
            job_tags = job.get('tags', [])
            if not isinstance(job_tags, list):
                job_tags = []
            
            # Check if any tag matches (case-insensitive)
            job_tags_lower = [str(tag).lower() for tag in job_tags]
            company_lower = str(job.get('company', '')).lower()
            role_lower = str(job.get('role', '')).lower()
            location_lower = str(job.get('location', '')).lower()
            content_lower = str(job.get('content', '')).lower()
            
            # Match if any tag appears in tags, company, role, location, or content
            matches = False
            for tag in tag_list:
                if (tag in job_tags_lower or 
                    tag in company_lower or 
                    tag in role_lower or 
                    tag in location_lower or 
                    tag in content_lower):
                    matches = True
                    break
            
            if matches:
                matched_jobs.append(job)
        
        if not matched_jobs:
            return "No match found. No jobs match the provided tags."
        
        # Format results
        result_lines = [f"Found {len(matched_jobs)} matching job(s):\n"]
        
        for idx, job in enumerate(matched_jobs, start=1):
            company = job.get('company', 'Unknown')
            role = job.get('role', 'Unknown')
            location = job.get('location', 'Not specified')
            salary = job.get('salary', 'Not specified')
            content = job.get('content', 'No content')
            job_tags = ', '.join(job.get('tags', []))
            date = job.get('date', 'Unknown')
            
            # Truncate content if too long (keep first 500 chars)
            if len(content) > 500:
                content = content[:500] + "..."
            
            result_lines.append(
                f"{idx}. Company: {company}\n"
                f"   Role: {role}\n"
                f"   Location: {location}\n"
                f"   Salary: {salary}\n"
                f"   Tags: {job_tags}\n"
                f"   Date: {date}\n"
                f"   JD Content: {content}\n"
            )
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Failed to query database: {str(e)}"


@tool
def save_to_db_tool(company: str, role: str, location: str, salary: str, jd_content: str, tags: str) -> str:
    """
    Save a new job entry to the local database.

    This tool adds a new job description to the local JSON database with
    company, role, location, salary, JD content, tags, and timestamp.

    Args:
        company (str): The company name.
                     Example: "ByteDance", "Shopee"
        
        role (str): The job role/position title.
                   Example: "AI Engineer", "Software Developer"
        
        location (str): The work location/base.
                       Example: "Beijing", "Shanghai", "Remote"
        
        salary (str): The salary range or information.
                     Example: "25k-40k/月", "Market Ref: 20k-30k/月"
        
        jd_content (str): The full job description content.
                         Should be the complete JD text extracted from the webpage.
        
        tags (str): A string of tags/keywords separated by commas or spaces.
                   These tags will be used for future searches.
                   Example: "Python, AI, Beijing, Junior"

    Returns:
        str: A success message indicating the job was saved, or an error message.

    Examples:
        >>> result = save_to_db_tool(
        ...     "ByteDance", "AI Engineer", "Beijing", "25k-40k/月",
        ...     "We are looking for...", "Python, AI, Beijing"
        ... )
        >>> print(result)
        "Job saved successfully."
    """
    try:
        # Load existing database
        db = _load_db()
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.replace(',', ' ').split() if tag.strip()]
        
        # Create new job entry
        new_job = {
            "company": company.strip(),
            "role": role.strip(),
            "location": location.strip(),
            "salary": salary.strip(),
            "content": jd_content.strip(),
            "tags": tag_list,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Validate required fields
        if not new_job["company"] or not new_job["role"]:
            return "Error: Company and role are required fields."
        
        # Append to database
        db.append(new_job)
        
        # Save database
        _save_db(db)
        
        return "Job saved successfully."
        
    except Exception as e:
        return f"Error: Failed to save job to database: {str(e)}"
