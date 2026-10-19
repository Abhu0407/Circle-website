<!--
  A toggle chip for filters and quick picks (same shape as Profile's tags).
  Usage: <FilterChip :on="nearby" @click="nearby = !nearby">Within 10km</FilterChip>
-->
<template>
  <button type="button" class="fchip" :class="{ 'fchip--on': on }" :aria-pressed="on"><slot /></button>
</template>

<script setup>
defineProps({
  on: { type: Boolean, default: false },
});
</script>

<style scoped>
.fchip {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 14px;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.fchip:hover {
  border-color: #c9dafa;
  background: var(--primary-soft);
}

.fchip--on,
.fchip--on:hover {
  color: var(--primary);
  background: var(--primary-soft);
  border-color: var(--primary);
}

.fchip:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--focus);
}
</style>
