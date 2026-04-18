from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
import os
from secrets import compare_digest

# ============================================================
# Basic Auth configuration
# ============================================================
security = HTTPBasic()

# Read credentials from environment variables (set on Render)
# Defaults for local testing (change these)
AUTH_USERNAME = os.getenv("API_USERNAME", "admin").strip()
AUTH_PASSWORD = os.getenv("API_PASSWORD", "sap123").strip()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify username and password."""
    correct_username = compare_digest(credentials.username, AUTH_USERNAME)
    correct_password = compare_digest(credentials.password, AUTH_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ============================================================
# 1. Data Models based on your sample Excel payloads
# ============================================================

class POAckPayload(BaseModel):
    sending_partner: str
    unique_id: str
    msg_data: str
    msg_type: str

class POErrorItem(BaseModel):
    po_no: str
    idoc_no: str
    log_type: str
    po_line_no: str
    log_val: str

class POErrorPayload(BaseModel):
    ackmsg: List[POErrorItem]

class SerialNoStruct(BaseModel):
    SERNR: str

class ASNItem(BaseModel):
    LIFEX: str
    EBELN: str
    FKDAT: str
    LFDAT: str
    EBELP: str
    KDMAT: str
    EAN11: str
    MATNR: str
    MAKTX: str
    LFIMG: str
    CHARG: str
    HSDAT: str
    VFDAT: str
    NETPR: str
    CNETPR: str
    VNETPR: str
    LNETPR: str
    ANZPK: str
    FREEFLG: str
    POSNR: str
    SerailNoStruct: List[SerialNoStruct] = []

class ASNPayload(BaseModel):
    MainASNStruct: List[ASNItem]

# ============================================================
# 2. In-memory storage
# ============================================================
po_acks_store = []
po_errors_store = []
asn_data_store = []

# ============================================================
# 3. FastAPI app with CORS
# ============================================================
app = FastAPI(title="SAP Portal (PO_ACK, PO_ERROR, ASN_Data) with Basic Auth",
              description="Protected endpoints require username/password")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 4. Public endpoint (no auth) – optional health check
# ============================================================
@app.get("/health")
async def health():
    return {"status": "ok", "service": "SAP Dummy Portal"}

# ============================================================
# 5. Protected Receive Endpoints (SAP → Portal)
# ============================================================

@app.post("/receive/po_ack", status_code=201)
async def receive_po_ack(payload: POAckPayload, username: str = Depends(authenticate)):
    """Receives PO Acknowledgement – requires Basic Auth."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    po_acks_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

@app.post("/receive/po_error", status_code=201)
async def receive_po_error(payload: POErrorPayload, username: str = Depends(authenticate)):
    """Receives PO Error – requires Basic Auth."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    po_errors_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

@app.post("/receive/asn_data", status_code=201)
async def receive_asn_data(payload: ASNPayload, username: str = Depends(authenticate)):
    """Receives ASN Data – requires Basic Auth."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    asn_data_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

# ============================================================
# 6. Protected View Endpoints (Portal → You)
# ============================================================

@app.get("/view/po_acks")
async def list_po_acks(username: str = Depends(authenticate)):
    """Returns all stored PO Acknowledgements – requires Basic Auth."""
    return po_acks_store

@app.get("/view/po_errors")
async def list_po_errors(username: str = Depends(authenticate)):
    """Returns all stored PO Errors – requires Basic Auth."""
    return po_errors_store

@app.get("/view/asn_data")
async def list_asn_data(username: str = Depends(authenticate)):
    """Returns all stored ASN Data – requires Basic Auth."""
    return asn_data_store

# ============================================================
# 7. Admin (optional, protected)
# ============================================================
@app.delete("/admin/clear", status_code=204)
async def clear_all(username: str = Depends(authenticate)):
    po_acks_store.clear()
    po_errors_store.clear()
    asn_data_store.clear()
