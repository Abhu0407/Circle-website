<!--
  One community's chat: messages (older ones load when you scroll up) and a
  box to write in. New messages arrive live over the shared socket
  (chat.mjs); while this is on screen they count as read.
  Photos, videos and files can be attached with the clip button, dropped
  onto the chat, or pasted; each is sent as its own message (the text goes
  with the first one as its caption). The smiley button opens an emoji
  picker; a message of only 1-3 emoji is shown large.
  Usage: <ChatRoom :community-id="3" :user="user" @back="..." />
-->
<template>
  <div
    class="room"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div v-if="dragging && !notMember" class="dropzone">
      <Icon name="paperclip" :size="28" />
      <strong>Drop to send</strong>
      <span>Photos, videos or files · up to {{ chat.maxFileMb }} MB each</span>
    </div>

    <!-- ---------- Header ---------- -->
    <header class="room__head">
      <button type="button" class="iconbtn" aria-label="Back to chats" title="Back to chats" @click="$emit('back')">
        <Icon name="back" :size="18" />
      </button>
      <template v-if="info">
        <img :src="info.image" alt="" class="room__pic" />
        <div class="room__title">
          <a :href="info.url" class="room__name">{{ info.name }}</a>
          <span class="room__meta">
            {{ info.members_count }} {{ info.members_count === 1 ? 'member' : 'members' }}
            <span v-if="chat.stopped === 'signed-out'" class="room__offline">
              · You're signed out. <a :href="signinHref">Sign in again</a>
            </span>
            <span v-else-if="chat.stopped" class="room__offline">· Live updates are off. Reload the page.</span>
            <span v-else-if="!chat.online" class="room__offline">· Reconnecting…</span>
          </span>
        </div>
      </template>
      <div v-else class="room__title"><span class="room__name">Chat</span></div>
      <span class="room__lock" title="Only members of this community can see these messages">
        <Icon name="lock" :size="14" /> Members only
      </span>
    </header>

    <!-- ---------- Messages ---------- -->
    <div ref="scroller" class="room__scroll" @scroll="onScroll">
      <p v-if="loadingOlder" class="note">Loading earlier messages…</p>
      <p v-else-if="!hasMore && messages.length" class="note">This is the start of the chat.</p>

      <p v-if="loading" class="note">Loading messages…</p>
      <EmptyState v-else-if="notMember" icon="lock" text="Join this community to see and send messages.">
        <a v-if="info" :href="info.url">Open the community</a>
      </EmptyState>
      <p v-else-if="error" class="note note--error">{{ error }}</p>
      <EmptyState v-else-if="!messages.length" icon="chat" text="No messages yet. Say hello to the community!" />

      <template v-for="(m, i) in messages" :key="m.key">
        <div v-if="startsDay(i)" class="day"><span>{{ dayLabel(m.created_at) }}</span></div>
        <div
          class="msg"
          :class="{ 'msg--mine': isMine(m), 'msg--first': startsGroup(i), 'msg--pending': m.pending, 'msg--failed': m.failed }"
        >
          <span class="msg__avatar">
            <UserAvatar v-if="startsGroup(i) && !isMine(m)" :user="m.author" :size="32" />
          </span>
          <div class="msg__col">
            <span v-if="startsGroup(i) && !isMine(m)" class="msg__author">{{ authorName(m.author) }}</span>
            <div
              class="msg__bubble"
              :class="{ 'msg__bubble--media': isMedia(m), 'msg__bubble--emoji': !m.attachment && isBigEmoji(m.body) }"
            >
              <!-- Photo: opens large on click. Size is known up front so the chat doesn't jump. -->
              <button
                v-if="m.attachment && m.attachment.kind === 'image'"
                type="button"
                class="att-img"
                :style="mediaBox(m.attachment)"
                :aria-label="`Open photo ${m.attachment.name}`"
                @click="viewing = m"
              >
                <img :src="m.attachment.url" alt="" loading="lazy" @load="onMediaLoad" />
              </button>
              <video
                v-else-if="m.attachment && m.attachment.kind === 'video'"
                class="att-video"
                :src="m.attachment.url"
                controls
                playsinline
                preload="metadata"
                @loadedmetadata="onMediaLoad"
              ></video>
              <a
                v-else-if="m.attachment"
                class="att-file"
                :href="m.pending || m.failed ? undefined : `${m.attachment.url}?download=1`"
                :download="m.attachment.name"
              >
                <span class="att-file__icon"><Icon name="file" :size="20" /></span>
                <span class="att-file__info">
                  <strong>{{ m.attachment.name }}</strong>
                  <span>{{ formatSize(m.attachment.size) }}</span>
                </span>
                <Icon v-if="!m.pending && !m.failed" name="download" :size="18" class="att-file__dl" />
              </a>

              <span v-if="m.body" class="msg__text">{{ m.body }}</span>
              <span v-if="m.pending && m.file" class="progress" :aria-label="`Uploading ${percent(m)}%`">
                <span :style="{ width: `${percent(m)}%` }"></span>
              </span>
              <time class="msg__time" :datetime="m.created_at" :title="fullDate(m.created_at)">
                {{ m.pending ? (m.file ? `Uploading ${percent(m)}%` : 'Sending…') : clockTime(m.created_at) }}
              </time>
            </div>
            <span v-if="m.failed" class="msg__error">
              {{ m.error }}
              <button type="button" @click="retry(m)">Retry</button>
              <button type="button" @click="discard(m)">Delete</button>
            </span>
          </div>
        </div>
      </template>
    </div>

    <button v-if="newBelow" type="button" class="jump" @click="scrollToBottom(true)">
      {{ newBelow }} new {{ newBelow === 1 ? 'message' : 'messages' }} ↓
    </button>

    <!-- ---------- Composer ---------- -->
    <ul v-if="picked.length && !notMember" class="tray" aria-label="Files to send">
      <li v-for="(p, i) in picked" :key="p.key" class="tray__item">
        <img v-if="p.preview && p.kind === 'image'" :src="p.preview" alt="" class="tray__thumb" />
        <span v-else class="tray__thumb tray__thumb--icon"><Icon :name="p.kind === 'video' ? 'video' : 'file'" :size="20" /></span>
        <span class="tray__info">
          <strong>{{ p.file.name }}</strong>
          <span>{{ formatSize(p.file.size) }}</span>
        </span>
        <button type="button" class="tray__remove" :aria-label="`Remove ${p.file.name}`" @click="unpick(i)">
          <Icon name="close" :size="14" />
        </button>
      </li>
    </ul>
    <p v-if="pickError" class="pick-error" role="alert">{{ pickError }}</p>

    <form v-if="!notMember" class="composer" @submit.prevent="send">
      <input ref="fileInput" type="file" multiple hidden @change="onPick" />
      <EmojiPicker v-if="emojiOpen" @pick="insertEmoji" @close="emojiOpen = false" />
      <button
        type="button"
        class="attach"
        :class="{ 'attach--on': emojiOpen }"
        aria-label="Emoji"
        title="Emoji"
        :aria-expanded="emojiOpen"
        data-emoji-toggle
        @click="emojiOpen = !emojiOpen"
      >
        <Icon name="smile" :size="20" />
      </button>
      <button
        type="button"
        class="attach"
        aria-label="Attach photos, videos or files"
        title="Attach photos, videos or files"
        @click="fileInput.click()"
      >
        <Icon name="paperclip" :size="20" />
      </button>
      <textarea
        ref="input"
        v-model="draft"
        rows="1"
        :maxlength="MAX_LENGTH"
        :placeholder="picked.length ? 'Add a caption…' : 'Write a message…'"
        aria-label="Message"
        @keydown.enter.exact="onEnter"
        @input="autosize"
        @blur="saveCaret"
        @paste="onPaste"
      ></textarea>
      <button type="submit" class="send" :disabled="!draft.trim() && !picked.length" aria-label="Send" title="Send (Enter)">
        <Icon name="send" :size="18" />
      </button>
    </form>

    <!-- Photo, large -->
    <Modal v-if="viewing" :title="viewing.attachment.name" large @close="viewing = null">
      <div class="viewer"><img :src="viewing.attachment.url" :alt="viewing.attachment.name" /></div>
      <template #footer>
        <a :href="`${viewing.attachment.url}?download=1`" :download="viewing.attachment.name" class="viewer__dl">
          <Icon name="download" :size="16" /> Download
        </a>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { apiGet, ApiError, parseErrors } from '../api.mjs';
import { chat, formatSize, messagesApi, onChatEvent, sendMessage, setOpenChat, uploadMessage } from '../chat.mjs';
import { isBigEmoji } from '../emoji.mjs';
import { clockTime, dayLabel, fullDate } from '../time.mjs';
import EmojiPicker from './EmojiPicker.vue';
import EmptyState from './EmptyState.vue';
import Icon from './Icon.vue';
import Modal from './Modal.vue';
import UserAvatar from './UserAvatar.vue';

const props = defineProps({
  communityId: { type: Number, required: true },
  user: { type: Object, required: true },
});
defineEmits(['back']);

const MAX_LENGTH = 2000;
// Files that can be picked to send in one go.
const MAX_PICKED = 10;
// Largest size a photo is shown at in the chat (px).
const MEDIA_W = 280;
const MEDIA_H = 320;
// Same author within this many minutes = one group (name shown once).
const GROUP_MINUTES = 5;

const info = computed(() => chat.chats.find((c) => c.id === props.communityId));
const signinHref = `/signin/?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;

// [{ key, id, author, body, attachment, created_at,
//    pending?, failed?, error?, file?, progress?, preview? }], oldest first.
// Messages still being sent have id null; uploads keep their File and a
// local preview URL until the server has them.
const messages = ref([]);
const hasMore = ref(false);
const loading = ref(true);
const loadingOlder = ref(false);
const error = ref('');
const notMember = ref(false);
const draft = ref('');
const newBelow = ref(0);
const scroller = ref(null);
const input = ref(null);
const fileInput = ref(null);
// Files chosen but not sent yet: [{ key, file, kind, preview }]
const picked = ref([]);
const pickError = ref('');
const dragging = ref(false);
// The photo open in the large viewer.
const viewing = ref(null);
const emojiOpen = ref(false);

const withKey = (m) => ({ ...m, key: `m${m.id}` });
const isMine = (m) => m.author && m.author.id === props.user.id;
const authorName = (a) => (a ? a.name || a.username : 'Deleted user');
const lastSavedId = () => {
  for (let i = messages.value.length - 1; i >= 0; i--) if (messages.value[i].id) return messages.value[i].id;
  return null;
};

const isMedia = (m) => m.attachment && m.attachment.kind !== 'file';
const percent = (m) => Math.round((m.progress || 0) * 100);

// Photos get their final size before they load, so the chat doesn't jump.
function mediaBox(a) {
  if (!a.width || !a.height) return { width: '240px' };
  const scale = Math.min(1, MEDIA_W / a.width, MEDIA_H / a.height);
  return { width: `${Math.round(a.width * scale)}px`, aspectRatio: `${a.width} / ${a.height}` };
}

function startsDay(i) {
  if (i === 0) return true;
  return new Date(messages.value[i - 1].created_at).toDateString() !== new Date(messages.value[i].created_at).toDateString();
}

function startsGroup(i) {
  if (startsDay(i)) return true;
  const a = messages.value[i - 1];
  const b = messages.value[i];
  const sameAuthor = (a.author && a.author.id) === (b.author && b.author.id);
  return !sameAuthor || new Date(b.created_at) - new Date(a.created_at) > GROUP_MINUTES * 60000;
}

// ---------- loading ----------

function showError(err) {
  if (err instanceof ApiError && err.status === 403) notMember.value = true;
  else error.value = parseErrors(err).message;
}

async function loadLatest() {
  loading.value = true;
  try {
    const page = await apiGet(messagesApi(props.communityId));
    messages.value = page.messages.map(withKey);
    hasMore.value = page.has_more;
  } catch (err) {
    showError(err);
  } finally {
    loading.value = false;
  }
  await nextTick();
  scrollToBottom();
}

async function loadOlder() {
  const first = messages.value.find((m) => m.id);
  if (!first || !hasMore.value || loadingOlder.value) return;
  loadingOlder.value = true;
  const el = scroller.value;
  const fromBottom = el.scrollHeight - el.scrollTop;
  try {
    const page = await apiGet(messagesApi(props.communityId), { before: first.id });
    messages.value = [...page.messages.map(withKey), ...messages.value];
    hasMore.value = page.has_more;
  } catch (err) {
    showError(err);
  } finally {
    loadingOlder.value = false;
  }
  await nextTick();
  el.scrollTop = el.scrollHeight - fromBottom; // stay on the same message
}

// After the socket reconnects: fetch what we missed.
async function catchUp() {
  const after = lastSavedId();
  if (after === null) return loadLatest();
  try {
    let page;
    do {
      page = await apiGet(messagesApi(props.communityId), { after: lastSavedId() });
      page.messages.forEach(addMessage);
    } while (page.has_more);
  } catch (err) {
    showError(err);
  }
}

// ---------- live messages ----------

function nearBottom() {
  const el = scroller.value;
  return !el || el.scrollHeight - el.scrollTop - el.clientHeight < 120;
}

function scrollToBottom(smooth = false) {
  const el = scroller.value;
  if (el) el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
  newBelow.value = 0;
}

async function addMessage(message) {
  if (messages.value.some((m) => m.id === message.id)) return;
  const stick = nearBottom() || isMine(message);
  // Keep pending messages (still sending) at the end.
  const firstPending = messages.value.findIndex((m) => m.pending || m.failed);
  const at = firstPending === -1 ? messages.value.length : firstPending;
  messages.value.splice(at, 0, withKey(message));
  await nextTick();
  if (stick) scrollToBottom(true);
  else if (!isMine(message)) newBelow.value += 1;
}

// A video (or a photo without a known size) took up room: keep the latest in view.
function onMediaLoad() {
  const el = scroller.value;
  if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 400) scrollToBottom();
}

function onScroll() {
  const el = scroller.value;
  if (el.scrollTop < 80) loadOlder();
  if (nearBottom()) newBelow.value = 0;
}

// ---------- sending ----------

function autosize() {
  const el = input.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  el.style.overflowY = el.scrollHeight > 160 ? 'auto' : 'hidden';
}

function onEnter(event) {
  if (event.isComposing) return; // typing with an IME
  event.preventDefault();
  send();
}

// ---------- emoji ----------

// Where the cursor was in the message box, so an emoji goes there.
let caret = null;
function saveCaret() {
  const el = input.value;
  if (el) caret = [el.selectionStart, el.selectionEnd];
}

async function insertEmoji(char) {
  const text = draft.value;
  if (text.length + char.length > MAX_LENGTH) return;
  const el = input.value;
  const focused = el && document.activeElement === el;
  const [start, end] = focused ? [el.selectionStart, el.selectionEnd] : caret || [text.length, text.length];
  draft.value = text.slice(0, start) + char + text.slice(end);
  const at = start + char.length;
  caret = [at, at];
  await nextTick();
  autosize();
  // Phones: leave the keyboard down while picking several.
  if (el && window.matchMedia('(hover: hover)').matches) {
    el.focus();
    el.setSelectionRange(at, at);
  }
}

// ---------- picking files ----------

const kindOf = (file) => (file.type.startsWith('image/') ? 'image' : file.type.startsWith('video/') ? 'video' : 'file');

function addFiles(files) {
  pickError.value = '';
  for (const file of files) {
    if (picked.value.length >= MAX_PICKED) {
      pickError.value = `You can send up to ${MAX_PICKED} files at a time.`;
      break;
    }
    if (!file.size) {
      pickError.value = `${file.name} is empty.`;
      continue;
    }
    if (file.size > chat.maxFileMb * 1024 * 1024) {
      pickError.value = `${file.name} is bigger than ${chat.maxFileMb} MB.`;
      continue;
    }
    const kind = kindOf(file);
    const preview = kind === 'file' ? null : URL.createObjectURL(file);
    picked.value.push({ key: `f${Date.now()}${Math.random()}`, file, kind, preview });
  }
  input.value?.focus();
}

function unpick(i) {
  const [p] = picked.value.splice(i, 1);
  if (p.preview) URL.revokeObjectURL(p.preview);
}

function onPick(event) {
  addFiles(event.target.files);
  event.target.value = ''; // so the same file can be picked again
}

function onPaste(event) {
  const files = [...((event.clipboardData && event.clipboardData.files) || [])];
  if (!files.length) return; // plain text: paste as usual
  event.preventDefault();
  addFiles(files);
}

// Dragging over child elements fires enter/leave many times: count them.
let dragDepth = 0;
function onDragEnter(event) {
  if (!event.dataTransfer || ![...event.dataTransfer.types].includes('Files')) return;
  dragDepth += 1;
  dragging.value = true;
}
function onDragLeave() {
  dragDepth = Math.max(0, dragDepth - 1);
  if (!dragDepth) dragging.value = false;
}
function onDrop(event) {
  dragDepth = 0;
  dragging.value = false;
  if (!notMember.value && event.dataTransfer) addFiles(event.dataTransfer.files);
}

// ---------- sending ----------

// Messages go out one after another, so they arrive in the order sent.
let queue = Promise.resolve();
const enqueue = (item) => {
  queue = queue.then(() => deliver(item));
};

async function deliver(item) {
  item.pending = true;
  item.failed = false;
  item.progress = 0;
  try {
    const saved = item.file
      ? await uploadMessage(props.communityId, item.file, item.body, (f) => { item.progress = f; })
      : await sendMessage(props.communityId, item.body);
    const i = messages.value.indexOf(item);
    if (i !== -1) messages.value.splice(i, 1);
    if (item.preview) URL.revokeObjectURL(item.preview);
    addMessage(saved);
  } catch (err) {
    item.pending = false;
    item.failed = true;
    item.error = err.message || 'Message not sent.';
  }
}

function pendingItem(body, p) {
  return {
    key: `p${Date.now()}${Math.random()}`,
    id: null,
    author: props.user,
    body,
    attachment: p ? { kind: p.kind, name: p.file.name, size: p.file.size, url: p.preview } : null,
    created_at: new Date().toISOString(),
    pending: true,
    file: p ? p.file : null,
    preview: p ? p.preview : null,
    progress: 0,
  };
}

async function send() {
  const body = draft.value.trim();
  const files = picked.value;
  if (!body && !files.length) return;
  draft.value = '';
  caret = null;
  emojiOpen.value = false;
  picked.value = [];
  pickError.value = '';
  await nextTick();
  autosize();
  // One message per file; the text is the first one's caption.
  const items = files.length ? files.map((p, i) => pendingItem(i === 0 ? body : '', p)) : [pendingItem(body)];
  messages.value.push(...items);
  const added = messages.value.slice(-items.length); // the reactive copies
  await nextTick();
  scrollToBottom(true);
  added.forEach(enqueue);
}

const retry = (item) => enqueue(item);
const discard = (item) => {
  if (item.preview) URL.revokeObjectURL(item.preview);
  messages.value = messages.value.filter((m) => m !== item);
};

// ---------- setup ----------

let stopListening = null;

onMounted(() => {
  setOpenChat(props.communityId);
  stopListening = onChatEvent((event) => {
    if (event.type === 'message' && event.message.community === props.communityId) addMessage(event.message);
    else if (event.type === 'reconnected' && !loading.value) catchUp();
  });
  loadLatest();
  input.value?.focus();
});

onBeforeUnmount(() => {
  picked.value.forEach((p) => p.preview && URL.revokeObjectURL(p.preview));
  setOpenChat(null);
  if (stopListening) stopListening();
});
</script>

<style scoped>
.room {
  position: relative;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 420px;
}

button {
  font: inherit;
  cursor: pointer;
}

/* ---------- header ---------- */
.room__head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 4px 12px;
  border-bottom: 1px solid var(--border);
}

.iconbtn {
  display: grid;
  flex: none;
  place-items: center;
  width: 36px;
  height: 36px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 0;
  border-radius: 10px;
}

.iconbtn:hover {
  color: var(--primary);
  background: var(--primary-soft);
}

.room__pic {
  flex: none;
  width: 42px;
  height: 42px;
  object-fit: cover;
  border-radius: 50%;
}

.room__title {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.room__name {
  overflow: hidden;
  font-weight: 600;
  color: var(--text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room__meta {
  font-size: 13px;
  color: var(--muted);
}

.room__offline {
  color: var(--amber);
}

.room__lock {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--green-dark);
  background: var(--green-soft);
  border-radius: 999px;
}

/* ---------- messages ---------- */
.room__scroll {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  padding: 12px 4px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.note {
  margin: 4px 0 8px;
  font-size: 13px;
  text-align: center;
  color: var(--muted);
}

.note--error {
  color: var(--danger);
}

.day {
  display: flex;
  justify-content: center;
  margin: 12px 0 6px;
}

.day span {
  padding: 2px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: var(--surface-muted);
  border-radius: 999px;
}

.msg {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  max-width: 100%;
}

.msg--first {
  margin-top: 8px;
}

.msg__avatar {
  flex: none;
  width: 32px;
  align-self: flex-start;
}

.msg__col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  max-width: min(75%, 560px);
}

.msg__author {
  margin: 0 0 2px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.msg__bubble {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 2px 10px;
  max-width: 100%;
  padding: 7px 12px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
}

.msg__text {
  min-width: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.msg__time {
  margin-left: auto;
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}

.msg--mine {
  flex-direction: row-reverse;
}

.msg--mine .msg__avatar {
  display: none;
}

.msg--mine .msg__col {
  align-items: flex-end;
}

.msg--mine .msg__bubble {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
  border-radius: 16px 4px 16px 16px;
}

.msg--mine .msg__time {
  color: rgba(255, 255, 255, 0.75);
}

.msg__bubble--emoji {
  padding: 0 4px;
  background: none;
  border-color: transparent;
}

.msg__bubble--emoji .msg__text {
  font-size: 40px;
  line-height: 1.2;
}

.msg--mine .msg__bubble--emoji {
  color: inherit;
  background: none;
  border-color: transparent;
}

.msg--mine .msg__bubble--emoji .msg__time {
  color: var(--muted);
}

.msg__bubble--media {
  flex-direction: column;
  align-items: stretch;
  padding: 4px;
}

.msg__bubble--media .msg__text {
  padding: 2px 8px 0;
}

.msg__bubble--media .msg__time {
  padding: 0 8px 2px;
}

.att-img {
  display: block;
  max-width: 100%;
  padding: 0;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.06);
  border: 0;
  border-radius: 12px;
  cursor: zoom-in;
}

.att-img img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.att-video {
  display: block;
  width: 320px;
  max-width: 100%;
  max-height: 360px;
  background: #000;
  border-radius: 12px;
}

.att-file {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  max-width: 320px;
  padding: 6px 4px 4px 0;
  font-weight: 400;
  color: inherit;
}

.att-file:hover {
  text-decoration: none;
}

.att-file__icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 40px;
  height: 40px;
  color: var(--primary);
  background: var(--primary-soft);
  border-radius: 10px;
}

.msg--mine .att-file__icon {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}

.att-file__info {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.att-file__info strong {
  overflow: hidden;
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.att-file__info span {
  font-size: 12px;
  opacity: 0.75;
}

.att-file__dl {
  flex: none;
  opacity: 0.7;
}

.att-file:hover .att-file__dl {
  opacity: 1;
}

.progress {
  display: block;
  flex-basis: 100%;
  height: 4px;
  margin: 4px 0 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.35);
  border-radius: 999px;
}

.progress span {
  display: block;
  height: 100%;
  background: #fff;
  transition: width 0.2s;
}

.msg--pending .msg__bubble {
  opacity: 0.75;
}

.msg--failed .msg__bubble {
  background: var(--danger);
  border-color: var(--danger);
}

.msg__error {
  margin-top: 2px;
  font-size: 12px;
  color: var(--danger);
}

.msg__error button {
  margin-left: 6px;
  padding: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  background: none;
  border: 0;
}

.jump {
  position: absolute;
  bottom: 76px;
  left: 50%;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: var(--primary);
  border: 0;
  border-radius: 999px;
  box-shadow: var(--shadow);
  transform: translateX(-50%);
}

/* ---------- files to send ---------- */
.tray {
  display: flex;
  gap: 8px;
  margin: 0;
  padding: 10px 0 0;
  overflow-x: auto;
  list-style: none;
  border-top: 1px solid var(--border);
}

.tray + .pick-error,
.tray ~ .composer {
  border-top: 0;
}

.tray__item {
  position: relative;
  display: flex;
  flex: none;
  align-items: center;
  gap: 8px;
  width: 200px;
  padding: 6px 30px 6px 6px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.tray__thumb {
  flex: none;
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 8px;
}

.tray__thumb--icon {
  display: grid;
  place-items: center;
  color: var(--primary);
  background: var(--primary-soft);
}

.tray__info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.tray__info strong {
  overflow: hidden;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tray__info span {
  font-size: 12px;
  color: var(--muted);
}

.tray__remove {
  position: absolute;
  top: 6px;
  right: 6px;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  padding: 0;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 50%;
}

.tray__remove:hover {
  color: var(--danger);
}

.pick-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--danger);
}

/* ---------- drop target ---------- */
.dropzone {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--primary);
  background: rgba(232, 240, 253, 0.92);
  border: 2px dashed var(--primary);
  border-radius: 16px;
  pointer-events: none;
}

.dropzone span {
  font-size: 13px;
  color: var(--muted);
}

/* ---------- photo viewer ---------- */
.viewer {
  display: grid;
  place-items: center;
  height: 100%;
}

.viewer img {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: 8px;
}

.viewer__dl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* ---------- composer ---------- */
.composer {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.composer textarea {
  flex: 1;
  min-width: 0;
  max-height: 160px;
  padding: 10px 14px;
  font: inherit;
  line-height: 1.4;
  color: var(--text);
  resize: none;
  overflow-y: hidden;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 20px;
  outline: none;
}

.composer textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.attach {
  display: grid;
  flex: none;
  place-items: center;
  width: 42px;
  height: 42px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 0;
  border-radius: 50%;
}

.attach--on,
.attach:hover {
  color: var(--primary);
  background: var(--primary-soft);
}

.send {
  display: grid;
  flex: none;
  place-items: center;
  width: 42px;
  height: 42px;
  color: #fff;
  background: var(--primary);
  border: 0;
  border-radius: 50%;
}

.send:hover:not(:disabled) {
  background: var(--primary-hover);
}

.send:disabled {
  opacity: 0.45;
  cursor: default;
}

@media (max-width: 760px) {
  .room {
    height: calc(100vh - 140px);
  }
  .room__lock {
    display: none;
  }
  .composer {
    gap: 4px;
  }
  .attach {
    width: 36px;
    height: 36px;
    margin-bottom: 3px;
  }
}
</style>
