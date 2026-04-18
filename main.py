from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

# ============================================================
# 1. Data Models based on your sample Excel payloads
# ============================================================

# ---------- PO Acknowledgement (sample from sheet) ----------
class POAckPayload(BaseModel):
    sending_partner: str
    unique_id: str
    msg_data: str          # e.g., "POACK"
    msg_type: str          # e.g., "0460145625"

# ---------- PO Error / Changes (sample from sheet) ----------
class POErrorItem(BaseModel):
    po_no: str
    idoc_no: str
    log_type: str
    po_line_no: str
    log_val: str

class POErrorPayload(BaseModel):
    ackmsg: List[POErrorItem]

# ---------- ASN Data (Advance Shipping Notification) ----------
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
# 2. In-memory storage (arrays)
# ============================================================
po_acks_store = []      # stores POAckPayload
po_errors_store = []    # stores POErrorPayload
asn_data_store = []     # stores ASNPayload

# ============================================================
# 3. FastAPI app with CORS
# ============================================================
app = FastAPI(title="SAP Portal (PO_ACK, PO_ERROR, ASN_Data Receiver)",
              description="Receives realistic SAP payloads and stores them for viewing")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 4. Receive Endpoints (SAP → Portal)
# ============================================================

@app.post("/receive/po_ack", status_code=201)
async def receive_po_ack(payload: POAckPayload):
    """Receives PO Acknowledgement from SAP."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    po_acks_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

@app.post("/receive/po_error", status_code=201)
async def receive_po_error(payload: POErrorPayload):
    """Receives PO Error / Changes from SAP."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    po_errors_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

@app.post("/receive/asn_data", status_code=201)
async def receive_asn_data(payload: ASNPayload):
    """Receives Advance Shipping Notification (ASN) from SAP."""
    stored = payload.dict()
    stored["received_at"] = datetime.utcnow().isoformat()
    stored["internal_id"] = str(uuid4())
    asn_data_store.append(stored)
    return {"status": "stored", "id": stored["internal_id"]}

# ============================================================
# 5. View Endpoints (Portal → You)
# ============================================================

@app.get("/view/po_acks")
async def list_po_acks():
    """Returns all stored PO Acknowledgements."""
    return po_acks_store

@app.get("/view/po_errors")
async def list_po_errors():
    """Returns all stored PO Errors."""
    return po_errors_store

@app.get("/view/asn_data")
async def list_asn_data():
    """Returns all stored ASN Data."""
    return asn_data_store

# ============================================================
# 6. Admin (optional)
# ============================================================
@app.delete("/admin/clear", status_code=204)
async def clear_all():
    po_acks_store.clear()
    po_errors_store.clear()
    asn_data_store.clear()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "SAP Dummy Portal"}