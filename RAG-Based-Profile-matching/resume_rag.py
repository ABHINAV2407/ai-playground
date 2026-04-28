from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import Chroma
import os

def load_resumes(folder_path):
  documents = []

  for file in os.listdir(folder_path):
      path = os.path.join(folder_path, file)

      if file.endswith(".pdf"):
          print(f"Loading PDF: {file}")
          print("============================================")
          loader = PyPDFLoader(path)
      elif file.endswith(".docx"):
          loader = Docx2txtLoader(path)
      else:
          continue

      docs = loader.load()
      for doc in docs:
          doc.metadata["source"] = path
      documents.extend(docs)

  return documents


def split_resume_sections(text):
  sections = ["Education", "Experience", "Skills", "Projects"]
  chunks = []

  current_section = "General"
  buffer = ""

  for line in text.split("\n"):
      if any(sec.lower() in line.lower() for sec in sections):
          if buffer:
              chunks.append((current_section, buffer))
          current_section = line.strip()
          buffer = ""
      else:
          buffer += line + "\n"

  if buffer:
      chunks.append((current_section, buffer))

  return chunks



embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

import re

import re

def extract_metadata(text):
    name = text.split("\n")[0]

    # ✅ Step 1: extract raw skills from text
    raw_skills = re.findall(r'Python|Java|SQL|Machine Learning|AWS', text, re.I)

    # ✅ Step 2: normalize (remove duplicates like JAVA vs Java)
    skills = list(set([s.capitalize() for s in raw_skills]))

    # ✅ Step 3: extract experience
    experience = re.findall(r'(\d+)\+?\s+years', text.lower())
    experience_years = max(map(int, experience)) if experience else 0

    # ✅ Step 4: extract education
    education = "B.Tech" if "b.tech" in text.lower() else ""

    return {
        "name": name,
        "skills": skills,
        "experience_years": experience_years,
        "education": education
    }



import chromadb
import os
from langchain_community.vectorstores import Chroma

# ✅ Create Cloud client ONCE
import chromadb

client = chromadb.CloudClient(
  api_key='ck-5xL3rbnCo1jED27Vk5Bqt3T96rdJLneofVb5bnpk7oga',
  tenant='35a54849-3cf4-4f3d-9ebf-5be93b04ab33',
  database='ProfileMatching'
)

def create_vector_store(documents):
    texts = []
    metadatas = []

    for doc in documents:
        sections = split_resume_sections(doc.page_content)
        meta = extract_metadata(doc.page_content)

        for section, content in sections:
            if len(content.strip()) < 20:
                continue

            texts.append(content)
            metadatas.append({
                **meta,
                "section": section,
                "source": doc.metadata["source"]
            })

    vectordb = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        client=client,                 # ✅ CLOUD
        collection_name="resumes"
    )

    return vectordb
