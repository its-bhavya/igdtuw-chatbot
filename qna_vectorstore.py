import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
import chromadb
import google.generativeai as genai

# --- Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./vectorstore_web_gemini")
collection = chroma_client.get_or_create_collection(
    name="igdtuw_qna",
    metadata={"source": "qna_data"}
)

# --- Load data ---
with open(r"igdtuw-data\json_data\qna_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"📄 Loaded {len(data)} qna entries.")

# --- Embedding helper ---
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
            print(f"⚠️ Skipping one text due to error: {e}")
            embeddings.append([0]*768)
    return embeddings

# --- Build Vector Store for Web Data ---
batch_size = 10
for i in tqdm(range(0, len(data), batch_size), desc="Building QnA Vector Store"):
    batch = data[i:i+batch_size]

    faq_texts = [
    f"Q: {q['question']}; A: {q['answer']}"
    for q in batch
]

    questions = [item["question"] for item in batch]
    answers = [item["answer"]for item in batch]
    faq_metadatas = [
        {
            "source": "faq",
            "question": q["question"],
            "answer": q["answer"]
        }
        for q in batch
    ]

    ids = [f"Q{i+j}" for j in range(len(batch))]

    embeddings = get_gemini_embeddings(faq_texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=faq_texts,
        metadatas=faq_metadatas
    )

print("✅ Gemini-based vector store saved at ./vectorstore_qna_gemini/")
