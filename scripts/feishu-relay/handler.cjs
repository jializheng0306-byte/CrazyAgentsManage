#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const PENDING_PATH = path.join(__dirname, '.feishu-pending.jsonl');

function loadConfig() {
  const configPath = path.join(__dirname, 'handler-config.json');
  try {
    if (fs.existsSync(configPath)) {
      return JSON.parse(fs.readFileSync(configPath, 'utf8'));
    }
  } catch (e) {}
  return {};
}

async function main() {
  const input = await readStdin();
  if (!input.trim()) {
    process.stderr.write('[handler] No input\n');
    process.exit(1);
  }

  let parsed;
  try {
    parsed = JSON.parse(input);
  } catch (e) {
    parsed = { text: input };
  }

  const config = loadConfig();
  const userText = parsed.text || '';
  const chatId = parsed.event?.event?.message?.chat_id || '';
  const messageId = parsed.event?.event?.message?.message_id || '';
  const senderName = parsed.event?.event?.sender?.sender_id?.open_id || 'unknown';

  if (!userText.trim()) {
    process.stderr.write('[handler] Empty message text\n');
    process.exit(1);
  }

  const pendingEntry = {
    id: `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    ts: Date.now(),
    messageId,
    senderName,
    chatId,
    text: userText,
    raw: parsed.event || null,
    status: 'pending',
  };

  const line = JSON.stringify(pendingEntry) + '\n';
  fs.appendFileSync(PENDING_PATH, line);

  process.stderr.write(`[handler] Queued message ${pendingEntry.id}: "${userText.slice(0, 80)}"\n`);

  const ackMessage = config.ackMessage || '收到你的消息了，Trae Agent 正在处理中...';
  process.stdout.write(ackMessage);
}

function readStdin() {
  return new Promise((resolve) => {
    const chunks = [];
    if (process.stdin.isTTY) {
      resolve('');
      return;
    }
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => chunks.push(chunk));
    process.stdin.on('end', () => resolve(chunks.join('')));
  });
}

main().catch(err => {
  process.stderr.write(`[handler] Fatal: ${err.message}\n`);
  process.exit(1);
});
