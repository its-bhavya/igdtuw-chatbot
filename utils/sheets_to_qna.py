import json
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIG ===
SERVICE_ACCOUNT_FILE = "credentials.json"  # path to your downloaded JSON
SPREADSHEET_ID = "1tS4uSqKedvGqCssTuXmhJFxspM9uHBvkLMBU_xULa6U"     # from your Google Sheets URL
OUTPUT_FILE = "qna_data.json"

# === SETUP GOOGLE SHEETS CONNECTION ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet_names = [s.title for s in spreadsheet.worksheets()]

all_qna = []

for name in sheet_names:
    print(f"📄 Reading sheet: {name}")
    sheet = spreadsheet.worksheet(name)

    values = sheet.get_all_values()

    if not values or len(values) < 2:
        print(f"⚠️  Skipping '{name}' — not enough data.")
        continue

    df = pd.DataFrame(values[1:], columns=values[0])  # treat first row as header
    if df.shape[1] < 2:
        print(f"⚠️  Skipping '{name}' — less than 2 columns.")
        continue

    # take last two columns as Q and A
    q_col, a_col = df.columns[-2], df.columns[-1]

    for _, row in df.iterrows():
        q = str(row[q_col]).strip()
        a = str(row[a_col]).strip()
        if q and a and q.lower() != "question" and a.lower() != "answer":
            all_qna.append({
                "sheet": name,
                "question": q,
                "answer": a
            })

# === SAVE COMBINED QNA DATA ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_qna, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(all_qna)} QnA pairs to {OUTPUT_FILE}")