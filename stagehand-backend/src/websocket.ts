/**
 * WebSocket Manager for Real-time Communication
 * Broadcasts screenshots and logs to connected clients
 */
import { WebSocket, WebSocketServer } from "ws";

interface ClientInfo {
    ws: WebSocket;
    sessionId: string | null;
}

class WebSocketManager {
    private wss: WebSocketServer | null = null;
    private clients = new Map<WebSocket, ClientInfo>();

    attach(wss: WebSocketServer): void {
        this.wss = wss;

        wss.on("connection", (ws) => {
            console.log("[WebSocket] Client connected");
            this.clients.set(ws, { ws, sessionId: null });

            ws.on("message", (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    if (message.type === "subscribe" && message.sessionId) {
                        const client = this.clients.get(ws);
                        if (client) {
                            client.sessionId = message.sessionId;
                            console.log(`[WebSocket] Client subscribed to session: ${message.sessionId}`);
                        }
                    }
                } catch (error) {
                    console.error("[WebSocket] Error parsing message:", error);
                }
            });

            ws.on("close", () => {
                console.log("[WebSocket] Client disconnected");
                this.clients.delete(ws);
            });

            ws.on("error", (error) => {
                console.error("[WebSocket] Error:", error);
                this.clients.delete(ws);
            });
        });
    }

    /**
     * Broadcast screenshot to all clients subscribed to a session
     */
    broadcastScreenshot(sessionId: string, base64: string, step?: string): void {
        this.broadcast(sessionId, {
            type: "screenshot",
            sessionId,
            data: base64,
            step: step || "capture",
            timestamp: new Date().toISOString(),
        });
    }

    /**
     * Broadcast log message to all clients subscribed to a session
     */
    broadcastLog(sessionId: string, message: string, level: "info" | "success" | "warning" | "error" = "info"): void {
        this.broadcast(sessionId, {
            type: "log",
            sessionId,
            message,
            level,
            timestamp: new Date().toISOString(),
        });
    }

    /**
     * Broadcast status update to all clients subscribed to a session
     */
    broadcastStatus(sessionId: string, step: string, progress: number, message: string): void {
        this.broadcast(sessionId, {
            type: "status",
            sessionId,
            step,
            progress,
            message,
            timestamp: new Date().toISOString(),
        });
    }

    /**
     * Request user input (OTP, captcha, etc.)
     */
    requestInput(sessionId: string, inputType: "otp" | "captcha" | "custom", options?: Record<string, unknown>): void {
        this.broadcast(sessionId, {
            type: "request_input",
            sessionId,
            inputType,
            ...options,
            timestamp: new Date().toISOString(),
        });
    }

    /**
     * Broadcast result (success or failure)
     */
    broadcastResult(sessionId: string, success: boolean, message: string): void {
        this.broadcast(sessionId, {
            type: "result",
            sessionId,
            success,
            message,
            timestamp: new Date().toISOString(),
        });
    }

    private broadcast(sessionId: string, data: Record<string, unknown>): void {
        const message = JSON.stringify(data);

        for (const [, client] of this.clients) {
            if (client.sessionId === sessionId && client.ws.readyState === WebSocket.OPEN) {
                client.ws.send(message);
            }
        }
    }

    getClientCount(sessionId?: string): number {
        if (!sessionId) {
            return this.clients.size;
        }
        let count = 0;
        for (const [, client] of this.clients) {
            if (client.sessionId === sessionId) {
                count++;
            }
        }
        return count;
    }
}

// Singleton instance
export const wsManager = new WebSocketManager();
