from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from dotenv import load_dotenv
import os
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
        print("Running in headless mode (browser not visible)")
    else:
        print("Running in visible mode (browser will be shown)")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    
    # Only disable images in headless mode for better performance
    if headless:
        chrome_options.add_argument("--disable-images")
    
    try:
        # Automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        return f"Error: Could not start Chrome browser - {str(e)}"
    
    try:
        driver.get(f"https://datos.gov.co/browse?sortBy=relevance&pageSize=20&q={search_query}")
        time.sleep(4)
       
        tag = 'entry-name-link'
        links = driver.find_elements(By.CLASS_NAME, tag)

        if not links:
            return "Error: No datasets found for the given search query"

        max_links = min(len(links), 7)  # Use min instead of max to avoid index errors

        first_links = [link.get_attribute('href') for link in links][:max_links]

        for link in first_links:
            try:
                # Enter to the first link
                print(link)
                driver.get(link)
                time.sleep(4)
                # FIND BUTTON THAT SAYS "Descargar"
                button = driver.find_element(By.TAG_NAME, "forge-button")
                button.click()

                time.sleep(4)

                forge_button_toggles = driver.find_elements(By.TAG_NAME, 'forge-button-toggle')
                print(forge_button_toggles)
                
                # Check if we have enough buttons
                if len(forge_button_toggles) < 2:
                    print(f"Not enough forge-button-toggle elements found: {len(forge_button_toggles)}")
                    continue
                    
                api_export_button = forge_button_toggles[1]
                api_export_button.click()

                time.sleep(4)

                # FIND API ENDPOINT INPUT
                id_api_url = 'api-endpoint'
                try:
                    api_url_element = driver.find_element(By.ID, id_api_url)
                    api_url = api_url_element.get_attribute('value')
                    
                    if not api_url:
                        print("API URL element found but value is empty")
                        continue
                        
                    print(f"Found API URL: {api_url}")

                    query_components = api_url.split("/")
                    print(f"URL components: {query_components}")
                    
                    # Validate URL structure
                    if len(query_components) < 7:
                        print(f"URL structure invalid, not enough components: {len(query_components)}")
                        continue

                    api_url = "/".join(query_components[:3]) + "/resource/" + f"{query_components[6]}.json"
                    api_url = api_url + "?$limit=5&$$app_token=" + app_token
                    print(f"Final API URL: {api_url}")
                    return api_url
                    
                except Exception as api_error:
                    print(f"Error finding API endpoint: {api_error}")
                    continue
            except Exception as e:
                print(f"Error processing link {link}: {e}")
                continue
        
        # If no links worked
        return "Error: Could not extract API URL from any of the found datasets"
        
    except Exception as e:
        return f"Error during web scraping: {str(e)}"
    finally:
        # Always close the browser
        try:
            driver.quit()
        except:
            pass
