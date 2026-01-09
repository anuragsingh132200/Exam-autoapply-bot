# Exam Auto-Apply Bot 🤖

An AI-powered automated form-filling bot for exam registrations. Uses **LLM Vision** (Gemini) to analyze pages and **Stagehand** for browser automation.

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│    Frontend     │────▶│  Python Backend  │────▶│ Stagehand Backend  │
│   (Next.js)     │     │   (FastAPI)      │     │   (TypeScript)     │
│   Port: 3000    │     │   Port: 8000     │     │    Port: 3001      │
└─────────────────┘     └──────────────────┘     └────────────────────┘
        │                       │                        │
        │                       ▼                        ▼
        │              ┌──────────────────┐     ┌────────────────────┐
        │              │  Gemini Vision   │     │   Browser (CDP)    │
        │              │  (LLM Analysis)  │     │   via Stagehand    │
        │              └──────────────────┘     └────────────────────┘
        │
        ▼
   WebSocket (Real-time logs, OTP requests, screenshots)
```

## 🚀 Quick Start

### Prerequisites
- Node.js v18+
- Python 3.10+
- MongoDB (local or Atlas)

### 1. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 2. Python Backend Setup
```bash
cd python-backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Stagehand Backend Setup
```bash
cd stagehand-backend
npm install
npm run dev
```

### Environment Variables

**python-backend/.env**
```env
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key
MONGODB_URL=mongodb://localhost:27017
STAGEHAND_BACKEND_URL=http://localhost:3001
```

**stagehand-backend/.env**
```env
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key
```

## 🛠️ How It Works

1. **User adds exam** - Creates exam with URL and field mappings
2. **User adds profile** - Stores personal data (name, email, phone, etc.)
3. **Click Apply** - Starts the automation workflow

### Workflow Loop
```
capture_screenshot → llm_decide → execute_action → (loop)
                                        ↓
                         ┌──────────────────────────────┐
                         │     Action Types:            │
                         │  • fill_field (form inputs)  │
                         │  • click_checkbox            │
                         │  • click_button              │
                         │  • wait_for_human (OTP)      │
                         │  • success (done!)           │
                         └──────────────────────────────┘
```

### OTP Handling
- LLM detects OTP input → Sends modal to frontend
- User enters OTP → Bot fills it and continues

### Captcha Handling
- LLM reads captcha image automatically
- No human intervention needed (AI solves it!)

## 📁 Project Structure

```
├── frontend/                  # Next.js UI
│   └── app/
│       ├── page.tsx          # Dashboard
│       └── workflow/         # Real-time workflow view
│
├── python-backend/            # FastAPI + LangGraph
│   └── app/
│       ├── graph/            # Workflow nodes & logic
│       │   ├── nodes.py      # Action execution
│       │   ├── llm_decision.py  # LLM Vision analysis
│       │   └── builder.py    # Graph construction
│       └── api/
│           └── websocket.py  # Real-time communication
│
└── stagehand-backend/         # TypeScript Stagehand
    └── src/
        ├── sessions.ts       # Browser session manager
        └── routes/api.ts     # Stagehand API endpoints
```

## 🔧 Technologies

| Component | Technology |
|-----------|------------|
| Frontend | Next.js, React, Tailwind CSS |
| Python Backend | FastAPI, LangGraph, Pydantic |
| Stagehand Backend | TypeScript, Stagehand v3, Playwright |
| LLM | Gemini 2.5 Flash (Vision) |
| Database | MongoDB |
| Realtime | WebSockets |

## 📝 Adding Support for New Exams

1. **Add Exam** in frontend → Enter URL and field mappings
2. **Field Mappings** map user data keys to form labels
3. **Test** the workflow on the real site

## ⚠️ Notes

- For educational purposes only
- Ensure compliance with website terms of service
- OTP requires user intervention (can't be automated)

---
Made with ❤️ using Stagehand + Gemini Vision
