# Exam Automation Platform - Python Backend

FastAPI + LangGraph backend for generalized exam form automation.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

Create `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=exam_automation
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```
