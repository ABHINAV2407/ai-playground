from langchain_community.vectorstores import Chroma



from resume_rag import embedding_model

import chromadb

client = chromadb.CloudClient(
  api_key='ck-4PeGGpwXoieEMMg6nXivxQuAX6ww3yRefXuyEjL1z7Ka',
  tenant='35a54849-3cf4-4f3d-9ebf-5be93b04ab33',
  database='ProfileMatching'
)

def create_vector_store(texts, metadatas):
    vectordb = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        client=client,
        collection_name="resumes"
    )
    return vectordb


def load_db():
    return Chroma(
        client=client,   # ✅ use cloud
        collection_name="resumes",
        embedding_function=embedding_model
    )


def semantic_search(vectordb, job_description, k=10):
  return vectordb.similarity_search(job_description, k=k)

def hybrid_search(results, job_description):
  jd_keywords = ["Python", "SQL", "AWS", "Machine Learning"]

  scored = []

  for r in results:
      keyword_score = sum(
          1 for kw in jd_keywords if kw.lower() in r.page_content.lower()
      )

      scored.append((r, keyword_score))

  return sorted(scored, key=lambda x: x[1], reverse=True)


def compute_score(doc, keyword_score):
  base_score = 70
  keyword_weight = 5

  return min(100, base_score + keyword_score * keyword_weight)

def generate_reason(doc):
  return f"Matched skills: {doc.metadata.get('skills')} in {doc.metadata.get('section')}"

def match_candidates(job_description):
    db = load_db()
    results = semantic_search(db, job_description)

    hybrid = hybrid_search(results, job_description)

    candidate_map = {}

    for doc, keyword_score in hybrid:
        name = doc.metadata.get("name")

        if name not in candidate_map:
            candidate_map[name] = {
                "candidate_name": name,
                "resume_path": doc.metadata.get("source"),
                "match_score": 0,
                "matched_skills": set(),
                "relevant_excerpts": [],
                "reasoning": []
            }

        entry = candidate_map[name]

        score = compute_score(doc, keyword_score)
        entry["match_score"] = max(entry["match_score"], score)

        entry["matched_skills"].update(doc.metadata.get("skills", []))
        entry["relevant_excerpts"].append(doc.page_content[:200])
        entry["reasoning"].append(generate_reason(doc))

    # convert to list
    final_output = []
    for v in candidate_map.values():
        final_output.append({
            "candidate_name": v["candidate_name"],
            "resume_path": v["resume_path"],
            "match_score": v["match_score"],
            "matched_skills": list(v["matched_skills"]),
            "relevant_excerpts": v["relevant_excerpts"][:3],  # limit
            "reasoning": " | ".join(v["reasoning"][:2])
        })

    # sort by score
    final_output = sorted(final_output, key=lambda x: x["match_score"], reverse=True)

    return {
        "job_description": job_description,
        "top_matches": final_output[:10]
    }