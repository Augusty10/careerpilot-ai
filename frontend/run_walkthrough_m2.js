import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = 'C:\\Users\\LENOVO\\.gemini\\antigravity\\brain\\0ac0acc9-5a08-4838-a020-cc724a980acf\\walkthrough_screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  console.log('🚀 Launching Chrome for CareerPilot AI Module 2 Walkthrough...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    defaultViewport: { width: 1280, height: 800, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();

  try {
    // ----------------------------------------------------
    // STEP 1: Registration / Login
    // ----------------------------------------------------
    const testEmail = `alex.master${Date.now()}@example.com`;
    console.log(`Step 1: Registering candidate ${testEmail}...`);
    await page.goto('http://localhost:5173/register', { waitUntil: 'networkidle0' });
    await sleep(600);
    await page.type('#name', 'Alex Johnson');
    await page.type('#email', testEmail);
    await page.type('#password', 'FresherPass123');
    await page.type('#confirmPassword', 'FresherPass123');
    await page.click('button[type="submit"]');

    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(600);
    console.log('Logging in...');
    await page.type('#password', 'FresherPass123');
    await page.click('button[type="submit"]');

    // ----------------------------------------------------
    // STEP 2: Dashboard Incomplete Profile Prompt
    // ----------------------------------------------------
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(1000);
    console.log('Step 2: On Dashboard, verifying "Complete Profile" prompt...');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_01_dashboard_incomplete.png') });
    console.log('📸 Captured m2_01_dashboard_incomplete.png');

    // ----------------------------------------------------
    // STEP 3: Navigate to Profile Page (Empty Skeleton)
    // ----------------------------------------------------
    console.log('Step 3: Navigating to /profile...');
    await page.goto('http://localhost:5173/profile', { waitUntil: 'networkidle0' });
    await sleep(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_02_profile_initial_empty.png') });
    console.log('📸 Captured m2_02_profile_initial_empty.png');

    // ----------------------------------------------------
    // STEP 4: Upload Resume PDF for AI Extraction
    // ----------------------------------------------------
    console.log('Step 4: Uploading Alex_Johnson_Fresher_Resume.pdf...');
    const resumePath = path.resolve('Alex_Johnson_Fresher_Resume.pdf');
    const fileInput = await page.$('input[type="file"]');
    await fileInput.uploadFile(resumePath);

    console.log('Waiting for AI extraction to complete...');
    // Wait for the AI warning banner to appear
    await page.waitForSelector('.bg-amber-50', { timeout: 15000 });
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_03_ai_extracted_banner.png') });
    console.log('📸 Captured m2_03_ai_extracted_banner.png');

    // ----------------------------------------------------
    // STEP 5: Review Extracted Sections
    // ----------------------------------------------------
    console.log('Step 5: Reviewing Education tab...');
    // Click Education tab
    const eduTab = await page.evaluateHandle(() => {
      const tabs = Array.from(document.querySelectorAll('button'));
      return tabs.find((b) => b.textContent.includes('Education'));
    });
    await eduTab.click();
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_04_education_extracted.png') });
    console.log('📸 Captured m2_04_education_extracted.png');

    console.log('Reviewing Skills tab...');
    const skillsTab = await page.evaluateHandle(() => {
      const tabs = Array.from(document.querySelectorAll('button'));
      return tabs.find((b) => b.textContent.includes('Skills'));
    });
    await skillsTab.click();
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_05_skills_extracted.png') });
    console.log('📸 Captured m2_05_skills_extracted.png');

    console.log('Reviewing Projects tab...');
    const projTab = await page.evaluateHandle(() => {
      const tabs = Array.from(document.querySelectorAll('button'));
      return tabs.find((b) => b.textContent.includes('Projects'));
    });
    await projTab.click();
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_06_projects_extracted.png') });
    console.log('📸 Captured m2_06_projects_extracted.png');

    // ----------------------------------------------------
    // STEP 6: Edit & Save Draft
    // ----------------------------------------------------
    console.log('Step 6: Editing details and saving draft...');
    const personalTab = await page.evaluateHandle(() => {
      const tabs = Array.from(document.querySelectorAll('button'));
      return tabs.find((b) => b.textContent.includes('Personal'));
    });
    await personalTab.click();
    await sleep(600);

    // Click Save Draft button
    const saveDraftBtn = await page.evaluateHandle(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.find((b) => b.textContent.includes('Save Draft'));
    });
    await saveDraftBtn.click();
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_07_draft_saved.png') });
    console.log('📸 Captured m2_07_draft_saved.png');

    // ----------------------------------------------------
    // STEP 7: Approve & Save Master Profile
    // ----------------------------------------------------
    console.log('Step 7: Approving Master Profile...');
    const approveBtn = await page.evaluateHandle(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.find((b) => b.textContent.includes('Approve & Save'));
    });
    await approveBtn.click();
    await sleep(1800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_08_profile_approved.png') });
    console.log('📸 Captured m2_08_profile_approved.png');

    // ----------------------------------------------------
    // STEP 8: Reload Page to Verify Persistence
    // ----------------------------------------------------
    console.log('Step 8: Reloading page to verify data persistence...');
    await page.reload({ waitUntil: 'networkidle0' });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_09_reloaded_persistence.png') });
    console.log('📸 Captured m2_09_reloaded_persistence.png');

    // ----------------------------------------------------
    // STEP 9: Check Dashboard Approved State
    // ----------------------------------------------------
    console.log('Step 9: Navigating to Dashboard to verify approved banner...');
    await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle0' });
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_10_dashboard_approved_status.png') });
    console.log('📸 Captured m2_10_dashboard_approved_status.png');

    console.log('🎉 Module 2 browser walkthrough completed successfully with all screenshots saved!');
  } catch (err) {
    console.error('Walkthrough error:', err);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm2_error.png') });
  } finally {
    await browser.close();
  }
}

run();

