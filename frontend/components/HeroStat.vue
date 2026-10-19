<!-- One number in PageHero's stats row, e.g. "12 Members"; clickable. -->
<template>
  <button type="button" class="stat">
    <strong>{{ value }}</strong>
    <span>{{ label }}</span>
  </button>
</template>

<script setup>
defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
});
</script>

<style scoped>
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 10px 14px;
  font: inherit;
  text-align: center;
  color: var(--text);
  background: var(--surface-muted);
  border: 1px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.stat:hover {
  background: var(--primary-soft);
  border-color: #c9dafa;
}

.stat strong {
  font-size: 20px;
  line-height: 1.2;
}

.stat span {
  overflow: hidden;
  max-width: 100%;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--muted);
}

@media (max-width: 560px) {
  .stat {
    padding: 8px 6px;
  }
  .stat strong {
    font-size: 17px;
  }
}
</style>
