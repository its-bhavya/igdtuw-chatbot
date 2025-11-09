import os
from dotenv import load_dotenv
import chromadb
import google.generativeai as genai

# --- Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Connect to both collections
chroma_client = chromadb.PersistentClient(path="./vectorstore_web_gemini")

collection_web = chroma_client.get_or_create_collection("igdtuw_web")
collection_faq = chroma_client.get_or_create_collection("igdtuw_qna")

# --- Embedding helper ---
def get_gemini_embeddings(texts):
    embeddings = []
    for text in texts:
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text[:6000],
                task_type="retrieval_query"
            )
            embeddings.append(result["embedding"])
        except Exception as e:
            print(f"⚠️ Embedding failed: {e}")
            embeddings.append([0] * 768)
    return embeddings


# --- RAG Query ---
def rag_query(user_query, n_results=5):
    query_emb = get_gemini_embeddings([user_query])[0]

    # Query both collections
    res_web = collection_web.query(query_embeddings=[query_emb], n_results=n_results)
    res_faq = collection_faq.query(query_embeddings=[query_emb], n_results=n_results)

    # Combine results
    all_docs = []
    all_sources = []

    for doc, meta in zip(res_web["documents"][0], res_web["metadatas"][0]):
        all_docs.append(doc)
        all_sources.append(meta.get("url", "Web content"))

    for doc, meta in zip(res_faq["documents"][0], res_faq["metadatas"][0]):
        all_docs.append(doc)
        all_sources.append(meta.get("answer"))

    # Build context for Gemini
    combined_docs = "\n\n---\n\n".join(all_docs[:11])
    combined_sources = "\n\n---\n\n".join(all_sources[:11])
    combined_context = f"{combined_docs}\n\n---\n\n{combined_sources}"

    prompt = f"""
You are "IGDTUW Assist", an AI assistant built to help students, applicants, and faculty of 
Indira Gandhi Delhi Technical University for Women (IGDTUW). 
Respond conversationally but factually, keeping your answers concise, contextually relevant, and easy to read.

---

🎓 ROLE & STYLE
- You are knowledgeable about IGDTUW’s academics, admissions, campus life, facilities, events, rules, and official notices.
- Use a friendly, student-supportive tone — approachable but never informal.
- Avoid speculation. If the information isn’t in the context, say so politely (e.g., “That detail isn’t available in the current documents.”).
- When multiple documents overlap, merge their points smoothly instead of listing them.

---

📅 TEMPORAL UNDERSTANDING
- If a query involves time-sensitive data (e.g., placements, timetables, datesheets, holidays, admissions):
  - If the user **does not specify a year**, use the **most recent available year,  right now, starting from 2025 and going backwards** from the provided context.
  - If the user **specifies a year**, prioritize results from that year even if newer ones exist.
  - If multiple years appear, prefer the **most recent** but mention the year in your answer for clarity.

---

🔗 SOURCE HANDLING
- Each context block has a “Source” field — treat it as official or credible content.
- When answering, naturally reference the source type if relevant:
  - e.g., “According to the 2025 Placement Report...” or “As per the exam notice PDF...”

---

🧩 RESPONSE STRUCTURE
1. **Answer** → Clear and well-structured explanation, directly addressing the query.
2. **Contextual Merging** → Seamlessly integrate info from multiple sources without redundancy.
3. **Clarifications (if needed)** → Note any variations (e.g., “In 2023, timings were slightly different…”).
4. **(Optional)** → End with a short helpful tip if it makes sense (e.g., “You can check the latest updates on the IGDTUW website’s ‘Notices’ section.”).

---

⚠️ LIMITATIONS
- Do not hallucinate or assume details not in the given context.

---

Context:
{combined_context}

User question: {user_query}

Answer:

"""

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    return response.text, all_sources

