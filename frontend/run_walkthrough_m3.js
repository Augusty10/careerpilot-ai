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
  console.log('🚀 Launching Chrome for CareerPilot AI Module 3 Walkthrough...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    defaultViewport: { width: 1280, height: 900, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();

  try {
    // ----------------------------------------------------
    // STEP 1: Register and Login
    // ----------------------------------------------------
    const testEmail = `jordan.fresher${Date.now()}@example.com`;
    console.log(`Step 1: Registering candidate ${testEmail}...`);
    await page.goto('http://localhost:5173/register', { waitUntil: 'networkidle0' });
    await sleep(600);
    await page.type('#name', 'Jordan Smith');
    await page.type('#email', testEmail);
    await page.type('#password', 'FresherPass123');
    await page.type('#confirmPassword', 'FresherPass123');
    await page.click('button[type="submit"]');

    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(600);
    console.log('Logging in...');
    await page.type('#password', 'FresherPass123');
    await page.click('button[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(1000);

    // ----------------------------------------------------
    // STEP 2: Navigate to /profile, Upload Resume, and Approve
    // ----------------------------------------------------
    console.log('Step 2: Uploading resume and approving master profile...');
    await page.goto('http://localhost:5173/profile', { waitUntil: 'networkidle0' });
    await sleep(1000);

    const resumePath = path.resolve('Alex_Johnson_Fresher_Resume.pdf');
    const fileInput = await page.$('input[type="file"]');
    await fileInput.uploadFile(resumePath);

    // Wait for AI extraction
    await page.waitForSelector('.bg-amber-50', { timeout: 15000 });
    await sleep(1000);

    // Click Save Draft
    console.log('Saving Draft...');
    await clickButtonWithText(page, 'Save Draft');
    await sleep(1500);

    // Click Approve & Save
    console.log('Approving Master Profile...');
    await clickButtonWithText(page, 'Approve & Save');
    await sleep(1800);
    console.log('Master profile approved.');

    // ----------------------------------------------------
    // STEP 3: Navigate to /resumes (Empty State)
    // ----------------------------------------------------
    console.log('Step 3: Navigating to /resumes...');
    await page.goto('http://localhost:5173/resumes', { waitUntil: 'networkidle0' });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_01_resume_builder_empty.png') });
    console.log('📸 Captured m3_01_resume_builder_empty.png');

    // ----------------------------------------------------
    // STEP 4: Generate Single Resume (Full Stack Developer)
    // ----------------------------------------------------
    console.log('Step 4: Generating Full Stack Developer resume...');
    await clickButtonWithText(page, 'Generate Full Stack Developer Resume');

    // Wait for generation
    await page.waitForSelector('.shadow-sm.hover\\:shadow-md', { timeout: 20000 });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_02_resume_generated_card.png') });
    console.log('📸 Captured m3_02_resume_generated_card.png');

    // ----------------------------------------------------
    // STEP 5: Generate Second Version (Version Auto-Increment)
    // ----------------------------------------------------
    console.log('Step 5: Generating second version of Full Stack Developer...');
    await clickButtonWithText(page, 'Generate Full Stack Developer Resume');
    await sleep(3500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_03_version_incremented.png') });
    console.log('📸 Captured m3_03_version_incremented.png');

    // ----------------------------------------------------
    // STEP 6: Multi-Role Batch Generation
    // ----------------------------------------------------
    console.log('Step 6: Testing Multi-Role Batch Generation...');
    await clickButtonWithText(page, 'Multi-Role Batch');
    await sleep(800);

    // Submit batch
    await clickButtonWithText(page, 'Generate');
    await sleep(4000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_04_batch_generated_library.png') });
    console.log('📸 Captured m3_04_batch_generated_library.png');

    // ----------------------------------------------------
    // STEP 7: Live ATS Preview (Modern & Classic)
    // ----------------------------------------------------
    console.log('Step 7: Opening Live ATS Preview...');
    await clickButtonWithText(page, 'Preview');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_05_live_ats_preview_modern.png') });
    console.log('📸 Captured m3_05_live_ats_preview_modern.png');

    // Switch to Classic in preview modal
    await clickButtonWithText(page, 'Classic');
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_06_live_ats_preview_classic.png') });
    console.log('📸 Captured m3_06_live_ats_preview_classic.png');

    // Close preview modal
    await clickButtonWithText(page, '✕');
    await sleep(800);

    // ----------------------------------------------------
    // STEP 8: Edit Resume & Save
    // ----------------------------------------------------
    console.log('Step 8: Opening Resume Editor...');
    await clickButtonWithText(page, 'Edit');
    await sleep(1200);

    // Edit summary
    const summaryInput = await page.$('textarea');
    if (summaryInput) {
      await summaryInput.click({ clickCount: 3 });
      await summaryInput.type('Customized summary by candidate with high-impact software engineering accomplishments.');
    }
    await sleep(500);

    // Save edits
    await clickButtonWithText(page, 'Save & Update Resume');
    await sleep(2500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_07_resume_edited_saved.png') });
    console.log('📸 Captured m3_07_resume_edited_saved.png');

    // ----------------------------------------------------
    // STEP 9: Outdated Warning Badge Verification
    // ----------------------------------------------------
    console.log('Step 9: Modifying Master Profile to verify Outdated Warning Badge...');
    await page.goto('http://localhost:5173/profile', { waitUntil: 'networkidle0' });
    await sleep(1000);
    // Click Save Draft on profile to update master updated_at
    await clickButtonWithText(page, 'Save Draft');
    await sleep(1800);

    // Return to /resumes
    await page.goto('http://localhost:5173/resumes', { waitUntil: 'networkidle0' });
    await sleep(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_08_outdated_warning_badge.png') });
    console.log('📸 Captured m3_08_outdated_warning_badge.png');

    // ----------------------------------------------------
    // STEP 10: Dashboard Integration
    // ----------------------------------------------------
    console.log('Step 10: Navigating to Dashboard to view Module 3 status...');
    await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle0' });
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_09_dashboard_module3_active.png') });
    console.log('📸 Captured m3_09_dashboard_module3_active.png');

    console.log('✅ Module 3 Walkthrough successfully completed!');
  } catch (err) {
    console.error('❌ Walkthrough Error:', err);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'm3_error.png') });
    throw err;
  } finally {
    await browser.close();
  }
}

run();
