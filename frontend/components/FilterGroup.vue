<!--
  One titled group of choices inside a FilterMenu panel.
  Usage: <FilterGroup label="Category" hint="Pick one or more"><FilterChip ... /></FilterGroup>
  Slot `note` adds a line under the choices.
-->
<template>
  <section class="fgroup">
    <h3 class="fgroup__label">{{ label }} <span v-if="hint" class="fgroup__hint">{{ hint }}</span></h3>
    <div class="fgroup__chips" role="group" :aria-label="label"><slot /></div>
    <p v-if="$slots.note" class="fgroup__note"><slot name="note" /></p>
  </section>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  hint: { type: String, default: '' },
});
</script>

<style scoped>
.fgroup__label {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
}

.fgroup__hint {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
}

.fgroup__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.fgroup__chips :deep(.fchip:disabled) {
  cursor: not-allowed;
  opacity: 0.45;
}

.fgroup__note {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--muted);
}
</style>
