<!--
  One-line comment box that grows as you type. Enter sends, Shift+Enter
  adds a line, Esc cancels. `send(body)` is an async function from the
  parent; the box clears when it succeeds and shows its error if it fails.
  Usage: <CommentForm placeholder="Reply…" :send="reply" cancelable @cancel="..." />
-->
<template>
  <form class="cform" @submit.prevent="submit">
    <div class="cform__box">
      <textarea
        ref="input"
        v-model="body"
        rows="1"
        :maxlength="2000"
        :placeholder="placeholder"
        :aria-label="placeholder"
        @input="grow"
        @keydown.enter.exact.prevent="submit"
        @keydown.esc="$emit('cancel')"
      ></textarea>
      <button v-if="cancelable" type="button" class="cform__btn cform__btn--cancel" aria-label="Cancel" title="Cancel" @click="$emit('cancel')">
        <Icon name="close" :size="15" />
      </button>
      <button type="submit" class="cform__btn" :disabled="!body.trim() || sending" :aria-label="submitLabel" :title="submitLabel">
        <Icon name="send" :size="15" />
      </button>
    </div>
    <p v-if="error" class="cform__error" role="alert">{{ error }}</p>
  </form>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue';
import { parseErrors } from '../api.mjs';
import Icon from './Icon.vue';

const props = defineProps({
  send: { type: Function, required: true },
  placeholder: { type: String, default: 'Write a comment…' },
  submitLabel: { type: String, default: 'Post comment' },
  initial: { type: String, default: '' },
  autofocus: { type: Boolean, default: false },
  cancelable: { type: Boolean, default: false },
});
defineEmits(['cancel']);

const body = ref(props.initial);
const sending = ref(false);
const error = ref('');
const input = ref(null);

function grow() {
  const el = input.value;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight}px`;
}

onMounted(() => {
  if (props.initial) grow();
  if (props.autofocus) input.value.focus();
});

async function submit() {
  const text = body.value.trim();
  if (!text || sending.value) return;
  sending.value = true;
  error.value = '';
  try {
    await props.send(text);
    body.value = '';
    await nextTick();
    grow();
  } catch (err) {
    const { fieldErrors, message } = parseErrors(err);
    error.value = message || Object.values(fieldErrors)[0];
  } finally {
    sending.value = false;
  }
}
</script>

<style scoped>
.cform__box {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  padding: 4px 4px 4px 12px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 18px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.cform__box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--focus);
}

textarea {
  flex: 1;
  min-width: 0;
  max-height: 160px;
  padding: 5px 0;
  font: inherit;
  font-size: 14px;
  line-height: 1.45;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
  resize: none;
}

.cform__btn {
  display: grid;
  flex: none;
  place-items: center;
  width: 30px;
  height: 30px;
  color: #fff;
  background: var(--primary);
  border: 0;
  border-radius: 50%;
  cursor: pointer;
}

.cform__btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.cform__btn--cancel {
  color: var(--muted);
  background: none;
}

.cform__btn--cancel:hover {
  background: var(--border);
}

.cform__error {
  margin: 4px 0 0 12px;
  font-size: 13px;
  color: var(--danger);
}
</style>
