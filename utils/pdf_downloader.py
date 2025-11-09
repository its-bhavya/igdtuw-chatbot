import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse

# === CONFIG ===
BASE_URL = "https://www.igdtuw.ac.in"
SAVE_DIR = "./igdtuw-data/pdfs"
os.makedirs(SAVE_DIR, exist_ok=True)

# === STARTING PAGES ===
pages_to_check = [
    BASE_URL + "/",
    BASE_URL + "/placements",
    BASE_URL + "/newsletters",
    BASE_URL + "/admissions",
    BASE_URL + "/examinations",
    BASE_URL + "/examinations/datesheets",
    BASE_URL + "/academics",
]

# Track visited URLs to avoid loops
visited = set()

def is_internal_link(url):
    return url.startswith(BASE_URL) or url.startswith("/")

def fetch_pdfs_from_page(driver, page_url, depth=0, max_depth=1):
    """Recursively crawl IGDTUW pages up to max_depth to find PDFs."""
    if page_url in visited or depth > max_depth:
        return 0

    visited.add(page_url)
    new_files = 0
    print(f"\n🌐 Scanning (depth {depth}): {page_url}")

    try:
        driver.get(page_url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"].strip()
            if not href:
                continue

            full_url = urljoin(BASE_URL, href)

            # === CASE 1: PDF Link ===
            if href.lower().endswith(".pdf"):
                pdf_name = full_url.split("/")[-1]
                save_path = os.path.join(SAVE_DIR, pdf_name)
                if not os.path.exists(save_path):
                    try:
                        pdf_data = requests.get(full_url, timeout=15)
                        pdf_data.raise_for_status()
                        with open(save_path, "wb") as f:
                            f.write(pdf_data.content)
                        print(f"✅ Downloaded: {pdf_name}")
                        new_files += 1
                    except Exception as e:
                        print(f"⚠️ Error downloading {full_url}: {e}")

            # === CASE 2: Internal Link (go deeper) ===
            elif is_internal_link(full_url):
                # only crawl IGDTUW internal links, not external
                parsed = urlparse(full_url)
                if "igdtuw.ac.in" in parsed.netloc and full_url not in visited:
                    new_files += fetch_pdfs_from_page(driver, full_url, depth + 1, max_depth)

    except Exception as e:
        print(f"⚠️ Error scanning {page_url}: {e}")

    return new_files


def fetch_pdfs():
    print("🔍 Launching browser to crawl IGDTUW...")

    # === SETUP SELENIUM ===
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    total_new = 0

    for start_page in pages_to_check:
        total_new += fetch_pdfs_from_page(driver, start_page, depth=0, max_depth=1)

    driver.quit()

    if total_new == 0:
        print("\nNo new PDFs found — everything is up to date.")
    else:
        print(f"\n✨ {total_new} new PDFs saved to {SAVE_DIR}.")


if __name__ == "__main__":
    fetch_pdfs()
