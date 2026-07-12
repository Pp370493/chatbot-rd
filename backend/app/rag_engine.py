import re
from typing import List, Optional, Mapping, Any, Tuple
from pydantic import Field
from langchain_core.language_models.llms import LLM
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document

# 1. Mock Local Vector Store Document Store
# Contains official VAT registration documents and regulations from the Thai Revenue Department.
LAWS_DATABASE = [
    {
        "id": "sec_81_1",
        "title": "ประมวลรัษฎากร มาตรา 81/1 (หน้าที่จดทะเบียนและการยกเว้น)",
        "content": "ผู้ประกอบการซึ่งประกอบกิจการขายสินค้าหรือให้บริการในทางธุรกิจที่มีรายรับไม่เกิน 1.8 ล้านบาทต่อปี ได้รับยกเว้นไม่ต้องเสียภาษีมูลค่าเพิ่ม แต่สามารถแจ้งความประสงค์ขอจดทะเบียนภาษีมูลค่าเพิ่มได้ตามที่อธิบดีกำหนด โดยมีสิทธิและหน้าที่เสมือนผู้จดทะเบียนทั่วไป",
        "keywords": ["1.8 ล้าน", "ยกเว้น", "รายรับ", "รายได้", "สมัครใจ", "บังคับ", "หน้าที่", "มาตรา 81/1"]
    },
    {
        "id": "sec_85",
        "title": "ประมวลรัษฎากร มาตรา 85 (กำหนดเวลายื่นคำขอ)",
        "content": "ผู้ประกอบการที่มีหน้าที่เสียภาษีมูลค่าเพิ่ม ต้องยื่นคำขอจดทะเบียนภาษีมูลค่าเพิ่มก่อนวันเริ่มประกอบกิจการ หรือภายใน 30 วันนับแต่วันที่รายรับจากการขายสินค้าหรือให้บริการเกินเกณฑ์ 1.8 ล้านบาทต่อปี",
        "keywords": ["กำหนดเวลา", "30 วัน", "ก่อนเริ่ม", "รายรับเกิน", "ล่าช้า", "เกินกำหนด", "มาตรา 85"]
    },
    {
        "id": "sec_85_3",
        "title": "ประมวลรัษฎากร มาตรา 85/3 (สถานที่และวิธีจดทะเบียน)",
        "content": "การยื่นคำขอจดทะเบียนภาษีมูลค่าเพิ่ม (แบบ ภ.พ.01) ให้ยื่น ณ สถานที่จดทะเบียนตามที่อธิบดีกำหนด หรือยื่นผ่านระบบอินเทอร์เน็ตทางเว็บไซต์ของกรมสรรพากร (www.rd.go.th)",
        "keywords": ["ภ.พ.01", "สถานที่", "อินเทอร์เน็ต", "rd.go.th", "ยื่นที่ไหน", "ช่องทาง", "แบบฟอร์ม", "มาตรา 85/3"]
    },
    {
        "id": "sec_89_1",
        "title": "ประมวลรัษฎากร มาตรา 89(1) (เบี้ยปรับกรณียื่นล่าช้า)",
        "content": "ผู้ประกอบการที่มีหน้าที่จดทะเบียนภาษีมูลค่าเพิ่ม แต่ประกอบกิจการโดยไม่ได้จดทะเบียนภายในกำหนดเวลา ต้องเสียเบี้ยปรับอีก 2 เท่าของเงินภาษีที่ต้องเสียในแต่ละเดือนภาษีตลอดระยะเวลาที่ไม่จดทะเบียน",
        "keywords": ["เบี้ยปรับ", "ค่าปรับ", "ไม่ได้จด", "สองเท่า", "เงินเพิ่ม", "มาตรา 89"]
    },
    {
        "id": "sec_90_2",
        "title": "ประมวลรัษฎากร มาตรา 90/2 (โทษทางอาญาสำหรับผู้ไม่จดทะเบียน)",
        "content": "ผู้ประกอบการซึ่งมีหน้าที่เสียภาษีมูลค่าเพิ่ม แต่ตั้งใจละเลยไม่ยื่นคำขอจดทะเบียนภาษีมูลค่าเพิ่มภายในกำหนดเวลา ต้องระวางโทษจำคุกไม่เกิน 1 เดือน หรือปรับไม่เกิน 2,000 บาท หรือทั้งจำทั้งปรับ",
        "keywords": ["โทษทางอาญา", "จำคุก", "ปรับเงิน", "ละเลย", "2,000 บาท", "มาตรา 90/2"]
    },
    {
        "id": "doc_require",
        "title": "ประกาศอธิบดีกรมสรรพากร (เอกสารหลักฐานประกอบการจดทะเบียน)",
        "content": "เอกสารที่ต้องเตรียมสำหรับยื่นจดทะเบียน ภ.พ.01 ได้แก่ 1. แบบ ภ.พ.01 จำนวน 3 ฉบับ 2. บัตรประชาชนผู้ประกอบการ/กรรมการ 3. สำเนาทะเบียนบ้านของสถานประกอบการ 4. แผนที่และภาพถ่ายสถานประกอบการที่มีป้ายชื่อชัดเจน 5. หนังสือยินยอมให้ใช้สถานที่หรือสัญญาเช่าในกรณีที่ไม่ได้เป็นเจ้าของกรรมสิทธิ์เอง",
        "keywords": ["เอกสาร", "หลักฐาน", "เตรียมอะไรบ้าง", "รูปถ่าย", "ทะเบียนบ้าน", "สัญญาเช่า", "ป้ายชื่อ", "ยินยอมให้ใช้สถานที่"]
    },
    {
        "id": "rule_cancellation",
        "title": "แนวทางปฏิบัติการยกเลิกใบจดทะเบียน VAT สมัครใจ",
        "content": "ผู้ประกอบการที่ขอจดทะเบียนภาษีมูลค่าเพิ่มโดยสมัครใจ (มีรายได้ต่ำกว่า 1.8 ล้านบาทต่อปี) จะยื่นคำขอยกเลิกการจดทะเบียนได้ก็ต่อเมื่อได้จดทะเบียนภาษีมูลค่าเพิ่มมาแล้วไม่น้อยกว่า 2 ปีภาษี เว้นแต่เป็นกรณีเลิกประกอบกิจการหรือโอนกิจการทั้งหมด",
        "keywords": ["ยกเลิก", "ออกจากระบบ", "ออก vat", "ยกเลิกจด", "สมัครใจ", "2 ปีภาษี", "ถอนตัว"]
    },
    {
        "id": "rule_duplicate",
        "title": "ระเบียบกรมสรรพากรเรื่องการจดทะเบียนสถานประกอบการซ้ำซ้อน",
        "content": "สถานประกอบการแห่งหนึ่งสามารถจดทะเบียนเป็นที่ตั้งหลักของบุคคลเดียวได้เท่านั้น ห้ามใช้สถานที่เดียวกันจดทะเบียนซ้ำซ้อนในนามบุคคลธรรมดาเดียวกัน หรือนิติบุคคลเดียวกันโดยไม่มีการแบ่งแยกสัดส่วนพื้นที่อย่างเด่นชัดทางกายภาพ",
        "keywords": ["ซ้ำซ้อน", "สถานที่เดิม", "บ้านเลขที่เดียวกัน", "จดซ้ำ", "สองคน", "แบ่งแยก"]
    }
]

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Paths for real database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# Global variables for real database instance
_embeddings_instance = None
_db_instance = None

def get_real_db():
    global _embeddings_instance, _db_instance
    if os.path.exists(DB_DIR):
        if _db_instance is None:
            try:
                print("[*] Detected real Chroma DB. Loading vector index...")
                _embeddings_instance = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    model_kwargs={'device': 'cpu'}
                )
                _db_instance = Chroma(
                    persist_directory=DB_DIR,
                    embedding_function=_embeddings_instance
                )
            except Exception as e:
                print(f"[WARNING] Failed to load real ChromaDB: {e}. Falling back to simulation.")
                return None
        return _db_instance
    return None

# 2. Local ChromaDB Simulation using Keyword Score Matching or Real Search
class LocalThaiVATRetriever(BaseRetriever):
    """Retrieves document chunks from real ChromaDB if available, otherwise falls back to keyword matching simulation."""
    
    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        real_db = get_real_db()
        if real_db is not None:
            # Query real database!
            print(f"[RAG] Querying real ChromaDB for: '{query}'")
            matched_docs = real_db.similarity_search(query, k=3)
            # Standardize document metadata structure for LLM and API compatibility
            results = []
            for doc in matched_docs:
                results.append(Document(
                    page_content=doc.page_content,
                    metadata={
                        "id": doc.metadata.get("id", "doc_chunk"),
                        "title": doc.metadata.get("title", "เอกสารกฎหมายอ้างอิง"),
                        "score": 5.0 # default score for similarity search
                    }
                ))
            return results
            
        # Graceful fallback: Check if the real extracted raw text file exists
        raw_text_path = os.path.join(BASE_DIR, "data", "vat_laws_raw.txt")
        if os.path.exists(raw_text_path):
            try:
                print(f"[RAG] Reading real raw laws file for search: {raw_text_path}")
                with open(raw_text_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                
                # Perform the same regex splitting on the fly (100% pure Python, no torch required!)
                import re
                raw_chunks = re.split(r'(?=\n\s*(?:“?\s*ข้อ\s+\d+))', raw_text)
                
                scored_real_docs = []
                chunk_index = 1
                normalized_query = query.lower()
                
                for chunk in raw_chunks:
                    cleaned_chunk = chunk.strip()
                    if not cleaned_chunk:
                        continue
                        
                    score = 0
                    
                    # Extract title and clause number
                    clause_match = re.search(r'(?:ข้อ\s+\d+(?:/\d+)?)', cleaned_chunk)
                    if clause_match:
                        clause_name = clause_match.group(0)
                        title = f"ประกาศอธิบดีกรมสรรพากร (ฉบับที่ 57) - {clause_name}"
                        # If query explicitly mentions the clause (e.g. "ข้อ 5" or "ข้อ5")
                        clause_num_only = clause_name.replace("ข้อ", "").strip()
                        if clause_name in normalized_query or f"ข้อ{clause_num_only}" in normalized_query:
                            score += 15 # huge boost
                    else:
                        title = "ประกาศอธิบดีกรมสรรพากร (ฉบับที่ 57) - บททั่วไป"
                    
                    # Score based on word and character trigram overlap
                    # 1. Trigram matching for Thai phrase compatibility
                    trigrams = [normalized_query[i:i+3] for i in range(len(normalized_query)-2)]
                    for tg in trigrams:
                        if tg in cleaned_chunk.lower():
                            score += 1
                            
                    # 2. Individual space/dot token matching
                    query_words = [w for w in re.split(r'[\s.()（）]+', normalized_query) if len(w) > 0]
                    for word in query_words:
                        if word in cleaned_chunk.lower():
                            score += 4
                            
                    # 3. Bonus for exact phrase matching
                    if normalized_query in cleaned_chunk.lower():
                        score += 12
                        
                    if score > 0:
                        scored_real_docs.append((score, title, cleaned_chunk, f"clause_{chunk_index}"))
                    chunk_index += 1
                
                # Sort and take top 3
                scored_real_docs.sort(key=lambda x: x[0], reverse=True)
                if scored_real_docs:
                    results = []
                    for score, title, content, doc_id in scored_real_docs[:3]:
                        results.append(Document(
                            page_content=content,
                            metadata={
                                "id": doc_id,
                                "title": title,
                                "score": float(score)
                            }
                        ))
                    return results
            except Exception as e:
                print(f"[WARNING] Pure-Python fallback search failed: {e}. Falling back to default simulation.")

        # Graceful fallback simulation to hardcoded database if raw file is not present
        print(f"[RAG] ChromaDB and raw file not found. Falling back to default keyword search simulation.")
        scored_docs = []
        normalized_query = query.lower()
        
        for doc in LAWS_DATABASE:
            score = 0
            # Calculate match score based on keyword hits in the query
            for kw in doc["keywords"]:
                if kw.lower() in normalized_query:
                    score += 3
            # Bonus score if term matches in content or title
            if any(term in normalized_query for term in doc["title"].lower().split()):
                score += 2
            
            # Simple word overlap match
            for word in normalized_query.split():
                if len(word) > 2 and word in doc["content"].lower():
                    score += 1
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score descending and return top matches (max 3)
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = [
            Document(
                page_content=doc["content"],
                metadata={"id": doc["id"], "title": doc["title"], "score": score}
            )
            for score, doc in scored_docs[:3]
        ]
        return top_docs

# 3. Conversation Memory Query Re-writer Logic (Local Mock)
def rewrite_query(query: str, history: List[Tuple[str, str]]) -> str:
    """
    If there is conversation history, reformulates the follow-up query to include context.
    E.g. Q1: 'อยากจดทะเบียน VAT' -> Q2: 'ต้องใช้เอกสารอะไรบ้าง' 
    Rewritten Q2: 'เอกสารที่ต้องใช้ในการจดทะเบียนภาษีมูลค่าเพิ่ม (VAT)'
    """
    if not history:
        return query
    
    # Extract previous user questions to establish context
    prev_user_queries = [h[1] for h in history if h[0] == "user"]
    if not prev_user_queries:
        return query
    
    last_context = prev_user_queries[-1].lower()
    
    # Identify dependencies in the query
    documents_triggers = ["เอกสาร", "หลักฐาน", "เตรียมอะไร", "ใช้อะไร", "ใช้ตัวไหน"]
    channels_triggers = ["ยื่นที่ไหน", "ช่องทาง", "ยื่นช่องทางไหน", "ยื่นยังไง", "จดที่ไหน", "จดช่องทางไหน"]
    timeline_triggers = ["กี่วัน", "เวลา", "ล่าช้า", "ปรับ", "เมื่อไหร่", "ตอนไหน", "กำหนดเวลา"]
    cancel_triggers = ["ยกเลิก", "ลาออก", "ยกเลิกจด", "ถอนตัว"]
    
    # Determine what context was previously asked
    context_vat = "จดทะเบียนภาษีมูลค่าเพิ่ม (VAT)"
    if "ยกเลิก" in last_context:
        context_vat = "ยกเลิกการจดทะเบียนภาษีมูลค่าเพิ่ม (VAT)"
    
    query_lower = query.lower()
    
    # Query re-writing rules
    if any(t in query_lower for t in documents_triggers) and "จดทะเบียน" not in query_lower:
        return f"เอกสารหลักฐานที่ต้องเตรียมในการ{context_vat}"
    elif any(t in query_lower for t in channels_triggers) and "จดทะเบียน" not in query_lower:
        return f"ช่องทางและสถานที่ในการ{context_vat}"
    elif any(t in query_lower for t in timeline_triggers) and "จดทะเบียน" not in query_lower:
        return f"กำหนดเวลาและโทษกรณีล่าช้าในการ{context_vat}"
    elif any(t in query_lower for t in cancel_triggers) and "จดทะเบียน" not in query_lower:
        return f"การขออนุมัติยกเลิกจดทะเบียนภาษีมูลค่าเพิ่ม (VAT)"
        
    return query

# 4. Out-of-Scope Guardrails
# Defines valid keywords for VAT registration. If not found, flags as Out-of-Scope.
IN_SCOPE_KEYWORDS = [
    "vat", "ภาษีมูลค่าเพิ่ม", "จดทะเบียน", "จดvat", "ภ.พ.01", "ภพ01", "1.8 ล้าน", "1,800,000", 
    "รายรับ", "รายได้", "สมัครใจ", "บังคับ", "เอกสาร", "หลักฐาน", "ช่องทาง", "ยื่น", "อินเทอร์เน็ต", 
    "เว็บไซต์", "ล่าช้า", "ปรับ", "โทษ", "อาญา", "ซ้ำซ้อน", "ยกเลิก", "พื้นที่สาขา", "กรมสรรพากร"
]

def check_out_of_scope(query: str) -> bool:
    normalized = query.lower()
    # Check if any in-scope keywords match
    if any(kw in normalized for kw in IN_SCOPE_KEYWORDS):
        return False
        
    # Check specifically for known out-of-scope topics
    out_of_scope_patterns = [
        "ภ.ง.ด", "ภงด", "บุคคลธรรมดา", "ภาษีเงินได้", "ภาษีมรดก", "ท่องเที่ยวประชารัฐ", 
        "สมัครงาน", "รับสมัคร", "สอบสวน", "น้ำมัน", "ภาษีสรรพสามิต", "จดทะเบียนบริษัท", "กรมพัฒนาธุรกิจ"
    ]
    if any(p in normalized for p in out_of_scope_patterns):
        return True
        
    # If it's a general greeting or short input, let it pass to LLM response rules
    if len(normalized.strip()) < 5:
        return False
        
    # Otherwise check overlap
    return True

# 5. Regulatory Conflict Detection Logic
# Detects scenarios with conflicting legal rules or operational confusion.
def detect_regulatory_conflicts(query: str) -> Optional[str]:
    normalized = query.lower()
    
    # Scenario A: Voluntary registration vs Revenue limit
    if ("ไม่ถึง" in normalized or "ไม่เกิน" in normalized or "1.2" in normalized or "น้อยกว่า" in normalized) and ("สมัครใจ" in normalized or "จดได้ไหม" in normalized or "จด vat" in normalized):
        return (
            "⚠️ **ตรวจพบข้อขัดแย้งของกฎระเบียบ (ประเด็น: รายได้ไม่ถึงเกณฑ์แต่ขอจดทะเบียน)**\n"
            "ตามประมวลรัษฎากร มาตรา 81/1 ผู้ประกอบการรายรับไม่ถึง 1.8 ล้านบาท/ปี ได้รับยกเว้นภาษีมูลค่าเพิ่ม "
            "แต่หากแจ้งความประสงค์ขอจดทะเบียนโดยสมัครใจ จะเกิดภาระภาษีหน้าที่ยื่นแบบ ภ.พ.30 ทุกเดือน แม้ไม่มีรายได้เลย "
            "และมีข้อผูกมัดทางปฏิบัติที่ห้ามขอยกเลิกจนกว่าจะจดทะเบียนมาแล้วไม่น้อยกว่า 2 ปีภาษี"
        )
        
    # Scenario B: Cancelling voluntary registration
    if ("ยกเลิก" in normalized or "ออกจาก" in normalized) and ("สมัครใจ" in normalized or "ไม่ถึง" in normalized or "2 ปี" in normalized):
        return (
            "⚠️ **ตรวจพบข้อขัดแย้งของกฎระเบียบ (ประเด็น: เงื่อนไขเวลาการขอยกเลิกจดทะเบียน)**\n"
            "ผู้ประกอบการที่จดทะเบียนโดยสมัครใจ (มาตรา 81/1) ไม่สามารถยื่นขอยกเลิกจดทะเบียนเมื่อใดก็ได้ "
            "ระเบียบกรมสรรพากรกำหนดให้ต้องเป็นผู้จดทะเบียนแล้วไม่น้อยกว่า 2 ปีภาษีจึงจะยื่น ภ.พ.08 ขอยกเลิกได้ "
            "ข้อยกเว้นเพียงอย่างเดียวคือ เลิกประกอบกิจการหรือโอนกิจการทั้งหมด"
        )
        
    # Scenario C: Double registration at the same location
    if "ซ้ำซ้อน" in normalized or "สถานที่เดียวกัน" in normalized or "บ้านเลขที่เดียวกัน" in normalized or "จดสองรอบ" in normalized:
        return (
            "⚠️ **ตรวจพบข้อขัดแย้งของกฎระเบียบ (ประเด็น: สถานที่ตั้งซ้ำซ้อน)**\n"
            "ตามแนวทางปฏิบัติของเจ้าหน้าที่ สรรพากรพื้นที่จะตรวจสอบความทับซ้อนของที่ตั้งสถานประกอบการ "
            "หากเป็นการจดทะเบียนซ้ำซ้อนในนามบุคคลเดิม ณ สถานที่ตั้งเดิมจะไม่สามารถทำได้ "
            "แต่หากเป็นคนละนิติบุคคลจดทะเบียนในที่เดียวกัน ต้องมีสัญญายินยอมแบ่งแยกส่วนพื้นที่อย่างชัดเจน "
            "เพื่อป้องกันข้อหาจัดตั้งโครงสร้างหลบเลี่ยงภาษี"
        )
        
    # Scenario D: Compulsory registration timeline vs Penalties
    if "เกิน 30 วัน" in normalized or "จดช้า" in normalized or "ไม่ได้จดภายใน" in normalized:
        return (
            "⚠️ **ตรวจพบข้อขัดแย้งของกฎระเบียบ (ประเด็น: ยื่นจดทะเบียนล่าช้ากว่ากำหนด)**\n"
            "เมื่อรายรับเกิน 1.8 ล้านบาท เกิดหน้าที่ทันทีตามกฎหมายที่จะต้องจดทะเบียนภายใน 30 วัน (มาตรา 85) "
            "หากประกอบกิจการต่อโดยไม่ยื่นคำขอจดทะเบียน จะขัดแย้งกับระเบียบการงดเบี้ยปรับ "
            "ผู้ประกอบการจะต้องรับโทษปรับอาญา และรับผิดเบี้ยปรับ 2 เท่าของเงินภาษีที่คำนวณย้อนหลังตั้งแต่วันที่พ้นกำหนด 30 วัน"
        )
        
    return None

# 6. Custom Local LLM Simulation wrapping LangChain API
class ThaiVATLLM(LLM):
    """
    A 100% local, secure LLM simulation class that integrates with LangChain.
    Produces highly structured answers, simulates system reasoning, and checks guardrails.
    """
    
    # Fields declared for pydantic compatibility in LangChain
    model_name: str = Field(default="Local-ThaiVAT-Intelligence-Engine")
    
    @property
    def _llm_type(self) -> str:
        return "custom_local_vat_llm"
        
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        # Prompt analysis can extract query if structured by a Chain, 
        # or we fallback to matching. In this system, the API will call the parser directly.
        return "Custom Local LLM generation output"

    def generate_response(self, query: str, retrieved_docs: List[Document], conflict_warn: Optional[str]) -> str:
        """Generates detailed, concise, and professional answers for Thai tax officers."""
        normalized = query.lower()
        
        # Build document context text
        context_str = "\n".join([f"- {doc.metadata['title']}: {doc.page_content}" for doc in retrieved_docs])
        
        # Rule-based generator mimicking local LLM output for accuracy
        response = ""
        
        if conflict_warn:
            response += f"{conflict_warn}\n\n"
            
        # 1. Ask about documents
        if "เอกสาร" in normalized or "หลักฐาน" in normalized or "เตรียมอะไร" in normalized:
            response += (
                "**สรุปขั้นตอนและเอกสารสำหรับผู้ประกอบการ:**\n"
                "ในการยื่นจดทะเบียนภาษีมูลค่าเพิ่ม (แบบ ภ.พ.01) เจ้าหน้าที่ต้องแนะนำให้ผู้ประกอบการจัดเตรียมเอกสารหลักฐานดังนี้:\n"
                "1. **แบบคำขอจดทะเบียน ภ.พ.01** จำนวน 3 ฉบับ (ต้องกรอกข้อมูลให้ครบถ้วนพร้อมลงลายมือชื่อ)\n"
                "2. **เอกสารแสดงตัวตน:**\n"
                "   - กรณีบุคคลธรรมดา: สำเนาบัตรประชาชน และสำเนาทะเบียนบ้านของผู้ประกอบการ\n"
                "   - กรณีนิติบุคคล: หนังสือรับรองการจดทะเบียนหุ้นส่วนบริษัท (ไม่เกิน 6 เดือน) พร้อมสำเนาบัตรประชาชนและทะเบียนบ้านของกรรมการผู้มีอำนาจ\n"
                "3. **เอกสารที่ตั้งสถานประกอบการ:**\n"
                "   - สำเนาทะเบียนบ้านของอาคารที่ตั้งสถานประกอบการ\n"
                "   - สัญญาเช่าอาคาร หรือหนังสือยินยอมให้ใช้เป็นสถานที่ประกอบกิจการ (กรณีไม่ได้เป็นเจ้าของ)\n"
                "   - แผนที่แสดงที่ตั้งโดยสังเขป\n"
                "   - ภาพถ่ายของสถานประกอบการที่แสดงเห็นเลขที่บ้านและป้ายชื่อร้าน/บริษัทชัดเจน\n\n"
                "💡 *คำแนะนำเพิ่มเติมสำหรับเจ้าหน้าที่:* ให้ตรวจสอบภาพถ่ายสถานที่ว่ามีสภาพพร้อมประกอบกิจการจริงหรือไม่ เพื่อป้องกันการจดทะเบียนในลักษณะนอมินี"
            )
        
        # 2. Ask about revenue threshold (1.8 Million)
        elif "1.8" in normalized or "ล้าน" in normalized or "เกณฑ์" in normalized or "รายได้" in normalized:
            response += (
                "**เกณฑ์การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration Criteria):**\n"
                "1. **กรณีภาคบังคับ (Mandatory):** ผู้ประกอบการที่มีรายรับจากการขายสินค้าหรือให้บริการเกินกว่า **1.8 ล้านบาทต่อปี** มีหน้าที่ต้องจดทะเบียนภาษีมูลค่าเพิ่มภายใน 30 วันนับแต่วันที่รายรับเกินเกณฑ์ดังกล่าว\n"
                "2. **กรณีสมัครใจ (Voluntary):** ผู้ประกอบการที่มีรายรับไม่ถึง 1.8 ล้านบาทต่อปี หรือประกอบกิจการที่ได้รับยกเว้น VAT ตามกฎหมาย (เช่น ขายพืชผลทางการเกษตร, หนังสือ) มีสิทธิขอจดทะเบียนเข้าสู่ระบบ VAT ได้โดยสมัครใจ\n\n"
                "💡 *หมายเหตุ:* กฎหมายไม่ได้บังคับจดทะเบียนสำหรับผู้ที่มีรายได้ไม่ถึง 1.8 ล้านบาท แต่หากต้องการสิทธิในการเคลมภาษีซื้อ สามารถขอยื่นแบบ ภ.พ.01.1 เพื่อเข้าสู่ระบบได้"
            )
            
        # 3. Ask about timeline and delay penalties
        elif "กี่วัน" in normalized or "วัน" in normalized or "กำหนดเวลา" in normalized or "ล่าช้า" in normalized or "ปรับ" in normalized:
            response += (
                "**กำหนดเวลาและบทลงโทษกรณีจดทะเบียนภาษีมูลค่าเพิ่มล่าช้า:**\n"
                "ตามประมวลรัษฎากร ผู้มีรายรับเกินเกณฑ์ต้องยื่นคำขอจดทะเบียนภายใน **30 วัน** นับแต่วันที่รายรับเกิน 1.8 ล้านบาท\n"
                "**บทลงโทษกรณีเกินกำหนดเวลา:**\n"
                "1. **ค่าปรับทางอาญา:** ระวางโทษจำคุกไม่เกิน 1 เดือน หรือปรับไม่เกิน 2,000 บาท หรือทั้งจำทั้งปรับ (ตามมาตรา 90/2)\n"
                "2. **เบี้ยปรับ:** ต้องเสียเบี้ยปรับ 2 เท่าของเงินภาษีที่ต้องเสียในแต่ละเดือนภาษี นับตั้งแต่วันที่ต้องยื่นจดทะเบียนจนถึงวันที่จดทะเบียนสำเร็จ (ตามมาตรา 89(1))\n"
                "3. **เงินเพิ่ม:** ดอกเบี้ยปรับร้อยละ 1.5 ต่อเดือน ของเงินภาษีที่ต้องชำระ (เศษของเดือนคิดเป็น 1 เดือน)\n\n"
                "💡 *คำแนะนำเจ้าหน้าที่:* แนะนำให้ผู้ประกอบการรีบยื่นจดทะเบียนทันทีที่รายได้แตะเกณฑ์ เพื่อลดหย่อนภาระเบี้ยปรับย้อนหลัง"
            )
            
        # 4. Ask about location and online/offline channels
        elif "ยื่นที่ไหน" in normalized or "ช่องทาง" in normalized or "ยื่นยังไง" in normalized or "จดที่ไหน" in normalized or "เว็บไซต์" in normalized:
            response += (
                "**สถานที่และช่องทางการยื่นจดทะเบียนภาษีมูลค่าเพิ่ม:**\n"
                "ผู้ประกอบการสามารถเลือกยื่นแบบ ภ.พ.01 ได้ 2 ช่องทางดังนี้:\n"
                "1. **ช่องทางออนไลน์ (แนะนำ):** ยื่นผ่านระบบ e-Registration บนเว็บไซต์ของกรมสรรพากร (www.rd.go.th) ได้ตลอด 24 ชั่วโมง โดยจะได้รับการอนุมัติและออกใบทะเบียนภาษีมูลค่าเพิ่ม (ภ.พ.20) รวดเร็วกว่า\n"
                "2. **ยื่น ณ สำนักงานสรรพากรพื้นที่:** ยื่นด้วยกระดาษ ณ สำนักงานสรรพากรพื้นที่สาขา ที่สถานประกอบการตั้งอยู่ (กรณีมีสถานประกอบการหลายแห่ง ให้ยื่น ณ สรรพากรพื้นที่ที่สำนักงานใหญ่ตั้งอยู่)\n\n"
                "💡 *สิทธิ์สำหรับผู้ประกอบการ:* การยื่นออนไลน์เปิดสิทธิ์ให้ทำรายการได้ทันทีโดยไม่ต้องส่งเอกสารทางกระดาษ เว้นแต่เจ้าหน้าที่จะขอสืบค้นเพิ่มเติม"
            )
            
        # 5. Ask about cancellation
        elif "ยกเลิก" in normalized or "ถอนตัว" in normalized or "ออก" in normalized:
            response += (
                "**การขอยกเลิกจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Cancellation):**\n"
                "การยกเลิกใบทะเบียน สามารถแบ่งออกตามลักษณะการจดทะเบียนได้ดังนี้:\n"
                "1. **จดทะเบียนโดยบังคับ (รายรับเกิน 1.8 ล้าน):** สามารถขอยกเลิกจดทะเบียน (ยื่นแบบ ภ.พ.08) ได้หากรายรับลดลงต่ำกว่า 1.8 ล้านบาทต่อปี ติดต่อกันเป็นเวลาไม่น้อยกว่า 3 ปีภาษี\n"
                "2. **จดทะเบียนโดยสมัครใจ (รายรับไม่ถึง 1.8 ล้าน):** สามารถขอยกเลิกจดทะเบียนได้เมื่อเป็นผู้ประกอบการจดทะเบียนแล้วไม่น้อยกว่า 2 ปีภาษี\n"
                "3. **เลิกกิจการหรือโอนกิจการ:** สามารถยื่นแบบ ภ.พ.08 ขอยกเลิกได้ทันทีภายใน 15 วันนับแต่วันเลิกหรือโอนกิจการ\n\n"
                "💡 *ข้อควรระวัง:* ระหว่างที่ยังไม่ได้รับการอนุมัติยกเลิก ผู้ประกอบการยังมีหน้าที่ต้องยื่นแบบ ภ.พ.30 ทุกเดือน"
            )
            
        # 6. Default fallback response on VAT topics
        else:
            response += (
                "**ข้อมูลการจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration Info):**\n"
                "การจดทะเบียนภาษีมูลค่าเพิ่มเป็นหน้าที่ทางกฎหมายของผู้ประกอบการไทยเมื่อมีรายรับเกินเกณฑ์ 1.8 ล้านบาทต่อปี "
                "กรุณาระบุหัวข้อที่เจ้าหน้าที่ต้องการตรวจสอบ เช่น:\n"
                "- *'เอกสารที่ต้องใช้'* เพื่อเรียกดูรายการแบบฟอร์ม ภ.พ.01 และหลักฐานที่ตั้งประกอบ\n"
                "- *'จดทะเบียนล่าช้า'* เพื่อดูการคำนวณเบี้ยปรับ 2 เท่า และโทษอาญา\n"
                "- *'ยื่นจดทะเบียนช่องทางใด'* เพื่อดูรายละเอียดการยื่นผ่านอินเทอร์เน็ตบนหน้าเว็บสรรพากร\n"
                "- *'จดทะเบียนซ้ำซ้อน'* เพื่อประเมินประเด็นข้อระเบียบข้อขัดแย้งของสถานที่ตั้งสถานประกอบการ"
            )
            
        # Append retrieved reference log warning to guide officer
        if context_str:
            response += f"\n\n---\n🔎 **เอกสารกฎหมายอ้างอิงที่สืบค้นได้จาก Vector Store:**\n{context_str}"
            
        return response
