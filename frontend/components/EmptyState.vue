<!--
  Dashed "nothing here yet" box with an icon, a line of text and buttons
  (default slot), as on Profile.
  Usage: <EmptyState icon="users" text="No members yet."><ActionButton ... /></EmptyState>
-->
<template>
  <div class="blank">
    <Icon :name="icon" :size="28" />
    <p>{{ text }}</p>
    <div v-if="$slots.default" class="blank__actions"><slot /></div>
  </div>
</template>

<script setup>
import Icon from './Icon.vue';

defineProps({
  icon: { type: String, required: true },
  text: { type: String, required: true },
});
</script>

<style scoped>
.blank {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 16px;
  text-align: center;
  color: var(--muted);
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.blank p {
  max-width: 340px;
  margin: 0;
  font-size: 14px;
}

.blank__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}
</style>
