<!--
  A "Filters" button that opens a panel with the page's filter options
  (default slot). A dot on the button shows that filters are on.
  Choices apply straight away; "Clear all" emits `clear`, "Done" closes.
  Closes on Esc or a click outside.
  Usage:
    <FilterMenu :count="activeCount" @clear="clearFilters">
      <FilterGroup label="Category">...FilterChips...</FilterGroup>
    </FilterMenu>
-->
<template>
  <div ref="root" class="fmenu">
    <button
      type="button"
      class="fmenu__btn"
      :class="{ 'fmenu__btn--open': open, 'fmenu__btn--active': count }"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :aria-label="count ? `${label} (${count} on)` : label"
      @click="open = !open"
    >
      <Icon name="filter" :size="16" />
      <span class="fmenu__text">{{ label }}</span>
      <span v-if="count" class="fmenu__dot" aria-hidden="true"></span>
    </button>

    <div v-if="open" class="fmenu__panel" role="dialog" :aria-label="label">
      <div class="fmenu__body"><slot /></div>
      <footer class="fmenu__foot">
        <button type="button" class="fmenu__clear" :disabled="!count" @click="$emit('clear')">Clear all</button>
        <ActionButton icon="check" label="Done" size="sm" @click="open = false" />
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue';
import ActionButton from './ActionButton.vue';
import Icon from './Icon.vue';

defineProps({
  // How many filters are on (0 = none; shows the dot otherwise).
  count: { type: Number, default: 0 },
  label: { type: String, default: 'Filters' },
});
defineEmits(['clear']);

const open = ref(false);
const root = ref(null);

function onDocDown(event) {
  if (root.value && !root.value.contains(event.target)) open.value = false;
}

function onKey(event) {
  if (event.key === 'Escape') open.value = false;
}

watch(open, (isOpen) => {
  const method = isOpen ? 'addEventListener' : 'removeEventListener';
  document[method]('mousedown', onDocDown);
  document[method]('keydown', onKey);
});

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocDown);
  document.removeEventListener('keydown', onKey);
});
</script>

<style scoped>
.fmenu {
  position: relative;
  flex: none;
}

.fmenu__btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  padding: 0 16px;
  font: inherit;
  font-weight: 600;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.fmenu__btn:hover,
.fmenu__btn--open {
  border-color: #c9dafa;
  background: var(--primary-soft);
}

.fmenu__btn--active {
  color: var(--primary);
  border-color: var(--primary);
}

.fmenu__btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--focus);
}

/* The "filters are on" dot, on the button's top-right corner. */
.fmenu__dot {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 12px;
  height: 12px;
  background: var(--primary);
  border: 2px solid var(--surface);
  border-radius: 50%;
}

.fmenu__panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 600;
  display: flex;
  flex-direction: column;
  width: min(420px, calc(100vw - 32px));
  max-height: min(70vh, 560px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(8, 19, 31, 0.25);
  animation: drop 0.15s ease-out;
}

.fmenu__body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px;
  overflow-y: auto;
}

.fmenu__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 18px;
  border-top: 1px solid var(--border);
}

.fmenu__clear {
  padding: 0;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  background: none;
  border: 0;
  cursor: pointer;
}

.fmenu__clear:disabled {
  color: var(--muted);
  cursor: default;
  opacity: 0.6;
}

@keyframes drop {
  from { opacity: 0; transform: translateY(-4px); }
}

@media (max-width: 560px) {
  .fmenu__text {
    display: none;
  }
  .fmenu__btn {
    padding: 0 13px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fmenu__panel {
    animation: none;
  }
}
</style>
