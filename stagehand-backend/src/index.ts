/**
 * Stagehand Backend Server
 * 
 * Express + WebSocket server for browser automation
 * Called by Python LangGraph backend
 */
import "dotenv/config";
import express from "express";
import cors from "cors";
import { createServer } from "http";
import { WebSocketServer } from "ws";
import { apiRouter } from "./routes/api.js";
import { wsManager } from "./websocket.js";
import { sessionManager } from "./sessions.js";

const PORT = process.env.PORT || 3001;

// Create Express app
const app = express();

// Middleware
app.use(cors({
    origin: ["http://localhost:3000", "http://localhost:8000"],
    credentials: true,
}));
app.use(express.json({ limit: "50mb" }));

// API Routes
app.use("/api", apiRouter);

// Root endpoint
app.get("/", (_req, res) => {
    res.json({
        name: "Stagehand Backend",
        version: "1.0.0",
        status: "running",
        endpoints: {
            "POST /api/init": "Initialize browser session",
            "POST /api/execute": "Execute act/observe/extract",
            "POST /api/fill-form": "Fill form fields",
            "POST /api/click": "Click element",
            "POST /api/submit": "Submit form",
            "POST /api/input": "Enter OTP/captcha",
            "POST /api/analyze": "Analyze page",
            "POST /api/screenshot": "Capture screenshot",
            "POST /api/close": "Close session",
            "GET /api/health": "Health check",
            "WS /ws": "WebSocket for real-time updates",
        },
    });
});

// Create HTTP server
const server = createServer(app);

// Create WebSocket server
const wss = new WebSocketServer({ server, path: "/ws" });
wsManager.attach(wss);

// Graceful shutdown
process.on("SIGINT", async () => {
    console.log("\n[Server] Shutting down...");
    await sessionManager.closeAll();
    sessionManager.destroy();
    server.close(() => {
        console.log("[Server] Goodbye!");
        process.exit(0);
    });
});

process.on("SIGTERM", async () => {
    console.log("\n[Server] Received SIGTERM...");
    await sessionManager.closeAll();
    sessionManager.destroy();
    server.close(() => process.exit(0));
});

// Start server
server.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║                   STAGEHAND BACKEND                        ║
╠════════════════════════════════════════════════════════════╣
║  HTTP Server:  http://localhost:${PORT}                      ║
║  WebSocket:    ws://localhost:${PORT}/ws                     ║
║  Health:       http://localhost:${PORT}/api/health           ║
╚════════════════════════════════════════════════════════════╝
  `);
});

export { app, server };
