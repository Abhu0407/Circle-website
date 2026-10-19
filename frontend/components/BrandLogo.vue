<!-- Circle logo mark + wordmark. `dark` switches the wordmark to dark text for light backgrounds. -->
<template>
  <span class="brand" :class="{ 'brand--dark': dark }">
    <svg class="brand__mark" viewBox="0 0 32 32" :width="size" :height="size" aria-hidden="true">
      <defs>
        <linearGradient :id="gradId" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#22b8c9" />
          <stop offset="1" stop-color="#1f6fe5" />
        </linearGradient>
      </defs>
      <path d="M22 6.5A10 10 0 0 0 6.2 14" fill="none" :stroke="`url(#${gradId})`" stroke-width="4.5" stroke-linecap="round" />
      <path d="M10 25.5A10 10 0 0 0 25.8 18" fill="none" :stroke="`url(#${gradId})`" stroke-width="4.5" stroke-linecap="round" />
      <circle cx="16" cy="16" r="3.2" fill="#22b8c9" />
    </svg>
    <span class="brand__name">Circle</span>
  </span>
</template>

<script setup>
defineProps({
  dark: { type: Boolean, default: false },
  size: { type: Number, default: 32 },
});

// Unique per instance so two logos on one page don't share a gradient id.
const gradId = 'circle-grad-' + Math.random().toString(36).slice(2, 8);
</script>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--night-text);
}

.brand--dark {
  color: var(--text);
}

.brand__name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.brand--dark .brand__name {
  font-size: 18px;
}
</style>
