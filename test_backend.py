import sys
import os
import json

# Add backend directory to path to import app files
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

try:
    from app.database import init_db, log_chat, get_admin_stats
    from app.rag_engine import (
        rewrite_query,
        check_out_of_scope,
        detect_regulatory_conflicts,
        LocalThaiVATRetriever,
        ThaiVATLLM
    )
except ImportError as e:
    print(f"[ERROR] Import failed. Please run requirements installation first. Error: {e}")
    sys.exit(1)

def run_tests():
    print("==================================================")
    print("  Running Local RAG System Backend Verification  ")
    print("==================================================")
    
    # 1. Initialize SQLite Database
    print("\n[Step 1] Initializing SQLite database and seeding...")
    init_db()
    stats_before = get_admin_stats()
    print(f"-> Seed database successful! Total logs registered: {stats_before['total_interactions']}")
    
    # 2. Test Conversation Query Re-writing
    print("\n[Step 2] Testing Conversation Memory Query Re-writing...")
    history = [
        ("user", "อยากสมัครจดทะเบียนภาษีมูลค่าเพิ่มครับ"),
        ("assistant", "คุณสามารถเตรียมแบบคำขอ ภ.พ.01 และยื่นออนไลน์ทางเว็บไซต์กรมสรรพากรได้ครับ")
    ]
    query1 = "ต้องเตรียมเอกสารอะไรบ้าง"
    rewritten1 = rewrite_query(query1, history)
    print(f"Original: '{query1}'")
    print(f"Rewritten: '{rewritten1}'")
    assert "เอกสาร" in rewritten1 and "จดทะเบียน" in rewritten1, "Query rewriting failed for documents"
    
    query2 = "ยื่นที่ช่องทางไหน"
    rewritten2 = rewrite_query(query2, history)
    print(f"Original: '{query2}'")
    print(f"Rewritten: '{rewritten2}'")
    assert "ช่องทาง" in rewritten2, "Query rewriting failed for channels"
    print("-> Query re-writing tests PASSED!")

    # 3. Test Out-of-Scope Guardrails
    print("\n[Step 3] Testing Out-of-Scope Guardrails...")
    in_scope_q = "รายได้ 2 ล้านบาท ต้องจดทะเบียน VAT หรือไม่"
    out_of_scope_q = "ขั้นตอนขอคืนภาษีท่องเที่ยวประชารัฐทำอย่างไร"
    
    is_in_scope_flag = check_out_of_scope(in_scope_q)
    is_out_of_scope_flag = check_out_of_scope(out_of_scope_q)
    
    print(f"In-scope test: '{in_scope_q}' -> Out-of-Scope? {is_in_scope_flag}")
    print(f"Out-of-scope test: '{out_of_scope_q}' -> Out-of-Scope? {is_out_of_scope_flag}")
    
    assert not is_in_scope_flag, "Should mark VAT query as in-scope"
    assert is_out_of_scope_flag, "Should mark tourism refund query as out-of-scope"
    print("-> Out-of-scope guardrail tests PASSED!")

    # 4. Test Regulatory Conflict Detection
    print("\n[Step 4] Testing Regulatory Conflict Detection...")
    conflict_q = "รายได้ไม่เกิน 1.8 ล้าน แต่อยากจด VAT ได้ไหม"
    conflict_warn = detect_regulatory_conflicts(conflict_q)
    print(f"Query: '{conflict_q}'")
    print(f"Warning detected:\n{conflict_warn}")
    assert conflict_warn is not None, "Should detect voluntary VAT registration conflict"
    print("-> Regulatory conflict detection tests PASSED!")

    # 5. Test Vector Retriever & LLM Summary
    print("\n[Step 5] Testing Vector Search (Retriever) & Local LLM...")
    retriever = LocalThaiVATRetriever()
    llm = ThaiVATLLM()
    
    docs = retriever._get_relevant_documents("เอกสารจดทะเบียน ภ.พ.01", run_manager=None)
    print(f"Vector search returned {len(docs)} documents.")
    for doc in docs:
        print(f" - Document Match: {doc.metadata['title']} (Score: {doc.metadata['score']})")
        
    response = llm.generate_response("เอกสารจดทะเบียน ภ.พ.01", docs, conflict_warn=None)
    print("\nLocal LLM Response generated (excerpt):")
    print("\n".join(response.split("\n")[:5]) + "\n...")
    
    assert len(docs) > 0, "Vector retriever should return document matches"
    assert "ภ.พ.01" in response or "เอกสาร" in response, "LLM response should cover documents"
    print("-> Local Vector Store & LLM tests PASSED!")

    # 6. Test Logging and Stat Aggregations
    print("\n[Step 6] Testing SQLite Database logging and statistics...")
    test_session = "test_sess_999"
    log_chat(
        session_id=test_session,
        original_query=in_scope_q,
        rewritten_query=in_scope_q,
        response="ผลทดสอบการจดทะเบียน VAT สำหรับรายได้ 2 ล้านบาท",
        raw_laws=["ประมวลรัษฎากร มาตรา 81/1: ผู้ประกอบการขายสินค้า..."],
        is_out_of_scope=False,
        detected_conflict=False
    )
    
    stats_after = get_admin_stats()
    print(f"Initial log count: {stats_before['total_interactions']}")
    print(f"Updated log count: {stats_after['total_interactions']}")
    assert stats_after["total_interactions"] == stats_before["total_interactions"] + 1, "Log insertion failed"
    print("-> Database logging and statistics tests PASSED!")

    print("\n==================================================")
    print("  ALL BACKEND TESTS PASSED SUCCESSFULLY! (100% OK) ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
