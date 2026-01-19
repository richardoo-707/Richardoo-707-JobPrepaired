"""
Market Analysis Tools Module

This module provides tools for analyzing job market trends and finding companies
that hire candidates with similar backgrounds based on social proof from Chinese
job platforms like Nowcoder (牛客网) and Zhihu (知乎).
"""

from smolagents import tool, DuckDuckGoSearchTool


@tool
def analyze_market_match_tool(user_tags: str) -> str:
    """
    Analyze job market to find companies that hire candidates with similar background tags.

    This tool searches Nowcoder (牛客网) and Zhihu (知乎) to find real-world data about
    which companies hire candidates with specific background tags. It uses social proof
    from user posts and discussions to identify reachable companies.

    Args:
        user_tags (str): A string describing the user's background tags.
                        Should include educational background, major, experience level, etc.
                        Examples:
                        - "985 Master CS"
                        - "211 Bachelor Non-CS"
                        - "双非本科 计算机"
                        - "Overseas Student Master"
                        - "双非 非科班 转码"

    Returns:
        str: Search results containing snippets from Nowcoder and Zhihu that mention
             companies hiring candidates with similar tags. The results typically include
             lists of companies mentioned in posts like "Got offers from Shopee, Meyitu, and ByteDance".
             If search fails, returns an error message.

    Examples:
        >>> result = analyze_market_match_tool("双非本科 计算机")
        >>> print(result)
        "Search results from Nowcoder and Zhihu showing companies that hire candidates with 双非本科 计算机 background..."

    Search Strategy:
        The tool performs multiple searches:
        1. site:nowcoder.com {user_tags} offer 比较
        2. site:nowcoder.com {user_tags} 也是双非 拿到offer
        3. site:zhihu.com {user_tags} offer 公司
        4. site:zhihu.com {user_tags} 拿到 offer

    Error Handling:
        - Returns error message if search fails
        - Returns error message if DuckDuckGoSearchTool encounters issues
        - Returns error message if no results are found
    """
    try:
        # Initialize DuckDuckGoSearchTool
        search_tool = DuckDuckGoSearchTool(max_results=5, rate_limit=1.0)
        
        # Construct multiple search queries for comprehensive coverage
        queries = [
            f'site:nowcoder.com {user_tags} offer 比较',
            f'site:nowcoder.com {user_tags} 也是双非 拿到offer',
            f'site:zhihu.com {user_tags} offer 公司',
            f'site:zhihu.com {user_tags} 拿到 offer'
        ]
        
        all_results = []
        
        # Perform searches for each query
        for query in queries:
            try:
                search_results = search_tool(query)
                if search_results and search_results.strip():
                    all_results.append(f"Query: {query}\nResults: {search_results}\n")
            except Exception as e:
                # Continue with other queries if one fails
                all_results.append(f"Query: {query}\nError: {str(e)}\n")
                continue
        
        if not all_results or not any(result.strip() for result in all_results):
            return f"Error: No search results found for user tags '{user_tags}'. Try different tags or check if the platforms are accessible."
        
        # Combine all results
        combined_results = "\n---\n".join(all_results)
        
        return f"Market analysis results for tags '{user_tags}':\n\n{combined_results}"
        
    except Exception as e:
        return f"Error: Failed to analyze market match for tags '{user_tags}': {str(e)}"
