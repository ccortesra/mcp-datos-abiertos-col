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
        query_url = scraping.webscrape(search_query)

        req = requests.get(query_url)
        req.raise_for_status()
        return req.text
        
    except Exception as e:
        return f"Error: {str(e)}"
