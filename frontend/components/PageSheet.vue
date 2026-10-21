<!--
  The page frame used by every signed-in page (same look as Profile): the
  title on the dark header band, then one white sheet holding the page.
  Usage:
    <PageSheet title="My Communities">...</PageSheet>
    <PageSheet title="Community" back-url="/communities/" back-label="My Communities">...</PageSheet>
-->
<template>
  <section class="page">
    <a v-if="backUrl" :href="backUrl" class="page__back"><Icon name="back" :size="16" /> {{ backLabel }}</a>
    <h1 class="page__title">{{ title }}</h1>
    <div class="sheet"><slot /></div>
  </section>
</template>

<script setup>
import Icon from './Icon.vue';

defineProps({
  title: { type: String, required: true },
  backUrl: { type: String, default: '' },
  backLabel: { type: String, default: 'Back' },
});
</script>

<style scoped>
.page__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--night-muted);
}

.page__back:hover {
  color: var(--night-text);
  text-decoration: none;
}

.page__title {
  margin: 0 0 16px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--night-text);
}

.sheet {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  background: var(--surface);
  border-radius: 22px;
  box-shadow: 0 10px 30px rgba(8, 19, 31, 0.14);
}

@media (max-width: 560px) {
  .sheet {
    gap: 16px;
    padding: 12px;
    border-radius: 18px;
  }
}
</style>
