"""
Freelancer Admin Automation Agent — FastAPI Application
Routes: /api/chat, /api/action, /api/invoices, /api/invoices/{id}/status, /api/clients
"""
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.storage.database import init_db
from backend.storage import crud
from backend.chatbot.dialogue_manager import process_message
from backend.proposal.generator import create_proposal_pdf, create_proposal_docx
from backend.invoice.generator import generate_invoice_pdf
from backend.reminders.sender import send_email

# ─── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Freelancer Admin Automation Agent",
    description="AI-powered freelancer administration: proposals, invoices, reminders.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
init_db()

# Serve frontend and generated documents
app.mount("/static", StaticFiles(directory="frontend"), name="static")

DOCS_DIR = os.path.join(os.path.dirname(__file__), "generated_documents")
os.makedirs(DOCS_DIR, exist_ok=True)
app.mount("/docs", StaticFiles(directory="generated_documents"), name="docs")


# ─── Request Models ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str = ""
    message: str


class ActionRequest(BaseModel):
    session_id: str = ""
    action_type: str
    data: dict


class InvoiceStatusUpdate(BaseModel):
    status: str  # "PAID" or "UNPAID"


# ─── Frontend ────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return FileResponse("frontend/index.html")


# ─── Chat Endpoint ───────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(request: ChatRequest):
    """Main chat endpoint — processes user messages through the dialogue manager."""
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response = process_message(session_id, request.message)
        return {
            "session_id": session_id,
            "reply": response.get("reply"),
            "intent": response.get("intent"),
            "action": response.get("action"),
            "progress": response.get("progress"),
        }
    except Exception as e:
        print(f"[chat] Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error. Please try again."}
        )


# ─── Action Endpoint (Document Generation + Email) ───────────────────────────
@app.post("/api/action")
def perform_action(request: ActionRequest):
    """
    Handles document generation and email sending actions.
    action_type: proposal_generated | invoice_ready | reminder_ready
    """
    action_type = request.action_type
    data = request.data

    # ── Proposal: Generate PDF + DOCX ───────────────────────────────────────
    if action_type == "proposal_generated":
        content = data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="No proposal content provided.")

        hint = data.get("filename_hint", "Proposal")
        safe_hint = "".join(c for c in hint if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"Proposal_{safe_hint}_{uuid.uuid4().hex[:6]}"

        try:
            create_proposal_pdf(content, filename)
            create_proposal_docx(content, filename)
            return {
                "status": "success",
                "message": "Your proposal documents are ready to download!",
                "pdf_url": f"/docs/{filename}.pdf",
                "docx_url": f"/docs/{filename}.docx",
            }
        except Exception as e:
            print(f"[action] Proposal generation error: {e}")
            raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

    # ── Invoice: Generate PDF ────────────────────────────────────────────────
    elif action_type == "invoice_ready":
        invoice_data = data.get("data", data)
        inv_num = invoice_data.get("Invoice Number", uuid.uuid4().hex[:8])
        safe_num = inv_num.replace("/", "-").replace("\\", "-")
        filename = f"Invoice_{safe_num}"

        try:
            generate_invoice_pdf(invoice_data, filename)
            return {
                "status": "success",
                "message": f"Invoice {inv_num} PDF has been generated and is ready to download!",
                "pdf_url": f"/docs/{filename}.pdf",
            }
        except Exception as e:
            print(f"[action] Invoice generation error: {e}")
            raise HTTPException(status_code=500, detail=f"Invoice generation failed: {str(e)}")

    # ── Reminder: Send Email via Gmail ───────────────────────────────────────
    elif action_type == "reminder_ready":
        content = data.get("content", "")
        client_email = data.get("email", "")
        client_name = data.get("client_name", "Client")

        if not client_email:
            raise HTTPException(status_code=400, detail="Client email address is required.")
        if not content:
            raise HTTPException(status_code=400, detail="Reminder content is required.")

        lines = content.strip().split("\n")
        subject = "Payment Reminder"
        body = content
        if lines[0].lower().startswith("subject:"):
            subject = lines[0].replace("Subject:", "").replace("subject:", "").strip()
            body = "\n".join(lines[2:]).strip()

        success = send_email(client_email, subject, body)

        if success:
            return {
                "status": "success",
                "message": f"Payment reminder sent successfully to {client_email}!",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email. Please check your Gmail credentials in .env"
            )

    raise HTTPException(status_code=400, detail=f"Unknown action type: '{action_type}'")


# ─── Invoice Management API ───────────────────────────────────────────────────
@app.get("/api/invoices")
def get_invoices(status: str = None):
    """Get all invoices, optionally filtered by status (PAID/UNPAID)."""
    if status and status.upper() == "UNPAID":
        return {"invoices": crud.get_unpaid_invoices()}
    return {"invoices": crud.get_all_invoices()}


@app.patch("/api/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, update: InvoiceStatusUpdate):
    """Update payment status for an invoice."""
    valid_statuses = {"PAID", "UNPAID"}
    if update.status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")
    crud.update_invoice_status(invoice_id, update.status.upper())
    return {"status": "success", "message": f"Invoice {invoice_id} marked as {update.status.upper()}"}


# ─── Client API ───────────────────────────────────────────────────────────────
@app.get("/api/clients")
def get_clients():
    """Get all clients."""
    return {"clients": crud.get_all_clients()}


@app.get("/api/clients/{client_name}/history")
def get_client_history(client_name: str):
    """Get full history for a client."""
    history = crud.get_client_history(client_name)
    if not history:
        raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found.")
    return history


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
