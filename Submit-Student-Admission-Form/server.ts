import express from "express";
import http from "http";
import { WebSocketServer, WebSocket } from "ws";
import { runWorkflow } from "./index";

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.get("/health", (_, res) => {
  res.json({ ok: true });
});

wss.on("connection", (ws: WebSocket) => {
  console.log("🔌 WebSocket connected");
  let isRunning = false;

  const sendMessage = (type: string, payload: any = {}) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, payload }));
    }
  };

  const log = (message: string) => {
    console.log(`[${new Date().toISOString()}] ${message}`);
    sendMessage('LOG', { message });
  };

  ws.on("message", async (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      if (isRunning) {
        sendMessage('ERROR', { message: 'A workflow is already running' });
        return;
      }

      if (data.type === 'FORM_SUBMIT') {
        isRunning = true;
        log('Received form submission');
        
        try {
          log('Starting form processing workflow...');
          
          await runWorkflow(data.payload, (message) => {
            log(message);
          });
          
          log('Form processed successfully');
          sendMessage('SUBMISSION_RESULT', { 
            success: true, 
            message: 'Form submitted successfully' 
          });
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
          console.error('Workflow error:', error);
          log(`Error: ${errorMessage}`);
          sendMessage('SUBMISSION_RESULT', { 
            success: false, 
            message: errorMessage 
          });
        } finally {
          isRunning = false;
          // Give some time for the final messages to be sent before closing
          setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.close();
            }
          }, 1000);
        }
      } else {
        sendMessage('ERROR', { message: 'Invalid message type' });
      }
      
    } catch (error) {
      console.error('Error processing message:', error);
      sendMessage('ERROR', { 
        message: 'Error processing request',
        error: error instanceof Error ? error.message : String(error)
      });
    }
  });

  ws.on("close", () => {
    console.log("❌ Client disconnected");
  });
});

const PORT = Number(process.env.PORT ?? 3000);
server.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
