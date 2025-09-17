"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

import sys
import traceback

try:
    from mcp.server.fastmcp import FastMCP
    import scraping
    import requests
    from dotenv import load_dotenv
    import os
    
    print("Loading environment variables...", file=sys.stderr)
    load_dotenv()

    # Configuration: Set to False to show the browser window, True to run headless
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'  # Set via environment variable or default to True
    QUERY_LIMIT_ROW = os.getenv('QUERY_LIMIT_ROW', '50')
    print(f"HEADLESS_MODE: {HEADLESS_MODE}", file=sys.stderr)
    
    # Create an MCP server
    print("Creating MCP server...", file=sys.stderr)
    mcp = FastMCP("Demo")
    print("MCP server created successfully", file=sys.stderr)

except Exception as e:
    print(f"Error during startup: {e}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    sys.exit(1)

try:
    # Add an addition tool
    print("Defining fetch_data tool...", file=sys.stderr)
    @mcp.tool()
    def fetch_data(search_query: str) -> str:
        """
        Fetch data from Colombian Open Data API, this tool will fetch data given a search query. And will return the data in a JSON format.
        Busca datos en la plataforma de datos abiertos Colombia, dado un término de búsqueda, y retorna los datos en un formato JSON.
        
        Args:
            search_query (str): The search term to look for datasets
        
        Returns:
            str: JSON string with the data
        """
        print(f"[TOOL] Starting fetch_data with search_query: '{search_query}'", file=sys.stderr)
        
        app_token = os.getenv('APP_TOKEN')
        if not app_token:
            print("[TOOL] Error: APP_TOKEN not found in environment variables", file=sys.stderr)
            return "Error: APP_TOKEN not found in environment variables"
        
        print(f"[TOOL] APP_TOKEN found, length: {len(app_token)}", file=sys.stderr)
        
        try:
            print(f"[TOOL] Starting webscrape with headless mode: {HEADLESS_MODE}", file=sys.stderr)
            query_url = scraping.webscrape(search_query, headless=HEADLESS_MODE)
            print(f"[TOOL] Webscrape completed, returned: {query_url[:100]}...", file=sys.stderr)
            
            # Check if webscrape returned an error message instead of a URL
            if query_url.startswith("Error:"):
                print(f"[TOOL] Webscrape returned error: {query_url}", file=sys.stderr)
                return query_url
            
            # Validate that we have a proper URL
            if not query_url.startswith(("http://", "https://")):
                error_msg = f"Error: Invalid URL returned from webscrape: {query_url}"
                print(f"[TOOL] {error_msg}", file=sys.stderr)
                return error_msg

            print(f"[TOOL] Making HTTP request to: {query_url}", file=sys.stderr)
            req = requests.get(query_url)
            req.raise_for_status()
            print(f"[TOOL] HTTP request successful, response length: {len(req.text)}", file=sys.stderr)
            return req.text
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[TOOL] Exception occurred: {error_msg}", file=sys.stderr)
            return error_msg

    print("Tool defined successfully", file=sys.stderr)

except Exception as e:
    print(f"Error defining tools: {e}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    import sys
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running in test mode...", file=sys.stderr)
        try:
            result = fetch_data("educacion")
            print(f"Test result: {result[:200]}..." if len(result) > 200 else f"Test result: {result}", file=sys.stderr)
        except Exception as e:
            print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(0)
    
    try:
        print("Starting MCP server...", file=sys.stderr)
        print("Server is ready and waiting for MCP client connection...", file=sys.stderr)
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)