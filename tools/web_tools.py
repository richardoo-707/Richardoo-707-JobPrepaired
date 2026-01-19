"""
Web Tools Module

This module provides web-related tools for searching job descriptions and visiting web pages.
Uses smolagents' DuckDuckGoSearchTool and VisitWebpageTool for web operations.
"""

from smolagents import tool, DuckDuckGoSearchTool, VisitWebpageTool


@tool
def search_jd_tool(company: str, role: str) -> str:
    """
    Search for job descriptions (JD) on LinkedIn for a specific company and role.

    This tool uses DuckDuckGoSearchTool to search specifically for job descriptions
    using a query pattern that targets LinkedIn job postings. Returns the top 3
    search result URLs.

    Args:
        company (str): The name of the company to search for.
                     Example: "Google", "Microsoft", "OpenAI"
        
        role (str): The job role or position title to search for.
                   Example: "Software Engineer", "AI Engineer", "Data Scientist"

    Returns:
        str: A string containing the top 3 search result URLs, formatted as a
             newline-separated list. If the search fails, returns an error message.

    Examples:
        >>> result = search_jd_tool("Google", "Software Engineer")
        >>> print(result)
        "https://www.linkedin.com/jobs/view/123456\nhttps://www.linkedin.com/jobs/view/789012\n..."

    Error Handling:
        - Returns error message if search fails
        - Returns error message if DuckDuckGoSearchTool initialization fails
    """
    try:
        # Construct search query targeting LinkedIn job postings
        query = f'site:linkedin.com/jobs {company} {role}'
        
        # Initialize DuckDuckGoSearchTool with max_results=3 to get top 3 results
        search_tool = DuckDuckGoSearchTool(max_results=3, rate_limit=1.0)
        
        # Perform the search
        search_results = search_tool(query)
        
        # Return the results (DuckDuckGoSearchTool returns formatted string with URLs)
        return search_results
        
    except Exception as e:
        return f"Error: Failed to search for job descriptions for {company} {role}: {str(e)}"


@tool
def visit_page_tool(url: str) -> str:
    """
    Visit a webpage and extract its text content.

    This tool uses VisitWebpageTool from smolagents to scrape and extract
    the text content from a given URL. It handles exceptions gracefully
    and returns descriptive error messages if the operation fails.

    Args:
        url (str): The URL of the webpage to visit and scrape.
                  Should be a valid HTTP or HTTPS URL.
                  Example: "https://www.linkedin.com/jobs/view/123456"

    Returns:
        str: A string containing the extracted text content of the webpage.
             If extraction fails, returns a descriptive error message instead.

    Examples:
        >>> result = visit_page_tool("https://example.com")
        >>> print(result)
        "Example Domain\nThis domain is for use in illustrative examples..."

    Error Handling:
        - Returns error message if URL is invalid
        - Returns error message if webpage cannot be accessed
        - Returns error message if content extraction fails
        - Returns error message if VisitWebpageTool initialization fails
    """
    try:
        # Initialize VisitWebpageTool
        visit_tool = VisitWebpageTool()
        
        # Use the tool to scrape the webpage
        # VisitWebpageTool's __call__ method takes a URL and returns text content
        page_content = visit_tool(url)
        
        return page_content
        
    except Exception as e:
        return f"Error: Failed to visit and extract content from URL '{url}': {str(e)}"
