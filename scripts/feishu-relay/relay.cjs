#!/usr/bin/env node
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function loadConfig() {
  const configPath = path.join(__dirname, 'relay-config.json');
  if (fs.existsSync(configPath)) {
    try {
      return JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch (e) {
      process.stderr.write(`[WARN] Failed to parse config: ${e.message}\n`);
    }
  }
  return null;
}

const USER_CONFIG = loadConfig() || {};

const CONFIG = {
  appId: USER_CONFIG.appId || 'cli_a965b9099e269bc4',
  chatId: USER_CONFIG.chatId || 'oc_bbde428675a7c267d55c3f0663ca701d',
  botOpenId: USER_CONFIG.botOpenId || 'ou_78032b067c34b2bd7f058169d5d11b65',
  larkCliPath: USER_CONFIG.larkCliPath || 'C:\\Users\\123\\AppData\\Roaming\\npm\\lark-cli.cmd',
  inboxPath: path.join(__dirname, '.feishu-inbox.jsonl'),
  outboxPath: path.join(__dirname, '.feishu-outbox.jsonl'),
  logPath: path.join(__dirname, 'feishu-relay.log'),
  autoReply: USER_CONFIG.autoReply !== false,
  handlerCmd: USER_CONFIG.handlerCmd || null,
  replyOnMentionOnly: USER_CONFIG.replyOnMentionOnly !== false,
};

let subProcess = null;
let outboxWatcher = null;
let lastOutboxSize = 0;
let messageIdSet = new Set();

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}\n`;
  fs.appendFileSync(CONFIG.logPath, line);
  process.stderr.write(line);
}

function parseMessageContent(contentStr) {
  try {
    const parsed = JSON.parse(contentStr);
    if (parsed.text) return parsed.text;
    return contentStr;
  } catch {
    return contentStr;
  }
}

function stripBotMention(text, mentions) {
  let cleaned = text;
  if (mentions && Array.isArray(mentions)) {
    for (const m of mentions) {
      if (m.key) cleaned = cleaned.replace(m.key, '').trim();
    }
  }
  cleaned = cleaned.replace(/^@\S+\s*/, '').trim();
  return cleaned;
}

function extractTextFromEvent(event) {
  const msg = event?.event?.message;
  if (!msg) return null;
  const text = parseMessageContent(msg.content);
  const senderName = event?.event?.sender?.sender_id?.open_id || 'unknown';
  const chatType = msg.chat_type || 'unknown';
  const messageId = msg.message_id || '';
  const chatId = msg.chat_id || '';
  const createTime = msg.create_time || '';
  const mentions = msg.mentions || [];
  const isBotMentioned = mentions.some(
    m => m.mentioned_type === 'bot' || m.id?.open_id === CONFIG.botOpenId
  );
  const cleanText = stripBotMention(text, mentions);
  return { text, cleanText, senderName, chatType, messageId, chatId, createTime, isBotMentioned, raw: event };
}

function writeToInbox(entry) {
  const line = JSON.stringify(entry) + '\n';
  fs.appendFileSync(CONFIG.inboxPath, line);
}

function queueReply(text, chatId) {
  const entry = { action: 'reply', text, chatId: chatId || CONFIG.chatId, ts: Date.now() };
  const line = JSON.stringify(entry) + '\n';
  fs.appendFileSync(CONFIG.outboxPath, line);
}

async function sendReply(text, chatId) {
  return new Promise((resolve) => {
    const targetChatId = chatId || CONFIG.chatId;
    const safeText = text.replace(/"/g, '\\"').replace(/\$/g, '\\$');
    const cmd = `"${CONFIG.larkCliPath}" im +messages-send --as bot --chat-id "${targetChatId}" --text "${safeText}"`;
    const proc = spawn(cmd, [], { stdio: ['pipe', 'pipe', 'pipe'], shell: true });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

async function runHandler(cleanText, fullEvent) {
  if (!CONFIG.handlerCmd) return null;
  try {
    const input = JSON.stringify({ text: cleanText, event: fullEvent });
    const result = execSync(`${CONFIG.handlerCmd}`, {
      input,
      timeout: 30000,
      maxBuffer: 1024 * 1024,
      encoding: 'utf8',
      env: { ...process.env },
    }).trim();
    return result || null;
  } catch (e) {
    log(`Handler error: ${e.message}`);
    return null;
  }
}

async function handleMessage(extracted) {
  const { cleanText, text, isBotMentioned, chatType, chatId, messageId, raw } = extracted;

  if (CONFIG.replyOnMentionOnly && !isBotMentioned) {
    log(`Skipping non-bot-mention message in ${chatType}`);
    return;
  }

  log(`Processing message [${messageId}]: "${cleanText.slice(0, 100)}"`);

  let replyText = null;

  if (CONFIG.handlerCmd) {
    replyText = await runHandler(cleanText, raw);
  }

  if (!replyText) {
    replyText = `[Trae Agent] 收到你的消息："${cleanText.slice(0, 200)}"\n\n消息已记录到 inbox。当前使用的是基础模式（未配置 handler），如需智能回复请配置 relay-config.json 中的 handlerCmd 字段。`;
  }

  queueReply(replyText, chatId);
  log(`Queued reply for [${messageId}]`);
}

function watchOutbox() {
  if (!fs.existsSync(CONFIG.outboxPath)) {
    fs.writeFileSync(CONFIG.outboxPath, '');
    lastOutboxSize = 0;
  }
  try {
    lastOutboxSize = fs.statSync(CONFIG.outboxPath).size;
  } catch { lastOutboxSize = 0; }

  outboxWatcher = fs.watch(CONFIG.outboxPath, { persistent: false }, async (eventType) => {
    if (eventType !== 'change') return;
    try {
      const stat = fs.statSync(CONFIG.outboxPath);
      if (stat.size <= lastOutboxSize) return;
      const newContent = fs.readFileSync(CONFIG.outboxPath, 'utf8').slice(lastOutboxSize);
      lastOutboxSize = stat.size;
      const lines = newContent.split('\n').filter(l => l.trim());
      for (const line of lines) {
        try {
          const entry = JSON.parse(line);
          if (entry.action === 'reply' && entry.text) {
            log(`Sending reply to ${entry.chatId || CONFIG.chatId}: "${entry.text.slice(0, 80)}"`);
            const result = await sendReply(entry.text, entry.chatId);
            if (result.code === 0) {
              log(`Reply sent OK: ${JSON.parse(result.stdout)?.data?.message_id}`);
            } else {
              log(`Reply FAILED (code ${result.code}): ${result.stderr}`);
            }
          }
        } catch (e) {
          log(`Outbox parse error: ${e.message}`);
        }
      }
    } catch (e) {
      if (e.code !== 'ENOENT') log(`Outbox watch error: ${e.message}`);
    }
  });

  setTimeout(() => { watchOutbox(); }, 2000);
}

function startSubscription() {
  const args = [
    'event', '+subscribe',
    '--as', 'bot',
    '--event-types', 'im.message.receive_v1',
  ];

  log(`Starting subscription: lark-cli ${args.join(' ')}`);

  subProcess = spawn(CONFIG.larkCliPath, args, {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: true,
    env: { ...process.env },
  });

  let buffer = '';

  subProcess.stdout.on('data', (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line);
        const extracted = extractTextFromEvent(event);
        if (!extracted) continue;

        const { messageId, text, cleanText, senderName, chatType, isBotMentioned, raw } = extracted;

        if (messageIdSet.has(messageId)) continue;
        messageIdSet.add(messageId);

        if (messageIdSet.size > 1000) {
          const arr = Array.from(messageIdSet);
          messageIdSet = new Set(arr.slice(-500));
        }

        log(`[MSG] from=${senderName} type=${chatType} mention=${isBotMentioned} id=${messageId} text="${cleanText.slice(0, 100)}"`);

        const inboxEntry = {
          ts: Date.now(),
          messageId,
          senderName,
          chatType,
          chatId: raw.event.message.chat_id,
          text,
          cleanText,
          isBotMentioned,
          raw,
        };
        writeToInbox(inboxEntry);

        console.log(JSON.stringify(inboxEntry));

        if (CONFIG.autoReply) {
          setImmediate(() => handleMessage(extracted));
        }
      } catch (e) {
        log(`Event parse error: ${e.message}. Raw: ${line.slice(0, 200)}`);
      }
    }
  });

  subProcess.stderr.on('data', (chunk) => {
    const msg = chunk.toString().trim();
    if (msg) log(`[SUB-STDERR] ${msg}`);
  });

  subProcess.on('close', (code) => {
    log(`Subscription process exited with code ${code}. Restarting in 3s...`);
    setTimeout(startSubscription, 3000);
  });

  subProcess.on('error', (err) => {
    log(`Subscription error: ${err.message}. Restarting in 3s...`);
    setTimeout(startSubscription, 3000);
  });
}

function handleShutdown() {
  log('Shutting down...');
  if (subProcess) subProcess.kill('SIGTERM');
  if (outboxWatcher) outboxWatcher.close();
  setTimeout(() => process.exit(0), 2000);
}

process.on('SIGINT', handleShutdown);
process.on('SIGTERM', handleShutdown);

log('=== CrazyAgentsManage Feishu Relay v2 starting ===');
log(`App ID: ${CONFIG.appId}`);
log(`Target Chat: ${CONFIG.chatId}`);
log(`Auto Reply: ${CONFIG.autoReply}`);
log(`Handler Cmd: ${CONFIG.handlerCmd || '(none - using fallback mode)'}`);
log(`Reply on @mention only: ${CONFIG.replyOnMentionOnly}`);
log(`Inbox: ${CONFIG.inboxPath}`);
log(`Outbox: ${CONFIG.outboxPath}`);

watchOutbox();
startSubscription();
