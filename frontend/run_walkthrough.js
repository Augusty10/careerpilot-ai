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
  console.log('🚀 Launching Chrome for CareerPilot AI Walkthrough...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    defaultViewport: { width: 1280, height: 800, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();

  try {
    // ----------------------------------------------------
    // STEP 1: Registration Page
    // ----------------------------------------------------
    console.log('Step 1: Navigating to Register page...');
    await page.goto('http://localhost:5173/register', { waitUntil: 'networkidle0' });
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_register_page.png') });
    console.log('📸 Captured 01_register_page.png');

    // Fill in registration form
    console.log('Filling registration form for Alex Fresh...');
    await page.type('#name', 'Alex Fresh');
    await page.type('#email', 'alex.fresh@example.com');
    await page.type('#password', 'FresherPass123');
    await page.type('#confirmPassword', 'FresherPass123');
    await sleep(400);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_register_filled.png') });
    console.log('📸 Captured 02_register_filled.png');

    // Submit form
    console.log('Submitting registration form...');
    await page.click('button[type="submit"]');

    // ----------------------------------------------------
    // STEP 2: Login Redirect & Submission
    // ----------------------------------------------------
    console.log('Step 2: Waiting for redirect to /login with success notification...');
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_registered_redirect_login.png') });
    console.log('📸 Captured 03_registered_redirect_login.png');

    console.log('Signing in with created credentials...');
    // Type password
    await page.type('#password', 'FresherPass123');
    await sleep(400);
    await page.click('button[type="submit"]');

    // ----------------------------------------------------
    // STEP 3: Dashboard View
    // ----------------------------------------------------
    console.log('Step 3: Waiting for Dashboard load...');
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_dashboard.png') });
    console.log('📸 Captured 04_dashboard.png');

    // ----------------------------------------------------
    // STEP 4: Settings Page & Updates
    // ----------------------------------------------------
    console.log('Step 4: Navigating to Account Settings...');
    await page.goto('http://localhost:5173/settings', { waitUntil: 'networkidle0' });
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_settings_page.png') });
    console.log('📸 Captured 05_settings_page.png');

    // Update Name
    console.log('Updating user name to Alex Career...');
    await page.click('#name', { clickCount: 3 });
    await page.keyboard.press('Backspace');
    await page.type('#name', 'Alex Career');
    await sleep(300);
    // Click the first submit button (Save Changes)
    const buttons = await page.$$('button[type="submit"]');
    await buttons[0].click();
    await sleep(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_name_updated.png') });
    console.log('📸 Captured 06_name_updated.png');

    // Change Password
    console.log('Changing password to NewFresherPass456...');
    await page.type('#currentPassword', 'FresherPass123');
    await page.type('#newPassword', 'NewFresherPass456');
    await page.type('#confirmNewPassword', 'NewFresherPass456');
    await sleep(300);
    const updatedButtons = await page.$$('button[type="submit"]');
    await updatedButtons[1].click();
    await sleep(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_password_changed.png') });
    console.log('📸 Captured 07_password_changed.png');

    // ----------------------------------------------------
    // STEP 5: Logout Flow
    // ----------------------------------------------------
    console.log('Step 5: Logging out...');
    // Find logout button in navbar
    const logoutBtn = await page.evaluateHandle(() => {
      const allButtons = Array.from(document.querySelectorAll('button'));
      return allButtons.find((b) => b.textContent.includes('Logout'));
    });
    if (logoutBtn) {
      await logoutBtn.click();
    } else {
      await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle0' });
    }
    await sleep(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_logged_out.png') });
    console.log('📸 Captured 08_logged_out.png');

    // ----------------------------------------------------
    // STEP 6: Forgot Password Flow
    // ----------------------------------------------------
    console.log('Step 6: Navigating to Forgot Password page...');
    await page.goto('http://localhost:5173/forgot-password', { waitUntil: 'networkidle0' });
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_forgot_password_page.png') });
    console.log('📸 Captured 09_forgot_password_page.png');

    console.log('Requesting password reset for alex.fresh@example.com...');
    await page.type('#email', 'alex.fresh@example.com');
    await sleep(300);
    await page.click('button[type="submit"]');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_forgot_password_success.png') });
    console.log('📸 Captured 10_forgot_password_success.png');

    // ----------------------------------------------------
    // STEP 7: Reset Password with Token
    // ----------------------------------------------------
    console.log('Step 7: Reading generated reset token...');
    let resetToken = '';
    const tokenFilePath = path.resolve('.latest_reset_token.txt');
    if (fs.existsSync(tokenFilePath)) {
      resetToken = fs.readFileSync(tokenFilePath, 'utf-8').trim();
      console.log(`Retrieved token from disk: ${resetToken}`);
    }

    const resetUrl = `http://localhost:5173/reset-password?token=${resetToken}`;
    console.log(`Navigating to ${resetUrl}...`);
    await page.goto(resetUrl, { waitUntil: 'networkidle0' });
    await sleep(800);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11_reset_password_page.png') });
    console.log('📸 Captured 11_reset_password_page.png');

    console.log('Entering final new password ResetPassFinal789...');
    await page.type('#password', 'ResetPassFinal789');
    await page.type('#confirmPassword', 'ResetPassFinal789');
    await sleep(300);
    await page.click('button[type="submit"]');
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '12_reset_password_success.png') });
    console.log('📸 Captured 12_reset_password_success.png');

    // ----------------------------------------------------
    // STEP 8: Login with Final Reset Password
    // ----------------------------------------------------
    console.log('Step 8: Logging in with final reset password...');
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle0' });
    await sleep(600);
    await page.type('#email', 'alex.fresh@example.com');
    await page.type('#password', 'ResetPassFinal789');
    await sleep(300);
    await page.click('button[type="submit"]');

    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    await sleep(1200);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '13_dashboard_with_new_password.png') });
    console.log('📸 Captured 13_dashboard_with_new_password.png');

    console.log('🎉 Browser walkthrough completed successfully with all screenshots saved!');
  } catch (error) {
    console.error('Walkthrough failed:', error);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'error_state.png') });
  } finally {
    await browser.close();
  }
}

run();

