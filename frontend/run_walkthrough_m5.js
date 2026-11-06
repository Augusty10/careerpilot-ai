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
  console.log('🚀 Launching Chrome for CareerPilot AI Module 5 Walkthrough...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    defaultViewport: { width: 1280, height: 900, deviceScaleFactor: 1 },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(45000);

  try {
    // ----------------------------------------------------
    // STEP 1: Register and Login Candidate
    // ----------------------------------------------------
    const testEmail = `matcher.candidate${Date.now()}@example.com`;
    console.log(`Step 1: Registering candidate ${testEmail}...`);
    await page.goto('http://127.0.0.1:5173/register', { waitUntil: 'domcontentloaded' });
    await sleep(1000);
    await page.type('#name', 'Ananya Verma');
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
    // STEP 2: Setup & Approve Master Profile
    // ----------------------------------------------------
    console.log('Step 2: Approving Master Profile...');
    await page.goto('http://127.0.0.1:5173/profile', { waitUntil: 'domcontentloaded' });
    await sleep(1500);

    // Approve Profile directly via API
    const token = await page.evaluate(() => localStorage.getItem('token') || sessionStorage.getItem('token'));
    await page.evaluate(async (tok) => {
      // Seed rich master profile
      const prof = {
        personal: {
          full_name: 'Ananya Verma',
          email: 'ananya@example.com',
          phone: '+91 9876543210',
          location: 'Bengaluru, India',
          github_url: 'https://github.com/ananya-v'
        },
        education: [{
          degree: 'B.Tech Computer Science and Engineering',
          institution: 'RV College of Engineering',
          graduation_year: 2025,
          score_type: 'cgpa',
          score: 8.9
        }],
        skills: {
          languages: ['Python', 'SQL', 'JavaScript'],
          frameworks: ['Flask', 'React'],
          databases: ['MongoDB', 'PostgreSQL'],
          tools: ['Git', 'VS Code'],
          other: ['REST APIs']
        },
        projects: [{
          title: 'Campus Placement Portal',
          description: 'Full stack recruitment platform built with Flask and React.',
          tech_stack: ['Python', 'Flask', 'MongoDB', 'React'],
          link: 'https://github.com/ananya-v/placement-portal'
        }],
        internships: [{
          company: 'Nexus Software',
          role: 'Backend Engineering Intern',
          start_date: '2024-05',
          end_date: '2024-08',
          description: 'Developed Python REST endpoints and database schemas.'
        }],
        certifications: [],
        achievements: ['Won 1st prize in Smart City Hackathon 2024'],
        work_experience: [],
        preferred_roles: ['Python Developer', 'Full Stack Developer', 'Backend Engineer'],
        preferred_locations: ['Bengaluru', 'Remote']
      };
      await fetch('http://127.0.0.1:5000/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
        body: JSON.stringify(prof)
      });
      await fetch('http://127.0.0.1:5000/api/profile/approve', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tok}` }
      });
      // Also trigger job discovery so sample jobs are populated in DB
      await fetch('http://127.0.0.1:5000/api/jobs/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
        body: JSON.stringify({})
      });
    }, token);

    await sleep(2000);

    // ----------------------------------------------------
    // STEP 3: Navigate to Job Discovery and select a fresher job
    // ----------------------------------------------------
    console.log('Step 3: Opening Fresher Job in Discovery...');
    await page.goto('http://127.0.0.1:5173/jobs', { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // Open Junior Python Developer job
    await page.goto('http://127.0.0.1:5173/jobs/sample-001', { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // Capture screenshot: Job Details Initial with Check Match CTA
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_01_fresher_job_check_match.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_01_fresher_job_check_match.png');

    // ----------------------------------------------------
    // STEP 4: Compute Match and View Breakdown
    // ----------------------------------------------------
    console.log('Step 4: Computing Eligibility and Match Breakdown...');
    const checkBtn = await page.$('#btn-check-match');
    if (checkBtn) {
      await checkBtn.click();
      await sleep(2500);
    }

    // Capture screenshot: Comprehensive Match Breakdown
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_02_match_breakdown_view.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_02_match_breakdown_view.png');

    // ----------------------------------------------------
    // STEP 5: Open experienced job requiring 5+ years experience
    // ----------------------------------------------------
    console.log('Step 5: Testing Not Eligible criteria on Senior Job (sample-016)...');
    // Seed or open an experienced job
    await page.evaluate(async (tok) => {
      await fetch('http://127.0.0.1:5000/api/matches/sample-016', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tok}` }
      });
    }, token);

    await page.goto('http://127.0.0.1:5173/jobs/sample-016', { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // If check button exists, click it
    const checkBtnSenior = await page.$('#btn-check-match');
    if (checkBtnSenior) {
      await checkBtnSenior.click();
      await sleep(2000);
    }

    // Capture screenshot: Not Eligible reason with hard failure notice
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_03_not_eligible_reason.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_03_not_eligible_reason.png');

    // ----------------------------------------------------
    // STEP 6: Edit Profile Skills & Check Out-of-date Notice
    // ----------------------------------------------------
    console.log('Step 6: Editing profile to demonstrate staleness detection...');
    await page.evaluate(async (tok) => {
      // Modify profile by adding Docker to tools
      const getRes = await fetch('http://127.0.0.1:5000/api/profile', {
        headers: { 'Authorization': `Bearer ${tok}` }
      });
      const data = await getRes.json();
      const prof = data.profile;
      prof.skills.tools.push('Docker');
      prof.skills.tools.push('Kubernetes');
      await fetch('http://127.0.0.1:5000/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
        body: JSON.stringify(prof)
      });
      await fetch('http://127.0.0.1:5000/api/profile/approve', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tok}` }
      });
    }, token);

    // Return to the fresher job details page
    await page.goto('http://127.0.0.1:5173/jobs/sample-001', { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // Capture screenshot: Out of Date notice
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_04_out_of_date_notice.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_04_out_of_date_notice.png');

    // ----------------------------------------------------
    // STEP 7: Recompute Match
    // ----------------------------------------------------
    console.log('Step 7: Recomputing match with updated skills...');
    const recomputeBtn = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const target = btns.find(b => b.textContent.includes('Recompute Match'));
      if (target) {
        target.click();
        return true;
      }
      return false;
    });

    await sleep(2500);

    // Capture screenshot: Recomputed Match
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_05_recomputed_match.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_05_recomputed_match.png');

    // ----------------------------------------------------
    // STEP 8: Navigate to Recommended Jobs Page
    // ----------------------------------------------------
    console.log('Step 8: Navigating to Recommended Jobs page...');
    await page.goto('http://127.0.0.1:5173/jobs/recommended', { waitUntil: 'domcontentloaded' });
    await sleep(2500);

    // Capture screenshot: Recommended Jobs ranked by category & coverage
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_06_recommended_jobs_ranked.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_06_recommended_jobs_ranked.png');

    // ----------------------------------------------------
    // STEP 9: Navigate to Dashboard to verify Match Stats
    // ----------------------------------------------------
    console.log('Step 9: Checking Dashboard Match Metrics...');
    await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // Capture screenshot: Dashboard with Module 5 active & metrics
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_07_dashboard_match_widget.png'),
      fullPage: true,
    });
    console.log('📸 Captured: m5_07_dashboard_match_widget.png');

    console.log('🎉 All 7 Module 5 walkthrough screenshots captured successfully!');
  } catch (err) {
    console.error('Walkthrough failed:', err);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'm5_error.png'),
      fullPage: true,
    });
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
