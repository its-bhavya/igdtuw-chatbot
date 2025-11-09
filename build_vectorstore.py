import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
import chromadb
import google.generativeai as genai
import re

# --- Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./vectorstore_web_gemini")
collection = chroma_client.get_or_create_collection(
    name="igdtuw_web",
    metadata={"source": "web_and_pdfs"}
)

# --- Load merged content ---
with open(r"igdtuw-data\json_data\merged_content.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"📄 Loaded {len(data)} entries.")

# --- Embedding function ---
def get_gemini_embeddings(texts):
    embeddings = []
    for text in texts:
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text[:6000],
                task_type="retrieval_document"
            )
            embeddings.append(result["embedding"])
        except Exception as e:
            print(f"⚠️ Embedding failed: {e}")
            embeddings.append([0] * 768)
    return embeddings


# --- Build vectorstore safely ---
batch_size = 10
total_added = 0
year_pattern = re.compile(r"(20\d{2})")

for batch_start in tqdm(range(0, len(data), batch_size), desc="Building Vector Store"):
    batch = data[batch_start:batch_start + batch_size]

    valid_items = []
    for item in batch:
        text = item.get("text", "").strip()
        url = item.get("url", "")
        title = item.get("title")

        years = re.findall(year_pattern, url + title + text)
        latest_year = max(map(int, years)) if years else None

        # Keep both web pages and local igdtuw-data PDFs
        if text and (url.startswith("http") or "igdtuw-data" in url):
            valid_items.append(item)

    if not valid_items:
        continue

    texts = [item["text"] for item in valid_items]
    metadatas = [
        {
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "type": item.get("type", ""),
            "year": latest_year if latest_year else ""
        }
        for item in valid_items
    ]
    ids = [f"id_{batch_start + j}_{hash(item['url']) % 10000}" for j, item in enumerate(valid_items)]

    embeddings = get_gemini_embeddings(texts)
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    total_added += len(valid_items)

print(f"✅ Added {total_added} total documents (web + PDFs) to vectorstore.")
