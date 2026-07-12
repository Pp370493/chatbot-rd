import os
import sqlite3
import json
from datetime import datetime

# Path to SQLite database file in the same directory as backend
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chatbot_logs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and seeds it with mock records if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            original_query TEXT NOT NULL,
            rewritten_query TEXT,
            response TEXT NOT NULL,
            raw_laws TEXT,
            is_out_of_scope INTEGER NOT NULL DEFAULT 0,
            detected_conflict INTEGER NOT NULL DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Check if empty, and seed data for premium experience
    cursor.execute("SELECT COUNT(*) FROM logs")
    count = cursor.fetchone()[0]
    
    if count == 0:
        seed_data = [
            # In-Scope Logs
            ("sess_001", "อยากจดทะเบียนภาษีมูลค่าเพิ่ม ต้องใช้เอกสารอะไรบ้างครับ", "เอกสารที่ใช้จดทะเบียนภาษีมูลค่าเพิ่ม VAT", 
             "เอกสารที่ต้องใช้ในการจดทะเบียนภาษีมูลค่าเพิ่มสำหรับบุคคลธรรมดาและนิติบุคคล ได้แก่ 1. แบบคำขอจดทะเบียน ภ.พ.01 จำนวน 3 ฉบับ 2. สำเนาบัตรประชาชนผู้ประกอบการ/กรรมการ 3. สำเนาทะเบียนบ้านของสถานประกอบการ 4. แผนที่ตั้งของสถานประกอบการ 5. ภาพถ่ายสถานประกอบการพร้อมป้ายชื่อ และ 6. หนังสือยินยอมให้ใช้สถานที่หรือสัญญาเช่า (ถ้ามี)", 
             json.dumps(["มาตรา 85/3 ผู้ประกอบการจดทะเบียนต้องยื่นคำขอจดทะเบียนภาษีมูลค่าเพิ่มตามแบบที่อธิบดีกำหนด (ภ.พ.01)", "ประกาศอธิบดีกรมสรรพากรเกี่ยวกับภาษีมูลค่าเพิ่ม (ฉบับที่ 2) เรื่องกำหนดหลักเกณฑ์ วิธีการ และเงื่อนไขการจดทะเบียน"]), 0, 0),
            
            ("sess_001", "ยื่นจดทะเบียนได้ที่ช่องทางไหนบ้าง", "ช่องทางและสถานที่ในการยื่นจดทะเบียนภาษีมูลค่าเพิ่ม VAT", 
             "คุณสามารถยื่นขอจดทะเบียนภาษีมูลค่าเพิ่มได้ 2 ช่องทางหลัก: 1. ยื่นผ่านอินเทอร์เน็ตทางเว็บไซต์ของกรมสรรพากร (www.rd.go.th) ตลอด 24 ชั่วโมง ซึ่งเป็นวิธีที่สะดวกและแนะนำที่สุด 2. ยื่นด้วยกระดาษ ณ สำนักงานสรรพากรพื้นที่สาขาที่สถานประกอบการตั้งอยู่", 
             json.dumps(["มาตรา 85/3 ยื่น ณ สถานที่จดทะเบียนภาษีมูลค่าเพิ่มตามที่อธิบดีกำหนด", "คำชี้แจงกรมสรรพากร เรื่องการจดทะเบียนภาษีมูลค่าเพิ่มผ่านระบบอินเทอร์เน็ต"]), 0, 0),
            
            ("sess_002", "บริษัทรายได้เท่าไหร่ถึงต้องจด VAT ครับ", "เกณฑ์รายได้บังคับจดทะเบียนภาษีมูลค่าเพิ่ม VAT", 
             "ผู้ประกอบการที่มีรายได้จากการขายสินค้าหรือให้บริการเกินกว่า 1.8 ล้านบาทต่อปี มีหน้าที่ต้องยื่นขอจดทะเบียนภาษีมูลค่าเพิ่ม หากรายได้ยังไม่เกินเกณฑ์ก็สามารถเลือกจดทะเบียนโดยสมัครใจได้เช่นกัน", 
             json.dumps(["มาตรา 81/1 ผู้ประกอบการซึ่งประกอบกิจการขายสินค้าหรือให้บริการในทางธุรกิจที่มีรายรับไม่เกิน 1.8 ล้านบาทต่อปี ได้รับยกเว้นไม่ต้องเสียภาษีมูลค่าเพิ่ม แต่สามารถแจ้งความประสงค์ขอจดทะเบียนได้"]), 0, 0),

            ("sess_003", "ถ้าจดทะเบียน VAT ล่าช้า จะโดนค่าปรับอย่างไรบ้าง", "โทษและเบี้ยปรับในการจดทะเบียนภาษีมูลค่าเพิ่มล่าช้า", 
             "หากประกอบกิจการเกินเกณฑ์ 1.8 ล้านบาทแล้วไม่ยื่นจดทะเบียนภายใน 30 วัน จะมีโทษดังนี้: 1. เบี้ยปรับ 2 เท่าของเงินภาษีที่ต้องเสียในแต่ละเดือนภาษี 2. เงินเพิ่มร้อยละ 1.5 ต่อเดือนของภาษีที่ต้องชำระ 3. โทษทางอาญา ปรับไม่เกิน 2,000 บาท หรือจำคุกไม่เกิน 1 เดือน หรือทั้งจำทั้งปรับ", 
             json.dumps(["มาตรา 89(1) เบี้ยปรับสองเท่าของเงินภาษีที่ต้องเสีย", "มาตรา 90/2 ผู้ประกอบการที่ไม่ยื่นขอจดทะเบียนภาษีมูลค่าเพิ่มภายในกำหนดเวลา ต้องระวางโทษจำคุกไม่เกินหนึ่งเดือน หรือปรับไม่เกินสองพันบาท หรือทั้งจำทั้งปรับ"]), 0, 0),

            ("sess_003", "แล้วถ้ารายได้ 1.2 ล้าน แต่อยากจด VAT ได้ไหม", "รายได้ไม่เกิน 1.8 ล้านสามารถขอจดทะเบียนภาษีมูลค่าเพิ่มได้หรือไม่", 
             "ผู้ประกอบการที่มีรายรับไม่เกิน 1.8 ล้านบาทต่อปี ได้รับการยกเว้น VAT แต่มีสิทธิขอจดทะเบียนภาษีมูลค่าเพิ่มโดยสมัครใจได้ตามมาตรา 81/1 โดยให้ยื่นแบบ ภ.พ.01.1 หรือแจ้งความประสงค์ และจะมีหน้าที่และสิทธิเสมือนผู้จดทะเบียนทั่วไปทันที", 
             json.dumps(["มาตรา 81/1 ผู้ประกอบการซึ่งประกอบกิจการขายสินค้าหรือให้บริการ... มีรายรับไม่เกินเกณฑ์ ได้รับยกเว้น... แต่สามารถยื่นคำขอจดทะเบียนภาษีมูลค่าเพิ่มได้"]), 0, 0),

            # Out-of-Scope Logs
            ("sess_004", "วิธียื่นภาษีเงินได้บุคคลธรรมดา ภ.ง.ด.90 ทำยังไงครับ", "วิธียื่นภาษีเงินได้บุคคลธรรมดา ภ.ง.ด.90", 
             "ขออภัยครับ ระบบนี้ให้บริการข้อมูลและตอบคำถามเฉพาะเรื่อง 'การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration)' เท่านั้น หากท่านต้องการสอบถามข้อมูลเกี่ยวกับภาษีเงินได้บุคคลธรรมดา (ภ.ง.ด.90/91) กรุณาติดต่อสายด่วนสรรพากร โทร. 1161 หรือเยี่ยมชมเว็บไซต์กรมสรรพากร", 
             "[]", 1, 0),

            ("sess_005", "ขั้นตอนขอคืนภาษีท่องเที่ยวประชารัฐทำอย่างไร", "ขั้นตอนการขอคืนภาษีท่องเที่ยวประชารัฐ", 
             "ขออภัยครับ ระบบนี้ให้บริการข้อมูลและตอบคำถามเฉพาะเรื่อง 'การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration)' เท่านั้น หากท่านต้องการสอบถามเรื่องการขอคืนภาษีการท่องเที่ยว กรุณาศึกษาข้อมูลเพิ่มเติมที่เว็บไซต์ของกรมสรรพากรโดยตรงครับ", 
             "[]", 1, 0),

            ("sess_006", "ขอทราบวิธีคำนวณภาษีมรดกหน่อยค่ะ", "วิธีคำนวณภาษีมรดก", 
             "ขออภัยครับ ระบบนี้ให้บริการข้อมูลและตอบคำถามเฉพาะเรื่อง 'การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration)' เท่านั้น สำหรับข้อมูลเกี่ยวกับภาษีมรดก สามารถสืบค้นได้ที่หัวข้อภาษีมรดกในเว็บไซต์กรมสรรพากรครับ", 
             "[]", 1, 0),

            ("sess_007", "กรมสรรพากรสมัครงานยังไง เปิดสอบช่วงไหน", "สมัครงานกรมสรรพากร เปิดสอบช่วงไหน", 
             "ขออภัยครับ ระบบนี้ให้บริการข้อมูลและตอบคำถามเฉพาะเรื่อง 'การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration)' เท่านั้น หากท่านสนใจร่วมงานกับกรมสรรพากร สามารถติดตามข่าวสารการรับสมัครงานและสอบแข่งขันได้ที่กองบริหารทรัพยากรบุคคล บนเว็บไซต์หลักของกรมสรรพากรครับ", 
             "[]", 1, 0),

            ("sess_008", "จดทะเบียนบริษัทที่กรมพัฒนาธุรกิจการค้ากระทรวงพาณิชย์ทำอย่างไร", "จดทะเบียนบริษัท กรมพัฒนาธุรกิจการค้า", 
             "ขออภัยครับ ระบบนี้ให้บริการข้อมูลและตอบคำถามเฉพาะเรื่อง 'การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration)' ของกรมสรรพากรเท่านั้น หากท่านต้องการทราบขั้นตอนการจดทะเบียนจัดตั้งบริษัทจำกัด กรุณาติดต่อกรมพัฒนาธุรกิจการค้า (DBD) กระทรวงพาณิชย์ หรือสายด่วน 1570", 
             "[]", 1, 0),
        ]
        
        for item in seed_data:
            cursor.execute("""
                INSERT INTO logs (session_id, original_query, rewritten_query, response, raw_laws, is_out_of_scope, detected_conflict)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, item)
        conn.commit()
    conn.close()

def log_chat(session_id: str, original_query: str, rewritten_query: str, response: str, raw_laws: list, is_out_of_scope: bool, detected_conflict: bool):
    """Logs a chat interaction to the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (session_id, original_query, rewritten_query, response, raw_laws, is_out_of_scope, detected_conflict)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        original_query,
        rewritten_query,
        response,
        json.dumps(raw_laws, ensure_ascii=False),
        1 if is_out_of_scope else 0,
        1 if detected_conflict else 0
    ))
    conn.commit()
    conn.close()

def get_admin_stats():
    """Retrieves aggregated statistics for the Admin Dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total sessions
    cursor.execute("SELECT COUNT(DISTINCT session_id) FROM logs")
    total_sessions = cursor.fetchone()[0] or 0
    
    # 2. Total interactions
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_interactions = cursor.fetchone()[0] or 0
    
    # 3. Out of scope count
    cursor.execute("SELECT COUNT(*) FROM logs WHERE is_out_of_scope = 1")
    total_out_of_scope = cursor.fetchone()[0] or 0
    
    # 4. Conflict count
    cursor.execute("SELECT COUNT(*) FROM logs WHERE detected_conflict = 1")
    total_conflicts = cursor.fetchone()[0] or 0
    
    # 5. Top 5 In-Scope FAQs (queries that were not out of scope)
    cursor.execute("""
        SELECT original_query, COUNT(*) as count 
        FROM logs 
        WHERE is_out_of_scope = 0 
        GROUP BY original_query 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_faq = [dict(row) for row in cursor.fetchall()]
    
    # 6. Top 5 Out-of-Scope Queries
    cursor.execute("""
        SELECT original_query, COUNT(*) as count 
        FROM logs 
        WHERE is_out_of_scope = 1 
        GROUP BY original_query 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_out_of_scope = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_sessions": total_sessions,
        "total_interactions": total_interactions,
        "total_out_of_scope": total_out_of_scope,
        "total_conflicts": total_conflicts,
        "top_faq": top_faq,
        "top_out_of_scope": top_out_of_scope
    }

def get_all_logs(limit: int = 50):
    """Retrieves all chat logs ordered by latest timestamp first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, session_id, original_query, rewritten_query, response, raw_laws, is_out_of_scope, detected_conflict, timestamp 
        FROM logs 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs
