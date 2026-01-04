# Exam Auto-Apply Bot 🤖

An automated application bot designed to register students for the **PW NSAT (Physics Wallah National Scholarship cum Admission Test)**. This project leverages AI-powered browser automation with **Stagehand** and real-time communication via **WebSockets**.

## 🏗️ Architecture

The project is split into two main components:

-   **Backend (`Submit-Student-Admission-Form`)**: A Node.js server that runs the [Stagehand](https://stagehand.dev/) automation scripts. It manages the browser session and communicates with the frontend via WebSockets.
-   **Frontend (`cleint`)**: A Next.js application that provides a user-friendly interface for initiating the application process and entering the OTP (One-Time Password) during the login step.

## 🚀 Getting Started

### Prerequisites

-   Node.js (v18 or higher)
-   npm, pnpm, or yarn

### 1. Backend Setup

```bash
cd Submit-Student-Admission-Form
npm install
npm start
```

### 2. Frontend Setup

```bash
cd cleint
npm install
npm run dev
```

### ⚡ Simplified Run (Windows)

You can run both the backend and frontend simultaneously using the provided batch script:

1.  Double-click `run.bat` in the root directory.
2.  It will automatically install dependencies (if missing) and start both servers in separate windows.
*The client will be available at `http://localhost:3001` (or the next available port).*

## 🛠️ How It Works

1.  **Form Submission**: The user clicks "Apply" on the frontend.
2.  **WebSocket Connection**: The frontend opens a WebSocket connection to the backend server.
3.  **Automation Trigger**: The backend receives the `FORM_SUBMIT` message and initializes **Stagehand**.
4.  **Browser Orchestration**:
    -   Navigates to the PW NSAT registration page.
    -   Enters the student's mobile number.
    -   Requests an OTP from the user via the WebSocket.
5.  **OTP Handling**: The frontend displays an OTP input field. Once submitted, the OTP is sent back to the backend.
6.  **Completion**: The backend fills the OTP, selects the required exam and class details, and submits the form.
7.  **Real-time Logs**: Throughout the process, the backend sends status logs to the frontend, which are displayed in the UI.

## 📁 Project Structure

```text
.
├── Submit-Student-Admission-Form/   # Backend (Stagehand + Express + WebSocket)
│   ├── index.ts                     # Automation workflow logic
│   ├── server.ts                    # WebSocket server
│   └── stagehand.config.ts          # Stagehand configuration
└── cleint/                          # Frontend (Next.js + Tailwind CSS)
    └── app/
        └── page.tsx                 # Main UI and WebSocket client logic
```

## 🔋 Technologies Used

-   **[Stagehand](https://github.com/browserbase/stagehand)**: AI-driven browser automation.
-   **Next.js**: Modern React framework for the frontend.
-   **WebSockets (ws)**: For bidirectional, real-time communication between client and server.
-   **TypeScript**: Ensures type safety across the codebase.

---
*Note: This project is for educational purposes. Ensure you comply with the terms of service of any website you automate.*
