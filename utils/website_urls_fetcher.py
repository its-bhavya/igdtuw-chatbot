import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

def is_reachable(url, timeout=2):
    try:
        r = requests.head(url, timeout=timeout)
        return r.status_code < 400
    except:
        return False
    
driver = webdriver.Chrome() # Or other browser driver like Firefox
driver.get("https://www.igdtuw.ac.in")


links = driver.find_elements(By.TAG_NAME, "a")
urls = list(set([link.get_attribute("href") for link in links if link.get_attribute("href")]))

driver.quit()

cleaned_urls = [u for u in urls if u != "https://www.igdtuw.ac.in/#"]
cleaned_urls = [u for u in cleaned_urls if is_reachable(u)]
print(len(cleaned_urls))

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go to the parent directory
parent_dir = os.path.dirname(current_dir)

# Path to output file
output_path = os.path.join(parent_dir, "urls.txt")

with open(output_path, "w") as f:
    for url in cleaned_urls:
        f.write(url + "\n")

print(f"Saved {len(cleaned_urls)} to: {output_path}")
