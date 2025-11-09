import os
import time
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
BASE_URL = "https://www.igdtuw.ac.in"
SAVE_PATH = r"igdtuw-data\json_data\web_content.json"

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

visited = set()
content_data = []


def is_internal_link(url):
    return url.startswith(BASE_URL) or url.startswith("/")


def relevance_from_url(url):
    """Heuristic label based on URL content."""
    url_lower = url.lower()
    if "exam" in url_lower:
        return "examination info"
    elif "admission" in url_lower:
        return "admission info"
    elif "placement" in url_lower:
        return "placement info"
    elif "newsletter" in url_lower:
        return "news/updates"
    elif "academic" in url_lower or "course" in url_lower:
        return "academic content"
    else:
        return "general info"


def clean_page_text(soup):
    """Extract readable text content from a BeautifulSoup page."""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.extract()
    text = " ".join(soup.stripped_strings)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_metadata_from_page(driver, page_url, depth=0, max_depth=1):
    """Recursively crawl IGDTUW pages to record URLs, metadata, and text."""
    if page_url in visited or depth > max_depth:
        return 0

    visited.add(page_url)
    new_items = 0
    print(f"\n🌐 Scanning (depth {depth}): {page_url}")

    try:
        driver.get(page_url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else "No title"

        # --- Extract text ---
        page_text = clean_page_text(soup)
        if len(page_text) > 10000:
            page_text = page_text[:10000] + "..."

        # --- Store data for the current page ---
        content_data.append({
            "url": page_url,
            "type": "webpage",
            "title": page_title,
            "relevance_hint": relevance_from_url(page_url),
            "text": page_text
        })
        new_items += 1

        # --- Follow internal links ---
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"].strip()
            if not href:
                continue
            full_url = urljoin(BASE_URL, href)

            # === CASE 1: PDF Link ===
            if href.lower().endswith(".pdf"):
                content_data.append({
                    "url": full_url,
                    "type": "pdf",
                    "title": link.get_text(strip=True) or "PDF Document",
                    "relevance_hint": relevance_from_url(full_url),
                    "text": ""
                })
                new_items += 1

            # === CASE 2: Internal Link ===
            elif is_internal_link(full_url):
                parsed = urlparse(full_url)
                if "igdtuw.ac.in" in parsed.netloc and full_url not in visited:
                    new_items += fetch_metadata_from_page(driver, full_url, depth + 1, max_depth)

    except Exception as e:
        print(f"⚠️ Error scanning {page_url}: {e}")

    return new_items


def crawl_igdtuw():
    """Launch browser and crawl the website."""
    print("🔍 Launching browser to crawl IGDTUW...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    total_new = 0

    for start_page in pages_to_check:
        total_new += fetch_metadata_from_page(driver, start_page, depth=0, max_depth=1)

    driver.quit()

    # Save metadata + text
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(content_data, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Crawling complete. {total_new} entries saved to {SAVE_PATH}.")


# === RETRIEVAL UTILITY ===
def search_content(keyword=None, content_type=None, relevance=None):
    """Search crawled data by keyword, type, or relevance hint."""
    if not os.path.exists(SAVE_PATH):
        print("❌ No data found. Run crawl_igdtuw() first.")
        return []

    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for item in data:
        if keyword and keyword.lower() not in item["text"].lower():
            continue
        if content_type and item["type"] != content_type:
            continue
        if relevance and relevance.lower() not in item["relevance_hint"].lower():
            continue
        results.append(item)

    print(f"🔎 Found {len(results)} matching entries.")
    return results


if __name__ == "__main__":
    crawl_igdtuw()
