// workflow.ts

// Setup Instructions:
// 1. Install all dependencies:
//    pnpm add @browserbasehq/stagehand@latest zod
//    pnpm add -D tsx typescript @types/node
//
// 2. Create a .env file with your API keys:
//    BROWSERBASE_API_KEY=your-browserbase-api-key
//    BROWSERBASE_PROJECT_ID=your-browserbase-project-id
//    GEMINI_API_KEY=your-google-api-key
//
// 3. Run the workflow:
//    pnpm exec tsx workflow.ts

// Generated script for workflow 61235344-721e-4649-8962-b52d0f79a153
// Generated at 2025-12-13T20:28:19.250Z

import { Stagehand } from "@browserbasehq/stagehand";
import { z } from 'zod';
import StagehandConfig from "./stagehand.config.js";

// Stagehand configuration for local execution

export type ProgressCallback = (message: string) => void;

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

export async function runWorkflow(
  data: FormData,
  onProgress?: ProgressCallback
) {
  let stagehand: Stagehand | null = null;
  
  const log = (message: string) => {
    console.log(message);
    onProgress?.(message);
  };

  try {
    // Initialize Stagehand
    log('Initializing Stagehand...');
    stagehand = new Stagehand(StagehandConfig);
    await stagehand.init();
    console.log('Stagehand initialized successfully.');

    // Get the page instance
    const page: any = (stagehand as any).page ?? stagehand.context.pages()[0];
    if (!page) {
      throw new Error('Failed to get page instance from Stagehand');
    }

    const variables = {
      input1: '11/07/2005',
      input2: '11',
      input3: 'MM',
      input4: '11',
      input5: '11/07/2005',
    };

    // Step 1: Navigate to URL
    console.log('Navigating to: https://upsconline.nic.in/');
    await page.goto('https://upsconline.nic.in/');
    
    // Step 2: Perform action
    console.log(`Performing action: type '${data.fullName}' into the Full Name field`);
    await page.act(`type '${data.fullName}' into the Full Name field`);
    
    // Step 3: Perform action
    console.log(
      `Performing action: type '${data.mobileNumber}' into the Mobile Number field`,
    );
    await page.act(`type '${data.mobileNumber}' into the Mobile Number field`);
    
    // Step 4: Perform action
    console.log(
      `Performing action: type '${data.guardianMobileNumber}' into the Guardian Mobile Number field`,
    );
    await page.act(
      `type '${data.guardianMobileNumber}' into the Guardian Mobile Number field`,
    );
    
    // Step 5: Perform action
    console.log(
      `Performing action: type '${data.nearestCenter}' into the Preferred Admission/Nearest Center field`,
    );
    await page.act(
      `type '${data.nearestCenter}' into the Preferred Admission/Nearest Center field`,
    );
    
    // Step 6: Perform action
    console.log(`Performing action: type '${data.currentClass}' into the Current Class field`);
    await page.act(`type '${data.currentClass}' into the Current Class field`);
    
    // Step 7: Perform action
    console.log(
      `Performing action: type '${data.offeredCourses}' into the Offered Courses field`,
    );
    await page.act(
      `type '${data.offeredCourses}' into the Offered Courses field`,
    );
    
    // Step 8: Perform action
    console.log(
      `Performing action: type '${data.schoolName}' into the School Name field`,
    );
    await page.act(`type '${data.schoolName}' into the School Name field`);
    
    // Step 9: Perform action
    console.log(`Performing action: type '${data.pincode}' into the Pincode field`);
    await page.act(`type '${data.pincode}' into the Pincode field`);
    
    // Scroll: Scrolled to top of page
    await page.evaluate(() => {
      window.scrollTo(0, 0);
    });
    
    // Scroll: Scrolled down xs (10%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 10) / 100;
      window.scrollBy(0, scrollAmount);
    });
    
    // Step 12: Perform action
    log(`Performing action: click the Vidyapeeth radio button`);
    await page.act(`click the Vidyapeeth radio button`);
    
    // Scroll: Scrolled down lg (100%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 100) / 100;
      window.scrollBy(0, scrollAmount);
    });
    
    // Scroll: Scrolled down md (50%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 50) / 100;
      window.scrollBy(0, scrollAmount);
    });
    
    // Step 15: Perform action
    console.log(`Performing action: click the Date of Birth input field`);
    await page.act(`click the Date of Birth input field`);
    
    // Step 16: Perform action
    console.log(
      `Performing action: type the date of birth in mm/dd/yyyy format`,
    );
    await page.act(`type the date of birth in mm/dd/yyyy format`);
    
    // Step 17: Perform action
    console.log(`Performing action: click the date picker calendar button`);
    await page.act(`click the date picker calendar button`);
    
    // Step 18: Perform action
    console.log(
      `Performing action: click the Month spinbutton in the Date of Birth field`,
    );
    await page.act(
      `click the Month spinbutton in the Date of Birth field`,
    );
    
    // Step 19: Perform action
    console.log(`Performing action: type 11 into the month field`);
    await page.act(`type 11 into the month field`);
    
    // Step 20: Perform action
    console.log(
      `Performing action: triple-click on the date input field to select all text`,
    );
    await page.act(
      `triple-click on the date input field to select all text`,
    );
    
    // Step 21: Perform action
    console.log(`Performing action: click the Show date picker button`);
    await page.act(`click the Show date picker button`);
    
    // Step 22: Perform action
    console.log(`Performing action: click on the date input field`);
    await page.act(`click on the date input field`);
    
    // Step 23: Perform action
    console.log(`Performing action: type the date without slashes`);
    await page.act(`type the date without slashes`);
    
    // Step 24: Perform action
    console.log(`Performing action: click on the Month spinbutton`);
    await page.act(`click on the Month spinbutton`);
    
    // Scroll: Scrolled up sm (25%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 25) / 100;
      window.scrollBy(0, -scrollAmount);
    });
    
    // Step 26: Perform action
    console.log(`Performing action: click on the mm part of the date field`);
    await page.act(`click on the mm part of the date field`);
    
    // Step 27: Perform action
    console.log(`Performing action: type 11 for the month`);
    await page.act(`type 11 for the month`);
    
    // Step 28: Perform action
    console.log(`Performing action: click the calendar icon button`);
    await page.act(`click the calendar icon button`);
    
    // Scroll: Scrolled down sm (25%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 25) / 100;
      window.scrollBy(0, scrollAmount);
    });
    
    // Step 30: Perform action
    console.log(`Performing action: click on the date input field to focus it`);
    await page.act(`click on the date input field to focus it`);
    
    // Step 31: Perform action
    console.log(`Performing action: type the complete date ${data.dateOfBirth}`);
    await page.act(`type the complete date ${data.dateOfBirth}`);
    if (typeof page.keyPress === 'function') {
      await page.keyPress('Enter');
    } else {
      await page.keyboard.press('Enter');
    }
    
    // Scroll: Scrolled up xs (10%) of viewport
    await page.evaluate(() => {
      const viewportHeight = window.innerHeight;
      const scrollAmount = (viewportHeight * 10) / 100;
      window.scrollBy(0, -scrollAmount);
    });
    
    // Step 33: Perform action
    console.log(
      `Performing action: click directly on the mm text in the date field`,
    );
    await page.act(`click directly on the mm text in the date field`);
    
    // Step 34: Perform action
    console.log(`Performing action: click the Submit button`);
    await page.act(`click the Submit button`);
    

    console.log('Workflow completed successfully');
    return { success: true };
  } catch (error) {
    console.error('Workflow failed:', error);
    return { success: false, error };
  } finally {
    // Clean up
    if (stagehand) {
      console.log('Closing Stagehand connection.');
      try {
        await stagehand.close();
      } catch (err) {
        console.error('Error closing Stagehand:', err);
      }
    }
  }
}