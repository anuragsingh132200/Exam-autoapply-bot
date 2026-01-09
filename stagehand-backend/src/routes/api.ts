/**
 * API Routes for Stagehand Browser Automation
 * 
 * These endpoints are called by the Python LangGraph backend
 * to execute browser actions.
 * 
 * Stagehand v3 API - uses simple string parameters
 */
import { Router, Request, Response } from "express";
import { z } from "zod";
import { sessionManager } from "../sessions.js";
import { wsManager } from "../websocket.js";
import {
    buildFillPrompt,
    buildClickButtonPrompt,
    buildCheckboxPrompt,
    buildOtpPrompt,
    buildCaptchaPrompt,
    buildSubmitPrompt,
    buildSelectPrompt,
    normalizeFieldLabel,
} from "../prompts.js";

const router = Router();

// ==================== Request Schemas ====================

const InitRequestSchema = z.object({
    sessionId: z.string(),
    examUrl: z.string().url(),
});

const ExecuteRequestSchema = z.object({
    sessionId: z.string(),
    action: z.enum(["act", "observe", "extract"]),
    prompt: z.string(),
});

const FillFormRequestSchema = z.object({
    sessionId: z.string(),
    fields: z.array(z.object({
        key: z.string(),
        label: z.string().optional(),
        value: z.string(),
        type: z.enum(["text", "select", "checkbox", "date"]).optional(),
    })),
});

const ClickRequestSchema = z.object({
    sessionId: z.string(),
    target: z.string(),
    type: z.enum(["button", "checkbox", "link"]).optional(),
});

const InputRequestSchema = z.object({
    sessionId: z.string(),
    inputType: z.enum(["otp", "captcha"]),
    value: z.string(),
});

const CloseRequestSchema = z.object({
    sessionId: z.string(),
});

// ==================== Helper Functions ====================

async function captureAndBroadcast(sessionId: string, step: string): Promise<string | null> {
    const stagehand = sessionManager.get(sessionId);
    if (!stagehand) return null;

    try {
        const page = stagehand.context.pages()[0];
        // Playwright screenshot returns Buffer, convert to base64
        const buffer = await page.screenshot();
        const screenshot = buffer.toString("base64");
        wsManager.broadcastScreenshot(sessionId, screenshot, step);
        return screenshot;
    } catch (error) {
        console.error(`[${sessionId}] Failed to capture screenshot:`, error);
        return null;
    }
}

// ==================== Endpoints ====================

/**
 * POST /api/init
 * Initialize a new browser session and navigate to URL
 */
router.post("/init", async (req: Request, res: Response) => {
    try {
        const { sessionId, examUrl } = InitRequestSchema.parse(req.body);

        wsManager.broadcastLog(sessionId, "Initializing browser...", "info");
        wsManager.broadcastStatus(sessionId, "init", 5, "Starting browser...");

        const stagehand = await sessionManager.create(sessionId);
        const page = stagehand.context.pages()[0];

        wsManager.broadcastLog(sessionId, `Navigating to ${examUrl}`, "info");
        // Use longer timeout for slow government sites
        await page.goto(examUrl, {
            waitUntil: "networkidle",
            timeoutMs: 120000  // 120 seconds for slow gov sites
        });

        // Wait a bit for page to stabilize
        await new Promise(resolve => setTimeout(resolve, 2000));

        const screenshot = await captureAndBroadcast(sessionId, "init");

        wsManager.broadcastLog(sessionId, "Browser ready", "success");
        wsManager.broadcastStatus(sessionId, "init", 10, "Browser ready");

        res.json({
            success: true,
            sessionId,
            screenshot,
            pageUrl: page.url(),
        });
    } catch (error) {
        console.error("[init] Error:", error);
        res.status(500).json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/execute
 * Execute a raw Stagehand action (act/observe/extract)
 * Used for custom prompts from LangGraph
 */
router.post("/execute", async (req: Request, res: Response) => {
    try {
        const { sessionId, action, prompt } = ExecuteRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastLog(sessionId, `Executing: ${action}`, "info");
        console.log(`[${sessionId}] Executing ${action}: ${prompt.substring(0, 100)}...`);

        let result: unknown;

        // Stagehand v3 API - simple string parameters
        if (action === "act") {
            result = await stagehand.act(prompt);
        } else if (action === "observe") {
            result = await stagehand.observe(prompt);
        } else if (action === "extract") {
            result = await stagehand.extract(prompt);
        }

        const screenshot = await captureAndBroadcast(sessionId, action);

        res.json({
            success: true,
            result,
            screenshot,
        });
    } catch (error) {
        console.error("[execute] Error:", error);
        const sessionId = req.body?.sessionId;
        if (sessionId) {
            wsManager.broadcastLog(sessionId, `Action failed: ${error instanceof Error ? error.message : "Unknown error"}`, "error");
        }
        res.json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/fill-form
 * Fill multiple form fields using robust prompts
 */
router.post("/fill-form", async (req: Request, res: Response) => {
    try {
        const { sessionId, fields } = FillFormRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastStatus(sessionId, "fill_form", 40, "Filling form fields...");

        const results: Array<{ key: string; success: boolean; error?: string }> = [];

        for (const field of fields) {
            const label = field.label || normalizeFieldLabel(field.key);
            wsManager.broadcastLog(sessionId, `Filling: ${label}`, "info");

            try {
                let prompt: string;

                if (field.type === "select") {
                    prompt = buildSelectPrompt(label, field.value);
                } else if (field.type === "checkbox") {
                    prompt = buildCheckboxPrompt(label);
                } else {
                    prompt = buildFillPrompt(label, field.value);
                }

                console.log(`[${sessionId}] Fill prompt: ${prompt}`);
                // Stagehand v3 - just pass string
                await stagehand.act(prompt);

                results.push({ key: field.key, success: true });
                await captureAndBroadcast(sessionId, `fill_${field.key}`);

                // Small delay between fields
                await new Promise(resolve => setTimeout(resolve, 300));

            } catch (error) {
                console.error(`[${sessionId}] Failed to fill ${field.key}:`, error);
                results.push({
                    key: field.key,
                    success: false,
                    error: error instanceof Error ? error.message : "Unknown error",
                });
            }
        }

        const successCount = results.filter(r => r.success).length;
        wsManager.broadcastLog(sessionId, `Filled ${successCount}/${fields.length} fields`, "success");

        const screenshot = await captureAndBroadcast(sessionId, "fill_form_complete");

        res.json({
            success: true,
            results,
            screenshot,
        });
    } catch (error) {
        console.error("[fill-form] Error:", error);
        res.status(500).json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/click
 * Click a button, checkbox, or link
 */
router.post("/click", async (req: Request, res: Response) => {
    try {
        const { sessionId, target, type = "button" } = ClickRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastLog(sessionId, `Clicking: ${target}`, "info");

        let prompt: string;
        if (type === "checkbox") {
            prompt = buildCheckboxPrompt(target);
        } else {
            prompt = buildClickButtonPrompt(target);
        }

        console.log(`[${sessionId}] Click prompt: ${prompt}`);
        // Stagehand v3 - just pass string
        await stagehand.act(prompt);

        // Wait for potential navigation
        const page = await stagehand.context.awaitActivePage();
        await new Promise(resolve => setTimeout(resolve, 1000));

        const screenshot = await captureAndBroadcast(sessionId, "click");

        wsManager.broadcastLog(sessionId, `Clicked: ${target}`, "success");

        res.json({
            success: true,
            screenshot,
            pageUrl: page.url(),
        });
    } catch (error) {
        console.error("[click] Error:", error);
        res.json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/submit
 * Click the submit/continue button
 */
router.post("/submit", async (req: Request, res: Response) => {
    try {
        const { sessionId } = CloseRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastLog(sessionId, "Clicking submit button...", "info");
        wsManager.broadcastStatus(sessionId, "submit", 60, "Submitting form...");

        const prompt = buildSubmitPrompt();
        console.log(`[${sessionId}] Submit prompt: ${prompt}`);

        // Stagehand v3 - just pass string
        await stagehand.act(prompt);

        // Wait for navigation
        const page = await stagehand.context.awaitActivePage();
        await new Promise(resolve => setTimeout(resolve, 2000));

        const screenshot = await captureAndBroadcast(sessionId, "submit");

        wsManager.broadcastLog(sessionId, "Form submitted", "success");

        res.json({
            success: true,
            screenshot,
            pageUrl: page.url(),
        });
    } catch (error) {
        console.error("[submit] Error:", error);
        res.json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/input
 * Enter OTP or captcha solution
 */
router.post("/input", async (req: Request, res: Response) => {
    try {
        const { sessionId, inputType, value } = InputRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastLog(sessionId, `Entering ${inputType}...`, "info");

        let prompt: string;
        if (inputType === "otp") {
            prompt = buildOtpPrompt(value);
        } else {
            prompt = buildCaptchaPrompt(value);
        }

        console.log(`[${sessionId}] Input prompt: ${prompt}`);
        // Stagehand v3 - just pass string
        await stagehand.act(prompt);

        const screenshot = await captureAndBroadcast(sessionId, `input_${inputType}`);

        wsManager.broadcastLog(sessionId, `${inputType.toUpperCase()} entered`, "success");

        res.json({
            success: true,
            screenshot,
        });
    } catch (error) {
        console.error("[input] Error:", error);
        res.json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/analyze
 * Analyze current page state using extract
 */
router.post("/analyze", async (req: Request, res: Response) => {
    try {
        const { sessionId } = CloseRequestSchema.parse(req.body);
        const stagehand = sessionManager.get(sessionId);

        if (!stagehand) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        wsManager.broadcastLog(sessionId, "Analyzing page...", "info");

        // Stagehand v3 - simple extract with string instruction
        // IMPORTANT: Detect unchecked required checkboxes FIRST
        const pageState = await stagehand.extract(
            `Analyze this page and return JSON with:
- pageType: "login" or "form" or "otp" or "captcha" or "success" or "error"
- formFields: list of visible input field labels
- hasUncheckedCheckbox: true if there's an unchecked checkbox (like "I hereby declare", "I agree", terms and conditions) that MUST be clicked first
- uncheckedCheckboxLabel: the label/text of the unchecked checkbox if any
- hasOtp: true if there's an OTP/verification code input
- hasCaptcha: true if there's a captcha
- buttons: list of button texts (especially submit/continue)
- errors: list of any error messages`
        );

        const screenshot = await captureAndBroadcast(sessionId, "analyze");

        res.json({
            success: true,
            analysis: pageState,
            screenshot,
        });
    } catch (error) {
        console.error("[analyze] Error:", error);
        res.json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/screenshot
 * Capture current page screenshot
 */
router.post("/screenshot", async (req: Request, res: Response) => {
    try {
        const { sessionId } = CloseRequestSchema.parse(req.body);
        const screenshot = await captureAndBroadcast(sessionId, "manual");

        if (!screenshot) {
            return res.status(404).json({ success: false, error: "Session not found" });
        }

        res.json({
            success: true,
            screenshot,
        });
    } catch (error) {
        console.error("[screenshot] Error:", error);
        res.status(500).json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * POST /api/close
 * Close browser session
 */
router.post("/close", async (req: Request, res: Response) => {
    try {
        const { sessionId } = CloseRequestSchema.parse(req.body);

        wsManager.broadcastLog(sessionId, "Closing browser...", "info");
        await sessionManager.close(sessionId);

        res.json({ success: true });
    } catch (error) {
        console.error("[close] Error:", error);
        res.status(500).json({
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
        });
    }
});

/**
 * GET /api/health
 * Health check endpoint
 */
router.get("/health", (_req: Request, res: Response) => {
    res.json({
        status: "ok",
        timestamp: new Date().toISOString(),
    });
});

export { router as apiRouter };