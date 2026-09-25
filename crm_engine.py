import os
import sqlite3
import tempfile
from typing import List
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn

API_KEY_SECRET = os.getenv("API_KEY_SECRET", "EnterpriseAutomationSecret2026")

# Cloud File Path Logic: Use a safe temp directory to bypass read-only cloud systems
DB_PATH = os.getenv("DB_PATH", os.path.join(tempfile.gettempdir(), "enterprise_crm.db"))

app = FastAPI(
    title="Enterprise CRM Automation Sync Engine",
    description="Secure multi-route backend data pipeline with access control and Pydantic schema validation.",
    version="2026.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomerLead(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str

def verify_api_key(x_api_key: str = Header(..., description="Secure enterprise gateway validation key")):
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Security Violation: Invalid or missing API credential header.")
    return x_api_key

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            company TEXT,
            sync_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 1. FIXED HEALTH CHECK: Securely hides internal system directory details
@app.get("/")
def health_check():
    return {"status": "online", "service": "Enterprise CRM Automation Sync Engine"}

# 2. CREATE ENDPOINT (POST): Masked error exceptions to block data leaks
@app.post("/api/v1/sync-lead", status_code=201, dependencies=[Depends(verify_api_key)])
def sync_lead_to_crm(lead: CustomerLead):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leads (name, email, phone, company) VALUES (?, ?, ?, ?)",
                        (lead.name, lead.email, lead.phone, lead.company))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"🚀 Lead for '{lead.name}' successfully synced!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Error: This email already exists.")
    except Exception as e:
        print(f"Unexpected error: {e}")  # Logs error server-side safely
        raise HTTPException(status_code=500, detail="Internal server error.")

# 3. READ ENDPOINT (GET)
@app.get("/api/v1/leads", response_model=List[dict], dependencies=[Depends(verify_api_key)])
def get_all_leads():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY sync_timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 4. FIXED UPDATE ENDPOINT (PUT): Tracks and isolates duplicate emails cleanly
@app.put("/api/v1/leads/{lead_id}", dependencies=[Depends(verify_api_key)])
def update_lead(lead_id: int, updated_fields: CustomerLead):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM leads WHERE id = ?", (lead_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found.")
    try:
        cursor.execute("UPDATE leads SET name=?, email=?, phone=?, company=? WHERE id=?",
                        (updated_fields.name, updated_fields.email, updated_fields.phone, updated_fields.company, lead_id))
        conn.commit()
        return {"status": "success", "message": f"🔄 Lead {lead_id} updated."}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Error: This email already exists.")
    finally:
        conn.close()

# 5. DELETE ENDPOINT (DELETE)
@app.delete("/api/v1/leads/{lead_id}", dependencies=[Depends(verify_api_key)])
def delete_lead(lead_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM leads WHERE id = ?", (lead_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found.")
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"🗑️ Lead {lead_id} deleted."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("crm_engine:app", host="0.0.0.0", port=port, reload=False)