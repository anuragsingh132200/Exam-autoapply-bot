# Stagehand Backend

TypeScript backend for browser automation using [Stagehand](https://github.com/browserbase/stagehand).

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file and add your API key
cp .env.example .env

# Start development server
npm run dev
```

## Configuration

Edit `.env`:
```
GOOGLE_API_KEY=your_gemini_api_key_here
PORT=3001
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | POST | Initialize browser session |
| `/api/execute` | POST | Execute act/observe/extract |
| `/api/fill-form` | POST | Fill form fields |
| `/api/click` | POST | Click button/checkbox |
| `/api/submit` | POST | Submit form |
| `/api/input` | POST | Enter OTP/captcha |
| `/api/analyze` | POST | Analyze page state |
| `/api/screenshot` | POST | Capture screenshot |
| `/api/close` | POST | Close session |
| `/api/health` | GET | Health check |

## WebSocket

Connect to `ws://localhost:3001/ws` for real-time updates.

Subscribe to a session:
```javascript
ws.send(JSON.stringify({ type: "subscribe", sessionId: "your-session-id" }));
```

## Architecture

```
Python LangGraph → HTTP → TypeScript Stagehand → Browser
                   ↓
              WebSocket → Frontend (screenshots/logs)
```
