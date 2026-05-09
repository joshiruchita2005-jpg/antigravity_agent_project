🚀 Freelancer Admin Automation Agent
An AI-powered freelancer administration system that automates proposals, invoices, and payment reminders through a modern conversational interface.
Features
Feature	Description
🧾 Proposal Generation	AI-drafted professional proposals (PDF + DOCX)
💰 Invoice Generation	Auto-calculated invoices with professional PDF layout
📧 Payment Reminders	Tone-adaptive emails sent via Gmail
📋 Invoice Tracking	SQLite-backed persistent storage
🔍 Client History	Full history of all client interactions
💬 Conversational UI	Dark-themed, real-time chat interface
Quick Start
1. Install Dependencies
```bash
pip install -r requirements.txt
```
2. Configure Environment
Edit `.env` with your credentials:
```env
OPENAI_API_KEY=your_openai_api_key
GMAIL_SENDER=youremail@gmail.com
GMAIL_APP_PASS=your_gmail_app_password
```
3. Run the Server
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
4. Open in Browser
Visit: http://localhost:8000
Project Structure
```
antigravity_agent_project/
├── app.py                          # FastAPI application entry point
├── requirements.txt                # All Python dependencies
├── .env                            # API keys (never commit this)
├── freelancer.db                   # SQLite database (auto-created)
├── frontend/
│   ├── index.html                  # Premium dark-themed UI
│   ├── style.css                   # Design system & styles
│   └── script.js                   # Chat logic & action cards
├── backend/
│   ├── config/
│   │   ├── openai_client.py        # Centralized OpenAI client
│   │   └── settings.py             # Environment variable loader
│   ├── chatbot/
│   │   ├── dialogue_manager.py     # Core conversation engine
│   │   └── intent_router.py        # Intent detection (AI + fallback)
│   ├── proposal/
│   │   └── generator.py            # Proposal content + PDF + DOCX
│   ├── invoice/
│   │   └── generator.py            # Invoice PDF generator
│   ├── reminders/
│   │   ├── generator.py            # AI reminder email generator
│   │   └── sender.py               # Gmail SMTP sender
│   └── storage/
│       ├── database.py             # SQLite schema + init
│       └── crud.py                 # All CRUD operations
└── generated_documents/            # PDF/DOCX files saved here
```
API Endpoints
Method	Endpoint	Description
`POST`	`/api/chat`	Send a message to the AI agent
`POST`	`/api/action`	Generate docs or send email
`GET`	`/api/invoices`	List all invoices
`PATCH`	`/api/invoices/{id}/status`	Update invoice status
`GET`	`/api/clients`	List all clients
`GET`	`/api/clients/{name}/history`	Client full history
`GET`	`/api/health`	Health check
Gmail Setup
Enable 2-Factor Authentication on your Google account
Go to Google Account → Security → App Passwords
Generate an app password for "Mail"
Add it to `.env` as `GMAIL_APP_PASS`
AI Model
Uses GPT-4.1-mini for:
Intent detection
Field extraction from conversation
Proposal content generation
Payment reminder drafting
Falls back to GPT-3.5-turbo if primary model is unavailable.
Payment Reminder Tones
Days Overdue	Tone
1–7 days	🟢 Gentle
8–21 days	🟡 Firm
22+ days	🔴 Urgent
