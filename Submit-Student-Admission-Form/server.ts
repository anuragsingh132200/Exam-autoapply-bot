import express, { type Request, type Response } from "express";
import { runWorkflow } from "./index.js";

const app = express();
app.use(express.json());

let isRunning = false;

app.get("/health", (_req: Request, res: Response) => {
  res.json({ ok: true });
});

app.post("/start", async (req: Request, res: Response) => {
  if (isRunning) {
    return res.status(409).json({ success: false, error: "Workflow already running" });
  }

  const {
    fullName,
    mobileNumber,
    guardianMobileNumber,
    nearestCenter,
    currentClass,
    offeredCourses,
    schoolName,
    pincode,
    dateOfBirth,
  } = req.body || {};

  if (!fullName || !mobileNumber || !guardianMobileNumber || !nearestCenter || !currentClass || !offeredCourses || !schoolName || !pincode || !dateOfBirth) {
    return res.status(400).json({ success: false, error: "Missing required fields" });
  }

  isRunning = true;
  try {
    const result = await runWorkflow({
      fullName,
      mobileNumber,
      guardianMobileNumber,
      nearestCenter,
      currentClass,
      offeredCourses,
      schoolName,
      pincode,
      dateOfBirth,
    });
    return res.status(result.success ? 200 : 500).json(result);
  } catch (error) {
    return res.status(500).json({ success: false, error });
  } finally {
    isRunning = false;
  }
});

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
  console.log(`POST /start to run the workflow`);
});
