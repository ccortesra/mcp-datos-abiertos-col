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

def webscrape(search_query: str) -> str:
    # Configure Chrome options for better compatibility
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
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

        first_links = [link.get_attribute('href') for link in links][:5]

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
                api_export_button = forge_button_toggles[1]
                api_export_button.click()

                time.sleep(4)

                # FIND BUTTON THAT SAYS "Descargar"
                id_api_url = 'api-endpoint'
                api_url = driver.find_element(By.ID, id_api_url).get_attribute('value')

                print(api_url)

                query_components = api_url.split("/")
                print(query_components)

                api_url = "/".join(query_components[:3]) + "/resource/" + f"{query_components[6]}.json"
                api_url = api_url + "?$limit=5&$$app_token=" + app_token
                print(api_url)
                return api_url
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
