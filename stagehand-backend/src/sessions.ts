/**
 * Stagehand Session Manager - v3 Compatible
 * Manages browser sessions with proper lifecycle
 */
import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";

interface Session {
    stagehand: Stagehand;
    createdAt: Date;
    lastActivity: Date;
}

class SessionManager {
    private sessions = new Map<string, Session>();
    private cleanupInterval: NodeJS.Timeout | null = null;

    constructor() {
        // Clean up stale sessions every 5 minutes
        this.cleanupInterval = setInterval(() => this.cleanupStaleSessions(), 5 * 60 * 1000);
    }

    async create(sessionId: string): Promise<Stagehand> {
        // Close existing session if any
        if (this.sessions.has(sessionId)) {
            await this.close(sessionId);
        }

        console.log(`[Session ${sessionId}] Creating new Stagehand v3 instance...`);

        // Check for API key
        const geminiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY || process.env.GOOGLE_API_KEY;
        const openaiKey = process.env.OPENAI_API_KEY;

        if (!geminiKey && !openaiKey) {
            console.warn("[Warning] No API key found. Add OPENAI_API_KEY or GOOGLE_GENERATIVE_AI_API_KEY to .env");
        }

        // Stagehand v3 configuration for LOCAL mode with Gemini
        const stagehand = new Stagehand({
            env: "LOCAL",
            // For Gemini, use model config
            model: geminiKey ? "google/gemini-2.5-flash" : "openai/gpt-4o",
            localBrowserLaunchOptions: {
                headless: false,
            },
            verbose: 1,
        });

        await stagehand.init();
        console.log(`[Session ${sessionId}] Stagehand v3 initialized successfully`);

        this.sessions.set(sessionId, {
            stagehand,
            createdAt: new Date(),
            lastActivity: new Date(),
        });

        return stagehand;
    }

    get(sessionId: string): Stagehand | undefined {
        const session = this.sessions.get(sessionId);
        if (session) {
            session.lastActivity = new Date();
            return session.stagehand;
        }
        return undefined;
    }

    async close(sessionId: string): Promise<void> {
        const session = this.sessions.get(sessionId);
        if (session) {
            console.log(`[Session ${sessionId}] Closing...`);
            try {
                await session.stagehand.close();
            } catch (error) {
                console.error(`[Session ${sessionId}] Error closing:`, error);
            }
            this.sessions.delete(sessionId);
        }
    }

    async closeAll(): Promise<void> {
        const sessionIds = Array.from(this.sessions.keys());
        for (const sessionId of sessionIds) {
            await this.close(sessionId);
        }
    }

    private async cleanupStaleSessions(): Promise<void> {
        const now = new Date();
        const maxAge = 30 * 60 * 1000; // 30 minutes

        for (const [sessionId, session] of this.sessions) {
            const age = now.getTime() - session.lastActivity.getTime();
            if (age > maxAge) {
                console.log(`[Session ${sessionId}] Cleaning up stale session`);
                await this.close(sessionId);
            }
        }
    }

    destroy(): void {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        this.closeAll();
    }
}

// Singleton instance
export const sessionManager = new SessionManager();
