// Shared helpers for per-PRD demo scripts. Each scene runs twice:
// 390x844 with video (mobile-first, the one the user watches) and 1440x900 without video (desktop screenshots).
// shot("02-filter") writes 02-filter-390.png and 02-filter-1440.png.
const path = require("path");
const fs = require("fs");
const { chromium } = require(path.join(__dirname, "..", "node_modules", "playwright"));

const PASSES = [
  { tag: "390", viewport: { width: 390, height: 844 }, video: true, isMobile: true },
  { tag: "1440", viewport: { width: 1440, height: 900 }, video: false, isMobile: false },
];

// The project hook: <repo>/.claude/prd-demo.cjs exporting { baseUrl, signIn(page, who, BASE) }.
function loadHook(repo) {
  const file = path.join(repo, ".claude", "prd-demo.cjs");
  if (!fs.existsSync(file)) {
    throw new Error(`prd-demo: missing ${file}. It must export { baseUrl, signIn(page, who, BASE) }.`);
  }
  const hook = require(file);
  if (typeof hook.signIn !== "function" || !hook.baseUrl) {
    throw new Error(`prd-demo: ${file} must export baseUrl (string) and signIn (function).`);
  }
  return hook;
}

async function run(outDir, scenes, { repo = process.cwd() } = {}) {
  const hook = loadHook(repo);
  const BASE = process.env.PRD_DEMO_BASE_URL || hook.baseUrl;
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  try {
    for (const pass of PASSES) {
      for (const [name, scene] of Object.entries(scenes)) {
        const ctx = await browser.newContext({
          viewport: pass.viewport,
          isMobile: pass.isMobile,
          hasTouch: pass.isMobile,
          ...(pass.video && { recordVideo: { dir: `${outDir}/video-${name}`, size: pass.viewport } }),
        });
        const page = await ctx.newPage();
        const api = {
          page,
          BASE,
          mobile: pass.isMobile,
          shot: (file) => page.screenshot({ path: `${outDir}/${file}-${pass.tag}.png`, fullPage: false }),
          // Pauses only matter on the filmed pass.
          pause: (ms = 900) => (pass.video ? page.waitForTimeout(ms) : Promise.resolve()),
          signIn: (who) => hook.signIn(page, who, BASE),
        };
        try {
          await scene(api);
        } finally {
          await ctx.close();
        }
      }
    }
  } finally {
    await browser.close();
  }
}

module.exports = { run };
