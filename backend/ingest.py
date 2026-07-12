import os
import sys
import re
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 1. Establish file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "vat_laws_raw.txt")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

def ingest_data():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file missing at: {INPUT_FILE}")
        sys.exit(1)
        
    print("==================================================")
    # Step 2: Read raw data
    print("[Step 2] Reading extracted raw legal text...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    # Step 3: Precise Clause Chunking (Regex-based Splitting)
    # We split before every new clause "ข้อ X" or "ข้อ X/Y" to keep clauses whole.
    print("[Step 3] Splitting document by legal clauses (ข้อ)...")
    
    # Split using lookahead for "ข้อ "
    raw_chunks = re.split(r'(?=\n\s*(?:“?\s*ข้อ\s+\d+))', raw_text)
    
    documents = []
    chunk_index = 1
    
    for idx, chunk_text in enumerate(raw_chunks):
        cleaned_text = chunk_text.strip()
        if not cleaned_text:
            continue
            
        # Extract title automatically
        # For chunk 0 (usually the document header/title)
        if idx == 0 and "ข้อ" not in cleaned_text[:30]:
            title = "ประกาศอธิบดีกรมสรรพากร (ฉบับที่ 57) - บททั่วไป"
        else:
            # Find the clause number (e.g., "ข้อ 1", "ข้อ 4/1")
            clause_match = re.search(r'(?:ข้อ\s+\d+(?:/\d+)?)', cleaned_text)
            if clause_match:
                clause_name = clause_match.group(0)
                title = f"ประกาศอธิบดีกรมสรรพากร (ฉบับที่ 57) - {clause_name}"
            else:
                title = f"ประกาศอธิบดีกรมสรรพากร (ฉบับที่ 57) - ส่วนที่ {chunk_index}"
                
        # Generate clean documents
        doc = Document(
            page_content=cleaned_text,
            metadata={"id": f"clause_{chunk_index}", "title": title}
        )
        documents.append(doc)
        chunk_index += 1
        
    print(f"-> Generated {len(documents)} clean clause-level documents.")
    for doc in documents:
        print(f"   [+] Metadata Title: {doc.metadata['title']} ({len(doc.page_content)} chars)")

    # Step 4: Loading Embedding model locally (HuggingFace)
    embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    print(f"[Step 4] Loading Local Embedding model: {embedding_model_name}")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={'device': 'cpu'}
        )
    except Exception as e:
        print(f"[ERROR] Failed to load embedding model: {e}")
        print("Please check your internet connection (needed for the first download of model weights).")
        sys.exit(1)
        
    # Step 5: Initialize Chroma database and save vectors locally
    print("[Step 5] Compiling and saving vector embeddings into Chroma DB...")
    try:
        # Delete existing database to rebuild clean index
        if os.path.exists(DB_DIR):
            import shutil
            shutil.rmtree(DB_DIR)
            
        db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=DB_DIR
        )
        print("-> Vector Database built successfully from real DOCX text!")
        print(f"-> Saved data vectors in folder: {DB_DIR}")
        print("==================================================")
        print("[SUCCESS] Ingestion of real data complete! FastAPI will query this index immediately.")
    except Exception as e:
        print(f"[ERROR] Failed to compile Chroma database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_data()
