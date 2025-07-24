from selenium import webdriver
from selenium.webdriver.common.by import By

# Replace with your desired URL
url = "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions"

# Initialize the WebDriver (make sure you have the correct driver installed)
driver = webdriver.Chrome()  # or webdriver.Firefox(), etc.

try:
    driver.get(url)
    h1_elements = driver.find_elements(By.TAG_NAME, "span")
    for h1 in h1_elements:
        print(h1.text)
finally:
    driver.quit()