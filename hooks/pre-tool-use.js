#!/usr/bin/env node
/**
 * Antigravity PreToolUse Hook Handler
 * Protocol: Reads JSON from stdin, outputs JSON with decision ("allow", "deny", "ask", "force_ask") to stdout.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const BOARD_DENY = [
  [/\bgit(\s+(-[Cc]\s+\S+|--?\S+))*\s+push\b/, 'git push'],
  [/\bgit\b.*--amend\b/, 'git --amend'],
  [/core\.hooksPath\s*=/, 'core.hooksPath'],
  [/\bcompose\b.*\bdown\b/, 'docker compose down'],
  [/\brm\s+(-\w*r\w*f|-\w*f\w*r)\b/, 'rm -rf'],
  [/(^|[;&|(]\s*)sudo\b/, 'sudo'],
];

const PROD_GUARD = path.join(__dirname, 'prod-guard.py');

function prodGuard(cmd) {
  if (!fs.existsSync(PROD_GUARD)) return null;
  const res = spawnSync('python3', [PROD_GUARD], {
    input: JSON.stringify({ tool_input: { command: cmd } }),
    encoding: 'utf8',
    timeout: 10000,
  });
  return res.status === 2 ? (res.stderr || 'command against production blocked').trim() : null;
}

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
  });
}

async function main() {
  let input;
  try {
    const raw = await readStdin();
    input = raw ? JSON.parse(raw) : {};
  } catch (err) {
    console.log(JSON.stringify({ decision: 'allow' }));
    return;
  }

  const toolName = input.toolCall?.name || '';
  const args = input.toolCall?.args || {};

  // 1. Guardrail for run_command: block --no-verify, forbidden board verbs, and production writes
  if (toolName === 'run_command') {
    const cmd = String(args.CommandLine || '');
    if (/--no-verify/i.test(cmd)) {
      console.log(
        JSON.stringify({
          decision: 'deny',
          reason:
            'Blocked by Harness: --no-verify on git commands is forbidden to preserve hook integrity and quality checks.',
        })
      );
      return;
    }
    const forbidden = BOARD_DENY.find(([re]) => re.test(cmd));
    if (forbidden) {
      console.log(
        JSON.stringify({
          decision: 'deny',
          reason: `Blocked by Harness: ${forbidden[1]} is reserved for the human operator, not the agent.`,
        })
      );
      return;
    }
    const prodReason = prodGuard(cmd);
    if (prodReason) {
      console.log(JSON.stringify({ decision: 'deny', reason: `Blocked by prod-guard: ${prodReason}` }));
      return;
    }
  }

  // 2. Guardrail for write_to_file: warn on oversized source files (>800 lines)
  if (toolName === 'write_to_file') {
    const targetFile = String(args.TargetFile || '');
    const codeContent = String(args.CodeContent || '');
    const lines = codeContent.split('\n').length;

    if (
      lines > 800 &&
      !targetFile.includes('.gemini') &&
      !targetFile.includes('node_modules') &&
      !targetFile.includes('package-lock.json')
    ) {
      console.log(
        JSON.stringify({
          decision: 'ask',
          reason: `Harness warning: ${targetFile} has ${lines} lines (recommended maximum: 800 lines). Consider splitting into smaller modules.`,
        })
      );
      return;
    }
  }

  console.log(JSON.stringify({ decision: 'allow' }));
}

main().catch(() => {
  console.log(JSON.stringify({ decision: 'allow' }));
});
