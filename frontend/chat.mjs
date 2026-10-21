// Live chat: one socket per browser tab, shared by every signed-in page.
//
// BaseLayout calls startChat() once; the socket then stays open while the
// user moves between pages (main.js keeps this module loaded). It keeps
// `chat.chats` (the user's communities with unread counts) up to date, and
// passes new messages to whoever listens with onChatEvent() (the chat room).
//
// Security: the socket uses the normal sign-in cookie, and the server only
// lets members read or send in a community (see backend/apps/chat).

import { computed, reactive } from 'vue';
import { ApiError, apiGet, apiPost, getCookie, parseErrors } from './api.mjs';

export const chat = reactive({
  // [{ id, name, image, category_label, members_count, unread_count, last_message }]
  chats: [],
  loaded: false,
  loadError: '',
  // True while the live socket is connected.
  online: false,
  // Why live chat gave up ('signed-out' | 'bad-origin'), or '' while it keeps trying.
  stopped: '',
  // Largest file that can be sent (the server checks it too).
  maxFileMb: 25,
});

export const totalUnread = computed(() => chat.chats.reduce((sum, c) => sum + c.unread_count, 0));

// Close codes from the server: don't retry after these.
const NOT_SIGNED_IN = 4401;
const BAD_ORIGIN = 4403;
const SEND_TIMEOUT_MS = 10000;
// Wait between reconnect tries: starts at 2 s, doubles, at most 60 s.
const RETRY_MIN_MS = 2000;
const RETRY_MAX_MS = 60000;

let config = null; // { chatsApi, socketPath, userId }
let socket = null;
let retryMs = RETRY_MIN_MS;
let retryTimer = null;
let stopped = false;
let everConnected = false;
// The community whose chat is on screen (its new messages aren't unread).
let openChatId = null;
const listeners = new Set();
// client_id -> { resolve, reject, timer } for messages waiting for the server.
const pending = new Map();

export function startChat({ chatsApi, socketPath, userId, maxFileMb }) {
  if (config) return; // already running
  config = { chatsApi, socketPath, userId };
  if (maxFileMb) chat.maxFileMb = maxFileMb;
  refreshChats();
  connect();
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'visible') return;
    if (openChatId !== null) markRead(openChatId);
    // Reconnecting waits while the tab is hidden; do it now.
    if (!socket && !stopped && !retryTimer) connect();
  });
}

export const messagesApi = (communityId) => `${config.chatsApi}${communityId}/messages/`;

export async function refreshChats() {
  try {
    chat.chats = await apiGet(config.chatsApi);
    chat.loadError = '';
  } catch (err) {
    chat.loadError = parseErrors(err).message;
  } finally {
    chat.loaded = true;
  }
}

// Listen to {type: 'message', message} and {type: 'reconnected'}. Returns a function that stops listening.
export function onChatEvent(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function emit(event) {
  listeners.forEach((fn) => fn(event));
}

// ---------- socket ----------

function connect() {
  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(`${scheme}//${window.location.host}${config.socketPath}`);

  socket.onopen = () => {
    chat.online = true;
    retryMs = RETRY_MIN_MS;
    if (everConnected) {
      // Messages may have arrived while we were offline.
      refreshChats();
      emit({ type: 'reconnected' });
    }
    everConnected = true;
  };

  socket.onmessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }
    if (data.type === 'message') onMessage(data.message, data.client_id);
    else if (data.type === 'read') onRead(data.community, data.last_id);
    else if (data.type === 'chats_changed') refreshChats();
    else if (data.type === 'error') settle(data.client_id, null, data.detail || 'Message not sent.');
  };

  socket.onclose = (event) => {
    chat.online = false;
    socket = null;
    if (event.code === NOT_SIGNED_IN || event.code === BAD_ORIGIN) {
      stopped = true; // retrying can't help
      chat.stopped = event.code === BAD_ORIGIN ? 'bad-origin' : 'signed-out';
      if (event.code === BAD_ORIGIN) console.warn('Live chat is off: this address is not in ALLOWED_HOSTS.');
      return;
    }
    scheduleReconnect();
  };
}

function scheduleReconnect() {
  const wait = retryMs;
  retryMs = Math.min(retryMs * 2, RETRY_MAX_MS);
  retryTimer = setTimeout(async () => {
    retryTimer = null;
    // Hidden tab: wait until it is looked at again (see visibilitychange).
    if (document.visibilityState !== 'visible') return;
    // Signed out (e.g. in another tab)? Then stop instead of retrying.
    try {
      await apiGet(config.chatsApi);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        stopped = true;
        chat.stopped = 'signed-out';
        return;
      }
    }
    connect();
  }, wait);
}

function socketOpen() {
  return socket && socket.readyState === WebSocket.OPEN;
}

function sortChats() {
  const lastId = (c) => (c.last_message ? c.last_message.id : 0);
  chat.chats.sort((a, b) => lastId(b) - lastId(a) || a.name.localeCompare(b.name));
}

function onMessage(message, clientId) {
  settle(clientId, message);
  const c = chat.chats.find((x) => x.id === message.community);
  if (!c) {
    refreshChats(); // a community we just joined
  } else if (!c.last_message || message.id > c.last_message.id) {
    c.last_message = message;
    const mine = message.author && message.author.id === config.userId;
    const watching = openChatId === message.community && document.visibilityState === 'visible';
    if (watching) markRead(message.community, message.id);
    else if (!mine) c.unread_count += 1;
    sortChats();
  }
  emit({ type: 'message', message });
}

function onRead(communityId, lastId) {
  const c = chat.chats.find((x) => x.id === communityId);
  if (c && (!c.last_message || lastId >= c.last_message.id)) c.unread_count = 0;
}

function settle(clientId, message, error) {
  const p = clientId && pending.get(clientId);
  if (!p) return;
  pending.delete(clientId);
  clearTimeout(p.timer);
  if (message) p.resolve(message);
  else p.reject(new Error(error));
}

// ---------- actions ----------

// The chat on screen (null when none). Its messages count as read.
export function setOpenChat(communityId) {
  openChatId = communityId;
  if (communityId !== null) markRead(communityId);
}

export function markRead(communityId, lastId) {
  const c = chat.chats.find((x) => x.id === communityId);
  if (c) c.unread_count = 0;
  const data = { community: communityId, last_id: lastId ?? c?.last_message?.id ?? null };
  if (socketOpen()) socket.send(JSON.stringify({ type: 'read', ...data }));
  else apiPost(`${config.chatsApi}${communityId}/read/`, { last_id: data.last_id }).catch(() => {});
}

// Send a message. Resolves with the saved message, or rejects with an Error
// whose text can be shown.
export function sendMessage(communityId, body) {
  if (!socketOpen()) {
    return apiPost(messagesApi(communityId), { body }).catch((err) => {
      const { message, fieldErrors } = parseErrors(err);
      throw new Error(fieldErrors.body || message);
    });
  }
  const clientId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => settle(clientId, null, 'Message not sent. Check your connection.'), SEND_TIMEOUT_MS);
    pending.set(clientId, { resolve, reject, timer });
    socket.send(JSON.stringify({ type: 'send', community: communityId, body, client_id: clientId }));
  });
}

// Send a photo, video or file, with an optional caption. `onProgress(0..1)`
// follows the upload. Resolves with the saved message; rejects with an Error
// whose text can be shown.
export function uploadMessage(communityId, file, body, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', messagesApi(communityId));
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    xhr.responseType = 'json';
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => {
      if (xhr.status === 201) return resolve(xhr.response);
      if (xhr.status === 413) return reject(new Error(`Files can be at most ${chat.maxFileMb} MB.`));
      const { message, fieldErrors } = parseErrors(new ApiError(xhr.status, xhr.response || {}));
      reject(new Error(fieldErrors.file || fieldErrors.body || message));
    };
    xhr.onerror = () => reject(new Error('Upload failed. Check your connection.'));
    const form = new FormData();
    form.append('file', file);
    if (body) form.append('body', body);
    xhr.send(form);
  });
}

// "820 KB", "4.2 MB".
export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(bytes < 10 * 1024 * 1024 ? 1 : 0)} MB`;
}

// One-line summary of a message for previews: its text, or what it sends.
export function messagePreview(message) {
  if (message.body) return message.body;
  const a = message.attachment;
  if (!a) return '';
  return { image: '📷 Photo', video: '🎥 Video' }[a.kind] || `📎 ${a.name}`;
}
