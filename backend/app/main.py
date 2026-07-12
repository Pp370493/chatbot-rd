from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Tuple
import os

from app.database import init_db, log_chat, get_admin_stats, get_all_logs
from app.rag_engine import (
    LocalThaiVATRetriever, 
    ThaiVATLLM, 
    rewrite_query, 
    check_out_of_scope, 
    detect_regulatory_conflicts
)

app = FastAPI(
    title="Thai Revenue Department VAT Registration Chatbot API",
    description="Decoupled local RAG system for checking VAT registration laws and regulations.",
    version="1.0.0"
)

# Enable CORS for the Next.js Frontend running on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB initialization
@app.on_event("startup")
def startup_event():
    init_db()

# Pydantic Schemas for Requests
class ChatHistoryItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    session_id: str
    query: str
    history: Optional[List[ChatHistoryItem]] = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        session_id = request.session_id
        original_query = request.query.strip()
        
        # 1. Format history list to the required format
        history_tuples = []
        if request.history:
            history_tuples = [(item.role, item.content) for item in request.history]
        
        # 2. Guardrails Check: Out-of-Scope Detection
        if check_out_of_scope(original_query):
            response_text = (
                "ขออภัยครับ ระบบนี้เป็นคลังความรู้สำหรับเจ้าหน้าที่กรมสรรพากรในการสืบค้นข้อมูล "
                "เฉพาะเกี่ยวกับการจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration) เท่านั้น "
                "คำถามของท่านไม่อยู่ในขอบเขต หรือเกี่ยวกับภาษี/บริการด้านอื่นที่ระบบยังไม่รองรับการให้บริการข้อมูลในขณะนี้"
            )
            # Log out-of-scope interaction (rewritten query is same as original)
            log_chat(
                session_id=session_id,
                original_query=original_query,
                rewritten_query=original_query,
                response=response_text,
                raw_laws=[],
                is_out_of_scope=True,
                detected_conflict=False
            )
            return {
                "session_id": session_id,
                "original_query": original_query,
                "rewritten_query": original_query,
                "response": response_text,
                "raw_laws": [],
                "is_out_of_scope": True,
                "detected_conflict": False
            }
            
        # 3. Query Re-writing based on Conversation Memory
        rewritten = rewrite_query(original_query, history_tuples)
        
        # 4. Search Local Vector Store (ChromaDB Simulation)
        retriever = LocalThaiVATRetriever()
        matched_docs = retriever._get_relevant_documents(rewritten, run_manager=None)
        
        # 5. Guardrails Check: Conflict Detection
        conflict_warning = detect_regulatory_conflicts(rewritten)
        has_conflict = conflict_warning is not None
        
        # 6. Generate Response using Custom Local LLM
        llm = ThaiVATLLM()
        response_text = llm.generate_response(rewritten, matched_docs, conflict_warning)
        
        # Extract raw law texts for the frontend's side injection panel
        raw_laws = []
        for doc in matched_docs:
            raw_laws.append({
                "title": doc.metadata["title"],
                "content": doc.page_content,
                "id": doc.metadata["id"]
            })
            
        # 7. Log interaction to SQLite Database
        log_chat(
            session_id=session_id,
            original_query=original_query,
            rewritten_query=rewritten,
            response=response_text,
            raw_laws=[f"{law['title']}: {law['content']}" for law in raw_laws],
            is_out_of_scope=False,
            detected_conflict=has_conflict
        )
        
        return {
            "session_id": session_id,
            "original_query": original_query,
            "rewritten_query": rewritten,
            "response": response_text,
            "raw_laws": raw_laws,
            "is_out_of_scope": False,
            "detected_conflict": has_conflict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผลระบบ RAG: {str(e)}")

@app.get("/api/stats")
async def stats_endpoint():
    try:
        stats = get_admin_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ไม่สามารถดึงข้อมูลสถิติได้: {str(e)}")

@app.post("/api/clear")
async def clear_logs_endpoint():
    """Endpoint for testing/admin purposes to reset database logs."""
    try:
        import sqlite3
        from app.database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        conn.commit()
        conn.close()
        
        # Re-initialize/re-seed if needed
        init_db()
        return {"status": "success", "message": "ล้างข้อมูลประวัติการสนทนาและสถิติการใช้งานเรียบร้อยแล้ว"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการล้างข้อมูล: {str(e)}")

@app.get("/api/logs")
async def logs_endpoint(limit: int = 50):
    """Endpoint for admin dashboard to retrieve a list of recent conversation logs."""
    try:
        logs = get_all_logs(limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ไม่สามารถดึงประวัติการสนทนาได้: {str(e)}")

@app.get("/api/laws")
async def laws_endpoint():
    """Endpoint for admin dashboard to retrieve the current vector store document records."""
    try:
        from app.rag_engine import LAWS_DATABASE
        return LAWS_DATABASE
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ไม่สามารถดึงคลังเอกสารกฎหมายได้: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
