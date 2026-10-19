<!--
  A grey section box inside a PageSheet (same look as Profile's cards):
  a header with the title, an optional count and an action on the right.
  Usage:
    <SectionCard title="Members" :count="12" wide>
      <template #action><ActionButton icon="plus" label="Add" size="sm" compact /></template>
      ...
    </SectionCard>
  `wide` spans both columns of a CardGrid.
-->
<template>
  <article class="card" :class="{ 'card--wide': wide }">
    <header v-if="title || $slots.action" class="card__head">
      <h2 class="card__title">
        {{ title }}
        <span v-if="count !== null && count !== undefined" class="card__count">{{ count }}</span>
      </h2>
      <slot name="action" />
    </header>
    <slot />
  </article>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  count: { type: [Number, String], default: null },
  wide: { type: Boolean, default: false },
});
</script>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 18px 20px 20px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 16px;
  scroll-margin-top: 16px;
}

.card--wide {
  grid-column: 1 / -1;
}

.card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 36px;
  margin-bottom: 12px;
}

.card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.card__count {
  margin-left: 6px;
  padding: 1px 9px;
  font-size: 12px;
  font-weight: 600;
  vertical-align: 2px;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 99px;
}

@media (max-width: 560px) {
  .card {
    padding: 16px;
  }
}
</style>
