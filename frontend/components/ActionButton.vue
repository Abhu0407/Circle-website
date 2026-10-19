<!--
  The app's button: blue, icon + label.
  Usage:
    <ActionButton icon="pin" label="Set location" @click="..." />
    <ActionButton icon="close" label="Cancel" variant="secondary" @click="..." />
    <ActionButton icon="edit" label="Edit" compact @click="..." />
  `compact` (for buttons in a box's header, on the right) shows only the icon
  and slides the label out on hover or keyboard focus; on touch screens (no
  hover) the label is always shown. `expanded` keeps a compact label open.
  Other attributes (type, disabled, form, aria-*) go to the <button>.
-->
<template>
  <button
    :type="type"
    class="abtn"
    :class="[`abtn--${size}`, `abtn--${variant}`, { 'abtn--compact': compact, 'abtn--open': expanded }]"
    :aria-label="label"
  >
    <Icon :name="icon" :size="iconSize" />
    <span class="abtn__label" aria-hidden="true">
      <span class="abtn__text">{{ label }}</span>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue';
import Icon from './Icon.vue';

const props = defineProps({
  icon: { type: String, required: true },
  label: { type: String, required: true },
  // primary (blue) | secondary (white, for Cancel)
  variant: { type: String, default: 'primary' },
  // md (44px) | sm (36px)
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  compact: { type: Boolean, default: false },
  expanded: { type: Boolean, default: false },
});

const iconSize = computed(() => (props.size === 'sm' ? 16 : 18));
</script>

<style scoped>
.abtn {
  --h: 44px;
  --icon: 18px;
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  height: var(--h);
  min-width: var(--h);
  padding: 0 18px;
  font: inherit;
  font-weight: 600;
  white-space: nowrap;
  color: #fff;
  background: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(31, 111, 229, 0.25);
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s, padding 0.22s ease;
}

.abtn--sm {
  --h: 36px;
  --icon: 16px;
  padding: 0 14px;
  font-size: 13px;
}

.abtn:hover:not(:disabled) {
  background: var(--primary-hover);
  box-shadow: 0 6px 16px rgba(31, 111, 229, 0.32);
}

/* White button for Cancel. */
.abtn--secondary {
  color: var(--text);
  background: var(--surface);
  border-color: var(--border);
  box-shadow: none;
}

.abtn--secondary:hover:not(:disabled) {
  background: var(--surface-muted);
  box-shadow: none;
}

.abtn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--focus);
}

.abtn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  box-shadow: none;
}

.abtn__label {
  display: grid;
  grid-template-columns: 1fr;
  margin-left: 8px;
}

.abtn__text {
  overflow: hidden;
}

/* ---------- compact: icon only until hovered ---------- */
.abtn--compact {
  /* Square padding so the icon sits in a circle. */
  padding: 0 calc((var(--h) - var(--icon)) / 2 - 1px);
}

/* The label is a 0-width grid column that grows to its text width. */
.abtn--compact .abtn__label {
  grid-template-columns: 0fr;
  margin-left: 0;
  opacity: 0;
  transition: grid-template-columns 0.22s ease, opacity 0.15s ease, margin 0.22s ease;
}

.abtn--compact:hover .abtn__label,
.abtn--compact:focus-visible .abtn__label,
.abtn--compact.abtn--open .abtn__label {
  grid-template-columns: 1fr;
  margin-left: 8px;
  opacity: 1;
}

.abtn--compact:hover,
.abtn--compact:focus-visible,
.abtn--compact.abtn--open {
  padding: 0 16px 0 calc((var(--h) - var(--icon)) / 2 - 1px);
}

@media (hover: none) {
  .abtn--compact,
  .abtn--compact:hover {
    padding: 0 14px;
  }
  .abtn--compact .abtn__label {
    grid-template-columns: 1fr;
    margin-left: 8px;
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .abtn,
  .abtn--compact .abtn__label {
    transition: none;
  }
}
</style>
