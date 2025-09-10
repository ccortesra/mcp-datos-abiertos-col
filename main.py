"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from mcp.server.fastmcp import FastMCP
import scraping
import requests
from dotenv import load_dotenv
import os
load_dotenv()

# Configuration: Set to False to show the browser window, True to run headless
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'  # Set via environment variable or default to True
print(f"HEADLESS_MODE: {HEADLESS_MODE}")
# Create an MCP server
mcp = FastMCP("Demo")

# Add an addition tool
@mcp.tool()
def fetch_data(search_query: str) -> str:
    """Fetch data from Colombian Open Data API"""
    app_token = os.getenv('APP_TOKEN')
    if not app_token:
        return "Error: APP_TOKEN not found in environment variables"
    
    try:
        query_url = scraping.webscrape(search_query, headless=HEADLESS_MODE)
        
        # Check if webscrape returned an error message instead of a URL
        if query_url.startswith("Error:"):
            return query_url
        
        # Validate that we have a proper URL
        if not query_url.startswith(("http://", "https://")):
            return f"Error: Invalid URL returned from webscrape: {query_url}"

        req = requests.get(query_url)
        req.raise_for_status()
        return req.text
        
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")