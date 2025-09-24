print("Testing WebDriver...")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    print("Creating Chrome options...")
    chrome_options = Options()
    # Don't use headless so we can see if browser opens
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    print("Installing ChromeDriver...")
    service = Service(ChromeDriverManager().install())

    print("Starting Chrome browser...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Browser opened successfully!")
    print("Going to Google...")
    driver.get("https://www.google.com")

    print("Sleeping 5 seconds...")
    import time

    time.sleep(5)

    print("Closing browser...")
    driver.quit()

    print("Test completed successfully!")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()