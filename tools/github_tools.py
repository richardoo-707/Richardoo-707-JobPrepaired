"""
GitHub Tools Module

This module provides tools for searching GitHub repositories.
Uses GitHub API (preferred) or duckduckgo_search as fallback to find repositories.
"""

from smolagents import tool
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub API configuration (optional token for higher rate limits)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
GITHUB_API_URL = "https://api.github.com/search/repositories"


@tool
def search_github_tool(keywords: str) -> str:
    """
    Search for GitHub repositories related to the given keywords.

    This tool uses GitHub API (or duckduckgo_search as fallback) to find the top 3
    GitHub repositories matching the provided keywords. Returns a formatted string
    containing repository name, URL, and description for each result.

    Args:
        keywords (str): Search keywords to find relevant GitHub repositories.
                      Can be technology names, topics, or project descriptions.
                      Example: "machine learning", "react hooks", "python web scraping"

    Returns:
        str: A formatted string containing the top 3 GitHub repositories, with each
             repository showing only:
             - Project: The repository name (owner/repo)
             - Link: The GitHub repository URL
             
             Format example:
             "Project: owner/repo-name
             Link: https://github.com/owner/repo-name
             
             Project: owner2/repo-name2
             Link: https://github.com/owner2/repo-name2"
             
             If search fails, returns an error message.

    Examples:
        >>> result = search_github_tool("machine learning")
        >>> print(result)
        "Project: tensorflow/tensorflow
         Link: https://github.com/tensorflow/tensorflow
         
         Project: pytorch/pytorch
         Link: https://github.com/pytorch/pytorch"

    Error Handling:
        - Returns error message if GitHub API request fails
        - Falls back to alternative search method if available
        - Returns error message if no repositories are found
        - Handles network errors gracefully
    """
    try:
        # Try GitHub API first (preferred method)
        return _search_github_api(keywords)
    except Exception as api_error:
        # If GitHub API fails, try duckduckgo_search as fallback
        try:
            return _search_github_ddg(keywords)
        except Exception as ddg_error:
            return (
                f"Error: Failed to search GitHub repositories for keywords '{keywords}'. "
                f"GitHub API error: {str(api_error)}. "
                f"DuckDuckGo fallback error: {str(ddg_error)}"
            )


def _search_github_api(keywords: str) -> str:
    """
    Search GitHub repositories using GitHub API.
    
    Args:
        keywords (str): Search keywords
        
    Returns:
        str: Formatted string with repository information
        
    Raises:
        Exception: If API request fails
    """
    # Prepare headers (token is optional but recommended for higher rate limits)
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    # Prepare search parameters
    params = {
        "q": keywords,
        "sort": "stars",
        "order": "desc",
        "per_page": 3  # Get top 3 results
    }
    
    try:
        response = requests.get(
            GITHUB_API_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            raise Exception(f"GitHub API rate limit exceeded. Status: {response.status_code}")
        raise Exception(f"GitHub API HTTP error: {e} (status code {response.status_code})")
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub API request failed: {e}")
    
    data = response.json()
    items = data.get("items", [])
    
    if not items:
        return f"No GitHub repositories found for keywords '{keywords}'. Try different keywords."
    
    # Format the results - ONLY Project and Link, no description
    formatted_results = []
    for repo in items:
        repo_name = repo.get("full_name", "unknown")
        repo_url = repo.get("html_url", "")
        
        formatted_result = f"Project: {repo_name}\nLink: {repo_url}"
        formatted_results.append(formatted_result)
    
    return "\n\n".join(formatted_results)


def _search_github_ddg(keywords: str) -> str:
    """
    Search GitHub repositories using DuckDuckGo search as fallback.
    
    Args:
        keywords (str): Search keywords
        
    Returns:
        str: Formatted string with repository information (Project and Link only)
        
    Raises:
        Exception: If search fails
    """
    try:
        from duckduckgo_search import DDGS
        import re
    except ImportError:
        raise Exception("duckduckgo_search module not available. Install with: pip install duckduckgo-search")
    
    # Construct search query targeting GitHub repositories
    query = f'site:github.com {keywords}'
    
    # Initialize DuckDuckGo search
    with DDGS() as ddgs:
        # Search for results, limiting to top 5 to ensure we get at least 3 GitHub repos
        results = list(ddgs.text(query, max_results=5))
    
    if not results:
        raise Exception(f"No search results found for keywords '{keywords}'")
    
    # Filter results to only GitHub repositories and extract repository info
    github_repos = []
    for result in results:
        url = result.get('href', '')
        
        # Use stricter regex to match only repository roots (ignoring issues, pulls, etc.)
        # Match pattern: github.com/owner/repo (end of string or followed by ? or #)
        github_match = re.search(r'github\.com/([^/]+)/([^/?#]+)$', url)
        if github_match:
            owner = github_match.group(1)
            repo_name = github_match.group(2)
            repo_full_name = f"{owner}/{repo_name}"
            
            # Normalize URL to repository root (remove any trailing path)
            repo_url = f"https://github.com/{owner}/{repo_name}"
            
            github_repos.append({
                'name': repo_full_name,
                'url': repo_url
            })
            
            # Stop when we have 3 repositories
            if len(github_repos) >= 3:
                break
    
    if not github_repos:
        raise Exception(f"No GitHub repositories found for keywords '{keywords}'. Try different keywords.")
    
    # Format the results - ONLY Project and Link, no description
    formatted_results = []
    for repo in github_repos:
        formatted_result = f"Project: {repo['name']}\nLink: {repo['url']}"
        formatted_results.append(formatted_result)
    
    return "\n\n".join(formatted_results)
