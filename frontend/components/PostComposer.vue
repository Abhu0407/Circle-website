<!--
  "Share something…" bar that opens the Create post popup: pick the
  community, write, add a photo, then Post publishes it to that community.
  Emits `created` with the new post.
  Usage: <PostComposer :communities="user.join_community" :posts-api="postsApi" :user="user" @created="..." />
-->
<template>
  <div class="starter">
    <UserAvatar :user="user" :size="40" />
    <button type="button" class="starter__prompt" @click="openPopup()">
      {{ posted || `Share something with ${selectedName}…` }}
    </button>
    <button type="button" class="starter__btn" title="Add a photo" @click="openPopup(true)">
      <Icon name="image" :size="18" /> <span>Photo</span>
    </button>
    <ActionButton icon="plus" label="Post" size="sm" class="starter__post" @click="openPopup()" />
  </div>

  <Modal v-if="open" title="Create post" wide @close="close">
    <form id="post-form" class="pform" @submit.prevent="submit">
      <!-- Where it goes: the community is the post's title, you are tagged. -->
      <div class="pform__who">
        <UserAvatar :user="user" :size="44" />
        <div class="pform__who-text">
          <strong>@{{ user.username }}</strong>
          <label class="pform__community">
            <span>Posting in</span>
            <select v-model="communityId" aria-label="Community to post in" :disabled="communities.length === 1">
              <option v-for="c in communities" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>
        </div>
      </div>

      <div class="pform__text">
        <textarea
          ref="input"
          v-model="body"
          rows="6"
          :maxlength="MAX_LENGTH"
          :placeholder="`What do you want to share with ${selectedName}?`"
          aria-label="Post text"
          @keydown.ctrl.enter.prevent="submit"
          @keydown.meta.enter.prevent="submit"
        ></textarea>
        <span class="pform__count" :class="{ 'pform__count--near': body.length > MAX_LENGTH - 200 }">
          {{ body.length }} / {{ MAX_LENGTH }}
        </span>
      </div>

      <div v-if="preview" class="pform__preview">
        <img :src="preview" alt="Photo to post" />
        <div class="pform__preview-actions">
          <button type="button" @click="fileInput.click()"><Icon name="camera" :size="14" /> Change</button>
          <button type="button" @click="clearImage"><Icon name="trash" :size="14" /> Remove</button>
        </div>
      </div>
      <label
        v-else
        class="pform__drop"
        :class="{ 'pform__drop--over': dragging }"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="onDrop"
      >
        <Icon name="image" :size="26" />
        <strong>Add a photo</strong>
        <span>Click or drag one here · up to 5 MB</span>
        <input ref="fileInput" type="file" accept="image/*" @change="pickImage($event.target.files[0])" />
      </label>
      <!-- Kept mounted while a photo is shown, for "Change". -->
      <input v-if="preview" ref="fileInput" type="file" accept="image/*" class="pform__hidden" @change="pickImage($event.target.files[0])" />

      <p v-if="error" class="pform__error" role="alert">{{ error }}</p>
    </form>

    <template #footer>
      <span class="pform__hint">Visible to everyone who opens {{ selectedName }}</span>
      <ActionButton icon="close" label="Cancel" variant="secondary" @click="close" />
      <ActionButton
        type="submit"
        form="post-form"
        icon="send"
        :label="sending ? 'Posting…' : 'Post'"
        :disabled="sending || (!body.trim() && !image)"
      />
    </template>
  </Modal>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { apiPost, parseErrors } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import Icon from './Icon.vue';
import Modal from './Modal.vue';
import UserAvatar from './UserAvatar.vue';

const MAX_LENGTH = 5000;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;

const props = defineProps({
  // [{ id, name }] — the communities the user can post in.
  communities: { type: Array, required: true },
  postsApi: { type: String, required: true },
  user: { type: Object, required: true },
  // Community picked first (e.g. the one the feed is filtered to).
  defaultCommunity: { type: Number, default: null },
});
const emit = defineEmits(['created']);

const open = ref(false);
const body = ref('');
const image = ref(null);
const preview = ref('');
const communityId = ref(props.defaultCommunity || (props.communities[0] || {}).id);
const sending = ref(false);
const error = ref('');
const dragging = ref(false);
// "Posted to Hikers" on the bar for a moment after posting.
const posted = ref('');
const input = ref(null);
const fileInput = ref(null);

watch(() => props.defaultCommunity, (id) => {
  if (id) communityId.value = id;
});

const selectedName = computed(() => (props.communities.find((c) => c.id === communityId.value) || {}).name || 'your community');

async function openPopup(withPhoto = false) {
  open.value = true;
  error.value = '';
  await nextTick();
  if (withPhoto && fileInput.value) fileInput.value.click();
  else input.value.focus();
}

function close() {
  if (sending.value) return;
  if ((body.value.trim() || image.value) && !window.confirm('Discard this post?')) return;
  reset();
}

function reset() {
  open.value = false;
  body.value = '';
  error.value = '';
  clearImage();
}

function pickImage(file) {
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    error.value = 'That file is not a photo.';
    return;
  }
  if (file.size > MAX_IMAGE_SIZE) {
    error.value = 'Photo must be 5 MB or smaller.';
    return;
  }
  clearImage();
  error.value = '';
  image.value = file;
  preview.value = URL.createObjectURL(file);
}

function onDrop(event) {
  dragging.value = false;
  pickImage(event.dataTransfer.files[0]);
}

function clearImage() {
  if (preview.value) URL.revokeObjectURL(preview.value);
  image.value = null;
  preview.value = '';
}

onBeforeUnmount(clearImage);

let postedTimer;
async function submit() {
  if (sending.value || (!body.value.trim() && !image.value)) return;
  sending.value = true;
  error.value = '';
  const form = new FormData();
  form.append('community_id', communityId.value);
  form.append('body', body.value);
  if (image.value) form.append('image', image.value);
  try {
    const post = await apiPost(props.postsApi, form);
    sending.value = false;
    reset();
    emit('created', post);
    posted.value = `Posted to ${post.community.name} ✓`;
    clearTimeout(postedTimer);
    postedTimer = setTimeout(() => (posted.value = ''), 3000);
  } catch (err) {
    const { fieldErrors, message } = parseErrors(err);
    error.value = message || Object.values(fieldErrors)[0];
    sending.value = false;
  }
}
</script>

<style scoped>
button {
  font: inherit;
  cursor: pointer;
}

/* ---------- the bar in the feed ---------- */
.starter {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.starter__prompt {
  flex: 1;
  min-width: 0;
  height: 42px;
  padding: 0 16px;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 999px;
  transition: border-color 0.15s, background 0.15s;
}

.starter__prompt:hover {
  background: var(--primary-soft);
  border-color: rgba(31, 111, 229, 0.35);
}

.starter__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 9px;
}

.starter__btn:hover {
  color: var(--primary);
  background: var(--primary-soft);
}

/* ---------- the popup ---------- */
.pform {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 6px;
}

.pform__who {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pform__who-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.pform__who-text strong {
  font-weight: 600;
}

.pform__community {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}

.pform__community select {
  max-width: 240px;
  height: 30px;
  padding: 0 8px;
  font: inherit;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-soft);
  border: 0;
  border-radius: 8px;
}

.pform__community select:disabled {
  opacity: 1;
  appearance: none;
}

.pform__text {
  position: relative;
}

.pform__text textarea {
  display: block;
  width: 100%;
  min-height: 150px;
  max-height: 45vh;
  padding: 12px 14px 28px;
  font: inherit;
  font-size: 16px;
  line-height: 1.55;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  resize: vertical;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.pform__text textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.pform__count {
  position: absolute;
  right: 12px;
  bottom: 8px;
  font-size: 12px;
  color: var(--muted);
  pointer-events: none;
}

.pform__count--near {
  color: var(--danger);
}

.pform__drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 20px;
  font-size: 13px;
  text-align: center;
  color: var(--muted);
  background: var(--surface-muted);
  border: 2px dashed var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.pform__drop strong {
  font-size: 14px;
  color: var(--text);
}

.pform__drop:hover,
.pform__drop:focus-within,
.pform__drop--over {
  color: var(--primary);
  background: var(--primary-soft);
  border-color: var(--primary);
}

.pform__drop input,
.pform__hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.pform__preview {
  position: relative;
}

.pform__preview img {
  display: block;
  width: 100%;
  max-height: 320px;
  object-fit: contain;
  background: var(--surface-muted);
  border-radius: 12px;
}

.pform__preview-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
}

.pform__preview-actions button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 11px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: rgba(8, 19, 31, 0.65);
  border: 0;
  border-radius: 999px;
}

.pform__error {
  margin: 0;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

.pform__hint {
  margin-right: auto;
  font-size: 13px;
  color: var(--muted);
}

@media (max-width: 560px) {
  .starter__btn span,
  .pform__hint {
    display: none;
  }
  .starter__post {
    display: none;
  }
}
</style>
