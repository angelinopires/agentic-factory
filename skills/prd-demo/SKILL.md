---
name: prd-demo
description: Record the visual evidence package for a UI PRD (screenshots at 390px and 1440px, MP4 video and GIF at 390px) using Playwright against the running local stack so the user can review the feature without opening a browser. Runs only when the PRD header has `**Demo:** yes`, after QA passes. Use when QA finishes verifying a PRD with Demo enabled, or when the user asks to "record the demo", "take feature screenshots", or "record PRD video". Does NOT replace QA or live A/B comparison testing; for presentation videos with cursor animation and storytelling, use `ui-demo` (ECC).
argument-hint: "<path to PRD> [what to showcase]"
---

# /prd-demo — Screenshots and Video for a UI PRD

Generates visual evidence for the user's final review. Complements QA: the GREENLIGHT/HOLD verdict still belongs to QA (`/prd-ship`).

## Entry Conditions

1. **Gate.** Read the PRD header. Without `**Demo:** yes` → stop and report `"PRD has Demo disabled: nothing to record"`. The user decides this field during `/prd`; never infer it.
2. **Running stack.** Use the local environment that QA already started (Docker Compose, worktree, dev server). Do not spin up a throwaway database or custom seed. If the port differs from the project hook default (e.g., a worktree running on `:5174`), set `PRD_DEMO_BASE_URL=http://localhost:5174`.
3. **Project hook.** `<repo>/.claude/prd-demo.cjs` must exist and export:
   ```js
   module.exports = {
     baseUrl: "http://localhost:5173",
     async signIn(page, who, BASE) { /* leaves `page` signed in as `who` */ },
   };
   ```
   If the file is missing, the recorder stops with a clear error message stating what is required. Never improvise login flows inside the scene script: the hook is written once per project, via a project PRD.

## Steps

`$SKILL` = directory of this skill (`skills/prd-demo`). `$S` = session scratchpad directory. `$OUT` = `${PRD_DEMO_OUT:-.maestri/demos}/<project>/<prd-slug>`.

1. **Plan states.** From Part 4 of the PRD and the states validated by QA, list 4 to 10 states that prove the feature works, including empty or error states when visually relevant. Group them into scenes: one scene per role or flow (e.g., `user`, `admin`).
2. **Discover and rehearse.** Before recording, verify that every selector resolves, following the *Discover* and *Rehearse* phases of the `ui-demo` skill. Use accessible locators (`getByRole`, `getByLabel`), never brittle CSS classes.
3. **Write the scene script.** Create `$S/record.cjs`:
   ```js
   const { run } = require(process.env.RECORDER);
   run(process.argv[2], {
     user: async ({ page, BASE, signIn, shot, pause, mobile }) => {
       await signIn("qa@example.test");
       await page.goto(`${BASE}/items`);
       await page.getByRole("heading", { name: /items/i }).waitFor();
       await shot("01-list");
       await page.getByRole("button", { name: /filter/i }).click();
       await pause();
       await shot("02-filter-open");
     },
   }, { repo: process.argv[3] }).catch((e) => { console.error(e.message); process.exit(1); });
   ```
   Each scene runs twice: at `390×844` with video and at `1440×900` without video. `shot("NN-name")` writes `NN-name-390.png` and `NN-name-1440.png`. When the layout differs between viewports (such as a mobile hamburger menu), branch on `mobile`. `pause()` only waits during the filmed mobile pass.
4. **Record.** Run `RECORDER=$SKILL/scripts/recorder.cjs node $S/record.cjs $OUT <repo>`.
5. **Encode.** Run `$SKILL/scripts/encode.sh $OUT` to generate `<scene>.mp4` and `<scene>.gif` (390px wide, 8 fps) using system `ffmpeg`. If a GIF exceeds ~10 MB, shorten the scene.
6. **Inspect.** Open every generated PNG before delivering. If a screenshot caught a loading spinner, login screen, or unexpected error → fix the script and re-record. Filename and visual content must match.
7. **Clean database.** The demo script should avoid mutating database state. If it had to write data (saving a form, creating an item, changing a role), undo the mutation via the app's API or CLI at the end of the run. Never run manual SQL against the database.
8. **Deliver.** In the QA report (or in your `REPORT` back to the Manager), include the `$OUT` directory path and one line per file explaining what it proves. The Manager forwards the media paths to the user alongside brief manual test steps for anything that still requires human interaction.

## Do Not

- Do not delete `$OUT` or older demo directories. Cleanup belongs to the user.
- Do not commit demo media files into the project repository or `planning/`.
- Do not record a demo for a PRD without `**Demo:** yes`.
- Do not treat the demo as the QA verdict: a demo only shows the scripted path, whereas QA remains the verification gate.

## Installation (once per machine)

Playwright lives inside the skill folder so individual projects do not need it as a dependency:

```bash
cd ~/.claude/skills/prd-demo && npm i && npx playwright install chromium
```

System `ffmpeg`: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).

## Harness portability

- Inspecting PNGs (`Read` in Claude Code) → in Codex or Antigravity, open the image with the harness image viewer/read_file tool, or verify dimensions and request visual confirmation from the Manager.
- Delivering media attachments to the user is handled by the Manager; worker terminals report the `$OUT` path.
