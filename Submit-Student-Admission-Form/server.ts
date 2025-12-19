// server.ts
import express from "express";
import http from "http";
import { WebSocketServer, WebSocket } from "ws";
import { runWorkflow } from "./index";

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.get("/health", (_, res) => res.json({ ok: true }));

wss.on("connection", (ws: WebSocket) => {
  console.log("🔌 WebSocket connected");

  let otpResolver: ((otp: string) => void) | null = null;
  let workflowRunning = false;

  const send = (type: string, payload: any = {}) => {
    ws.readyState === WebSocket.OPEN &&
      ws.send(JSON.stringify({ type, payload }));
  };

  ws.on("message", async (raw) => {
    const msg = JSON.parse(raw.toString());

    // FORM SUBMIT
    if (msg.type === "FORM_SUBMIT" && !workflowRunning) {
      workflowRunning = true;

      try {
        send("LOG", "Starting workflow...");

        const getOtp = () =>
          new Promise<string>((resolve) => {
            otpResolver = resolve;
            send("REQUEST_OTP");
          });

        await runWorkflow(
          msg.payload,
          getOtp,
          (m) => send("LOG", m)
        );

        send("SUBMISSION_RESULT", { success: true });
      } catch (e: any) {
        send("SUBMISSION_RESULT", {
          success: false,
          message: e.message,
        });
      } finally {
        workflowRunning = false;
        setTimeout(() => ws.close(), 1000);
      }
    }

    // OTP SUBMIT
    if (msg.type === "OTP_SUBMIT" && otpResolver) {
      otpResolver(msg.payload.otp);
      otpResolver = null;
      send("LOG", "OTP submitted by user");
    }
  });

  ws.on("close", () => console.log("❌ WebSocket disconnected"));
});

server.listen(3000, () =>
  console.log("🚀 WS server running on http://localhost:3000")
);
