import json


# Load web and pdf data
with open(r"igdtuw-data\json_data\web_content.json", "r", encoding="utf-8") as f:
    web_data = json.load(f)
with open(r"igdtuw-data\json_data\pdf_texts.json", "r", encoding="utf-8") as f:
    pdf_data = json.load(f)

for item in pdf_data:
    if "path" in item:
        item["url"] = item.pop("path")

# --- Filter web_data to remove unwanted PDFs ---
filtered_web_data = [
    item for item in web_data
    if not (item.get("url", "").startswith("https://www.igdtuw.ac.in/IGDTUW/uploads/") and item.get("url", "").endswith(".pdf"))
]

print(f"Removed {len(web_data) - len(filtered_web_data)} unwanted PDF entries from web_content.json")

# Merge filtered web data with pdf data
merged = filtered_web_data + pdf_data

# Save the merged content
with open(r"igdtuw-data\json_data\merged_content.json", "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=4, ensure_ascii=False)

print(f"Merged total entries: {len(merged)}")
