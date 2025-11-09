import json

with open("web_content.json", "r", encoding="utf-8") as f:
    web_data = json.load(f)

# Keep only non-PDF entries
filtered_data = [item for item in web_data if item["type"] != "pdf"]

print(f"Removed {len(web_data) - len(filtered_data)} PDF entries.")
print(f"Remaining pages: {len(filtered_data)}")

with open("web_content_cleaned.json", "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=4, ensure_ascii=False)

