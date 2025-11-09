import os
import json
import re
from PyPDF2 import PdfReader
from tqdm import tqdm  # <-- progress bar

PDF_DIR = r"igdtuw-data\pdfs"           # Folder containing your PDFs
SAVE_PATH = r"igdtuw-data\json_data\pdf_texts.json"

def relevance_from_text(text):
    """Infer relevance from keywords in the text."""
    t = text.lower()
    if "exam" in t or "datesheet" in t:
        return "examination info"
    elif "admission" in t:
        return "admission info"
    elif "placement" in t:
        return "placement info"
    elif "result" in t:
        return "result notice"
    elif "circular" in t:
        return "university notice"
    else:
        return "general info"

def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        print(f"⚠️ Error reading {pdf_path}: {e}")
        return ""

def process_pdfs():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    pdf_data = []

    print(f"📂 Found {len(pdf_files)} PDFs. Starting extraction...\n")

    for fname in tqdm(pdf_files, desc="Extracting PDFs", unit="file"):
        full_path = os.path.join(PDF_DIR, fname)
        text = extract_text_from_pdf(full_path)
        if not text:
            continue

        title = text[:100].strip() or fname
        relevance = relevance_from_text(text)
        pdf_data.append({
            "path": full_path,
            "type": "pdf",
            "title": title[:80],
            "relevance_hint": relevance,
            "text": text[:15000]  # truncate large PDFs
        })

    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(pdf_data, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Done. Extracted {len(pdf_data)} PDFs successfully. Saved to {SAVE_PATH}")

if __name__ == "__main__":
    process_pdfs()
