<!--
  Centered dialog with a dimmed backdrop. Closes on Esc, the X button or a
  backdrop click. Usage:
    <Modal v-if="open" title="Edit profile" @close="open = false">...<template #footer>...</template></Modal>
-->
<template>
  <Teleport to="body">
    <div class="modal" @mousedown.self="$emit('close')">
      <section
        ref="dialog"
        class="modal__dialog"
        :class="{ 'modal__dialog--wide': wide }"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
      >
        <header class="modal__head">
          <h2 :id="titleId" class="modal__title">{{ title }}</h2>
          <button type="button" class="modal__close" aria-label="Close" @click="$emit('close')">
            <Icon name="close" :size="18" />
          </button>
        </header>
        <div class="modal__body"><slot /></div>
        <footer v-if="$slots.footer" class="modal__foot"><slot name="footer" /></footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import Icon from './Icon.vue';

defineProps({
  title: { type: String, required: true },
  wide: { type: Boolean, default: false },
});
const emit = defineEmits(['close']);

const titleId = `modal-${Math.random().toString(36).slice(2, 8)}`;
const dialog = ref(null);
let previousFocus = null;

function onKey(e) {
  if (e.key === 'Escape') emit('close');
}

onMounted(() => {
  previousFocus = document.activeElement;
  document.addEventListener('keydown', onKey);
  document.body.style.overflow = 'hidden';
  dialog.value.focus();
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey);
  document.body.style.overflow = '';
  if (previousFocus && previousFocus.focus) previousFocus.focus();
});
</script>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(8, 19, 31, 0.55);
  animation: fade 0.15s ease-out;
}

.modal__dialog {
  display: flex;
  flex-direction: column;
  width: min(460px, 100%);
  max-height: calc(100vh - 32px);
  color: var(--text);
  background: var(--surface);
  border-radius: 18px;
  box-shadow: 0 24px 60px rgba(8, 19, 31, 0.35);
  outline: none;
  animation: rise 0.18s ease-out;
}

.modal__dialog--wide {
  width: min(680px, 100%);
}

.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 12px;
}

.modal__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal__close {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 10px;
  cursor: pointer;
}

.modal__close:hover {
  color: var(--text);
  background: var(--surface-muted);
}

.modal__body {
  padding: 4px 20px 8px;
  overflow-y: auto;
}

.modal__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px 18px;
  border-top: 1px solid var(--border);
}

@keyframes fade {
  from { opacity: 0; }
}

@keyframes rise {
  from { opacity: 0; transform: translateY(8px); }
}

@media (prefers-reduced-motion: reduce) {
  .modal,
  .modal__dialog {
    animation: none;
  }
}
</style>
