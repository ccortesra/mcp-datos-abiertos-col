from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from dotenv import load_dotenv
import os
import shutil
import sys
import logging

# Configure logging to stderr so it shows up in Docker logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SCRAPING] %(levelname)s: %(message)s',
    stream=sys.stderr
)
load_dotenv()
app_token = os.getenv('APP_TOKEN')

def webscrape(search_query: str, headless: bool = True) -> str:
    """
    Scrape Colombian Open Data portal for API endpoints.
    
    Args:
        search_query (str): The search term to look for datasets
        headless (bool): If True, runs browser in headless mode (invisible). 
                        If False, shows the browser window for debugging/monitoring.
    
    Returns:
        str: API URL with token, or error message if scraping fails
    """
    # Configure Chrome options for better compatibility
    chrome_options = Options()
    
    # Add headless mode only if requested
    if headless:
        chrome_options.add_argument("--headless")  # Run in background
        logging.info("Running in headless mode (browser not visible)")
    else:
        logging.info("Running in visible mode (browser will be shown)")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Only disable images in headless mode for better performance
    if headless:
        chrome_options.add_argument("--disable-images")
    
    try:
        # Use system-installed ChromeDriver to avoid version mismatch
        logging.info("Initializing ChromeDriver...")
        chromedriver_path = shutil.which('chromedriver')
        if chromedriver_path:
            logging.info(f"Using system ChromeDriver at: {chromedriver_path}")
            service = Service(chromedriver_path)
        else:
            # Fallback to common system paths
            logging.info("ChromeDriver not in PATH, checking common system paths...")
            common_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/app/chromedriver'  # Docker container path
            ]
            
            service = None
            for path in common_paths:
                logging.info(f"Checking for ChromeDriver at: {path}")
                if os.path.exists(path):
                    logging.info(f"Found ChromeDriver at: {path}")
                    service = Service(path)
                    break
            
            if not service:
                logging.error("ChromeDriver not found in any common paths")
                return "Error: ChromeDriver not found. Please install chromedriver that matches your Chrome/Chromium version"
        
        logging.info("Starting Chrome browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Chrome browser started successfully")
    except Exception as e:
        error_msg = f"Error: Could not start Chrome browser - {str(e)}"
        logging.error(error_msg)
        return error_msg
    
    try:
        search_url = f"https://datos.gov.co/browse?sortBy=relevance&pageSize=20&q={search_query}"
        logging.info(f"Navigating to search URL: {search_url}")
        driver.get(search_url)
        logging.info("Waiting for page to load...")
        time.sleep(4)
       
        tag = 'entry-name-link'
        logging.info(f"Looking for dataset links with class: {tag}")
        links = driver.find_elements(By.CLASS_NAME, tag)
        logging.info(f"Found {len(links)} dataset links")

        if not links:
            logging.warning("No datasets found for the given search query")
            return "Error: No datasets found for the given search query"

        max_links = min(len(links), 10)  # Use min instead of max to avoid index errors
        logging.info(f"Processing first {max_links} links")

        first_links = [link.get_attribute('href') for link in links][:max_links]
        logging.info(f"Dataset URLs to process: {first_links}")

        for i, link in enumerate(first_links, 1):
            try:
                logging.info(f"Processing dataset {i}/{max_links}: {link}")
                driver.get(link)
                logging.info("Waiting for dataset page to load...")
                time.sleep(2)
                
                # FIND BUTTON THAT SAYS "Descargar"
                logging.info("Looking for download button (forge-button)...")
                button = driver.find_element(By.TAG_NAME, "forge-button")
                logging.info("Found download button, clicking...")
                button.click()

                logging.info("Waiting for download options to appear...")
                time.sleep(2)

                logging.info("Looking for export format buttons...")
                forge_button_toggles = driver.find_elements(By.TAG_NAME, 'forge-button-toggle')
                logging.info(f"Found {len(forge_button_toggles)} export format buttons")
                
                # Check if we have enough buttons
                if len(forge_button_toggles) < 2:
                    logging.warning(f"Not enough forge-button-toggle elements found: {len(forge_button_toggles)}, skipping this dataset")
                    continue
                    
                logging.info("Clicking API export button (2nd toggle button)...")
                api_export_button = forge_button_toggles[1]
                api_export_button.click()

                logging.info("Waiting for API endpoint to appear...")
                time.sleep(4)

                # FIND API ENDPOINT INPUT
                id_api_url = 'api-endpoint'
                try:
                    logging.info(f"Looking for API endpoint input with ID: {id_api_url}")
                    api_url_element = driver.find_element(By.ID, id_api_url)
                    api_url = api_url_element.get_attribute('value')
                    
                    if not api_url:
                        logging.warning("API URL element found but value is empty, trying next dataset")
                        continue
                        
                    logging.info(f"Found raw API URL: {api_url}")

                    query_components = api_url.split("/")
                    logging.info(f"URL components: {query_components}")
                    
                    # Validate URL structure
                    if len(query_components) < 7:
                        logging.warning(f"URL structure invalid, not enough components: {len(query_components)}, trying next dataset")
                        continue

                    api_url = "/".join(query_components[:3]) + "/resource/" + f"{query_components[6]}.json"
                    api_url = api_url + "?$limit=5&$$app_token=" + app_token
                    logging.info(f"Final constructed API URL: {api_url}")
                    logging.info("Successfully found API endpoint, returning URL")
                    return api_url
                    
                except Exception as api_error:
                    logging.error(f"Error finding API endpoint: {api_error}")
                    continue
            except Exception as e:
                logging.error(f"Error processing dataset {link}: {e}")
                continue
        
        # If no links worked
        logging.error("Could not extract API URL from any of the found datasets")
        return "Error: Could not extract API URL from any of the found datasets"
        
    except Exception as e:
        error_msg = f"Error during web scraping: {str(e)}"
        logging.error(error_msg)
        return error_msg
    finally:
        # Always close the browser
        logging.info("Closing browser...")
        try:
            driver.quit()
            logging.info("Browser closed successfully")
        except Exception as e:
            logging.warning(f"Error closing browser: {e}")
