import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = 'C:\\Users\\LENOVO\\.gemini\\antigravity\\brain\\0ac0acc9-5a08-4838-a020-cc724a980acf\\walkthrough_screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function clickButtonWithText(page, text) {
  const found = await page.evaluate((btnText) => {
    const btns = Array.from(document.querySelectorAll('button'));
    const target = btns.find((b) => b.textContent.includes(btnText));
    if (target) {
      target.click();
      return true;
    }
    return false;
  }, text);
  return found;
}

async function run() {
  console.log('🚀 Launching Chrome for CareerPilot AI Module 4 Walkthrough...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    defaultViewport: { width: 1280, height: 900, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();

  try {
    // ----------------------------------------------------
    // STEP 1: Register and Login Candidate
    // ----------------------------------------------------
    const testEmail = `dev.jobseeker${Date.now()}@example.com`;
    console.log(`Step 1: Registering candidate ${testEmail}...`);
    await page.goto('http://localhost:5173/register', { waitUntil: 'domcontentloaded' });
    await sleep(1000);
    await page.type('#name', 'Rohan Sharma');
    await page.type('#email', testEmail);
    await page.type('#password', 'FresherPass123');
    await page.type('#confirmPassword', 'FresherPass123');
    await page.click('button[type="submit"]');

    await sleep(2000);
    console.log('Logging in...');
    await page.type('#password', 'FresherPass123');
    await page.click('button[type="submit"]');
    await sleep(2000);

    // ----------------------------------------------------
    // STEP 2: Navigate to /jobs (Initial Discovery Feed)
    // ----------------------------------------------------
    console.log('Step 2: Navigating to /jobs (Job Discovery Hub)...');
    await page.goto('http://localhost:5173/jobs', { waitUntil: 'domcontentloaded' });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_01_job_discovery_initial.png') });
    console.log('📸 Captured m4_01_job_discovery_initial.png');

    // ----------------------------------------------------
    // STEP 3: Click "Find Jobs" & View Discovery Summary
    // ----------------------------------------------------
    console.log('Step 3: Running Discovery (#btn-discover-jobs)...');
    await page.click('#btn-discover-jobs');

    // Wait for the discovery summary alert
    await page.waitForSelector('.bg-emerald-50', { timeout: 15000 });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_02_discovery_summary_alert.png') });
    console.log('📸 Captured m4_02_discovery_summary_alert.png');

    // ----------------------------------------------------
    // STEP 4: Filter by Role & Fresher Only
    // ----------------------------------------------------
    console.log('Step 4: Filtering for Python Fresher opportunities...');
    await clickButtonWithText(page, 'Python');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_03_fresher_filtered_feed.png') });
    console.log('📸 Captured m4_03_fresher_filtered_feed.png');

    // ----------------------------------------------------
    // STEP 5: View Job Details
    // ----------------------------------------------------
    console.log('Step 5: Opening Job Details page...');
    // Click View Details on first card
    await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const viewLink = links.find((l) => l.textContent.includes('View Details'));
      if (viewLink) viewLink.click();
    });
    await sleep(2000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_04_job_details_view.png') });
    console.log('📸 Captured m4_04_job_details_view.png');

    // ----------------------------------------------------
    // STEP 6: Save the Job
    // ----------------------------------------------------
    console.log('Step 6: Saving the job (#btn-save-job)...');
    await page.click('#btn-save-job');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_05_job_saved_action.png') });
    console.log('📸 Captured m4_05_job_saved_action.png');

    // ----------------------------------------------------
    // STEP 7: View Saved Jobs Pipeline Tab
    // ----------------------------------------------------
    console.log('Step 7: Returning to /jobs and opening Saved Jobs tab...');
    await page.goto('http://localhost:5173/jobs', { waitUntil: 'domcontentloaded' });
    await sleep(1200);
    await clickButtonWithText(page, 'Saved Jobs');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_06_saved_jobs_pipeline.png') });
    console.log('📸 Captured m4_06_saved_jobs_pipeline.png');

    // ----------------------------------------------------
    // STEP 8: Dashboard Integration
    // ----------------------------------------------------
    console.log('Step 8: Navigating to Dashboard to view Module 4 status and Saved count...');
    await page.goto('http://localhost:5173/dashboard', { waitUntil: 'domcontentloaded' });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_07_dashboard_jobs_widget.png') });
    console.log('📸 Captured m4_07_dashboard_jobs_widget.png');

    console.log('✅ Module 4 Walkthrough completed successfully!');
  } catch (err) {
    console.error('❌ Walkthrough Error:', err);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm4_error.png') });
    throw err;
  } finally {
    await browser.close();
  }
}

run();
