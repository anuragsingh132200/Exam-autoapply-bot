// workflow.ts
import { Stagehand } from "@browserbasehq/stagehand";
import StagehandConfig from "./stagehand.config.js";

export interface FormData {
  fullName: string;
  mobileNumber: string;
  guardianMobileNumber: string;
  mailId: string;
  nearestCenter: string;
  currentClass: string;
  offeredCourses: string;
  schoolName: string;
  pincode: string;
  dateOfBirth: string;
}

export type ProgressCallback = (message: string) => void;
export type GetOtpFn = () => Promise<string>;

export async function runWorkflow(
  data: FormData,
  getOtp: GetOtpFn,
  onProgress?: ProgressCallback
) {
  let stagehand: Stagehand | null = null;

  const log = (msg: string) => {
    console.log(msg);
    onProgress?.(msg);
  };

  try {
    log("Initializing Stagehand...");
    stagehand = new Stagehand(StagehandConfig);
    await stagehand.init();

    const page: any =
      (stagehand as any).page ?? stagehand.context.pages()[0];

    if (!page) throw new Error("Page not found");

    log("Navigating to NSAT page");
    await page.goto("https://www.pw.live/scholarship/vidyapeeth/nsat");

    log("Clicking login");
    await page.act("click on login button");

    log("Entering mobile number");
    await page.act(`type '${data.mobileNumber}' into mobile number field`);
    await page.act("click on continue button");

    // ⏸️ WAIT FOR OTP FROM FRONTEND
    log("Waiting for OTP from user...");
    const otp = await getOtp();

    log("OTP received. Filling OTP...");
    await page.act(`type '${otp}' into otp input field`);
    await page.act("click on continue button");


    await page.act("select exam as IITJEE in the exam dropdown");
    
    await page.act("select 12th as class  in the class dropdown");
    await page.act("click on submit button");
    
    log("Login successful. Workflow completed.");
    return { success: true };
  } catch (err) {
    log("Workflow failed");
    throw err;
  } finally {
    if (stagehand) {
      await stagehand.close();
    }
  }
}
