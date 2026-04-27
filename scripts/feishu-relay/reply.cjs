#!/usr/bin/env node
const fs = require('fs');
const { spawn } = require('child_process');
const path = require('path');

const OUTBOX_PATH = path.join(__dirname, '.feishu-outbox.jsonl');

function sendReply(text, chatId) {
  const entry = {
    action: 'reply',
    text,
    chatId: chatId || null,
    ts: Date.now(),
  };
  const line = JSON.stringify(entry) + '\n';
  fs.appendFileSync(OUTBOX_PATH, line);
  console.log(`Reply queued: "${text.slice(0, 100)}" → ${chatId || 'default'}`);
}

const args = process.argv.slice(2);
if (args.length === 0) {
  console.log('Usage: node reply.cjs <text> [chat_id]');
  console.log('');
  console.log('Examples:');
  console.log('  node reply.cjs "你好，我是Trae Agent"');
  console.log('  node reply.cjs "回复内容" oc_bbde428675a7c267d55c3f0663ca701d');
  process.exit(1);
}

const text = args[0];
const chatId = args[1] || null;
sendReply(text, chatId);
