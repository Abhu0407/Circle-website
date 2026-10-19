<!-- Illustrated cover image for an activity/community card. -->
<template>
  <svg class="art" viewBox="0 0 240 140" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <template v-if="kind === 'football'">
      <rect width="240" height="140" fill="#3d8b3d" />
      <g fill="#46994a">
        <rect x="0" width="30" height="140" /><rect x="60" width="30" height="140" />
        <rect x="120" width="30" height="140" /><rect x="180" width="30" height="140" />
      </g>
      <g fill="none" stroke="#fff" stroke-opacity="0.85" stroke-width="2">
        <rect x="14" y="12" width="212" height="116" />
        <line x1="120" y1="12" x2="120" y2="128" />
        <circle cx="120" cy="70" r="18" />
        <rect x="14" y="44" width="26" height="52" />
        <rect x="200" y="44" width="26" height="52" />
      </g>
      <circle cx="120" cy="70" r="2.5" fill="#fff" />
    </template>

    <template v-else-if="kind === 'tennis'">
      <rect width="240" height="140" fill="#4f8a4a" />
      <rect x="22" y="14" width="196" height="112" fill="#2f6db5" />
      <g fill="none" stroke="#fff" stroke-width="2">
        <rect x="22" y="14" width="196" height="112" />
        <line x1="22" y1="28" x2="218" y2="28" />
        <line x1="22" y1="112" x2="218" y2="112" />
        <line x1="72" y1="28" x2="72" y2="112" />
        <line x1="168" y1="28" x2="168" y2="112" />
        <line x1="72" y1="70" x2="168" y2="70" />
      </g>
      <line x1="120" y1="8" x2="120" y2="132" stroke="#e9eef5" stroke-width="3" />
      <circle cx="150" cy="48" r="5" fill="#d8f04a" />
    </template>

    <template v-else-if="kind === 'cricket'">
      <rect width="240" height="140" fill="#2f7a3a" />
      <ellipse cx="120" cy="70" rx="112" ry="64" fill="#3c8f45" />
      <ellipse cx="120" cy="70" rx="60" ry="36" fill="none" stroke="#fff" stroke-opacity="0.5" stroke-width="1.5" stroke-dasharray="4 4" />
      <rect x="108" y="40" width="24" height="60" rx="2" fill="#c9b07a" />
      <g stroke="#fff" stroke-width="1.5">
        <line x1="108" y1="48" x2="132" y2="48" />
        <line x1="108" y1="92" x2="132" y2="92" />
      </g>
    </template>

    <template v-else-if="kind === 'tech'">
      <defs>
        <linearGradient id="art-tech" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#13284a" /><stop offset="1" stop-color="#1f6fe5" />
        </linearGradient>
      </defs>
      <rect width="240" height="140" fill="url(#art-tech)" />
      <g fill="none" stroke="#22b8c9" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M92 50 72 70l20 20" /><path d="M148 50l20 20-20 20" />
      </g>
      <line x1="128" y1="44" x2="112" y2="96" stroke="#fff" stroke-width="5" stroke-linecap="round" />
    </template>

    <template v-else>
      <defs>
        <linearGradient id="art-arts" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#f59f00" /><stop offset="1" stop-color="#d6336c" />
        </linearGradient>
      </defs>
      <rect width="240" height="140" fill="url(#art-arts)" />
      <circle cx="70" cy="60" r="30" fill="#fff" fill-opacity="0.25" />
      <circle cx="150" cy="84" r="40" fill="#7048e8" fill-opacity="0.35" />
      <circle cx="190" cy="40" r="18" fill="#22b8c9" fill-opacity="0.5" />
    </template>
  </svg>
</template>

<script setup>
defineProps({
  // football | tennis | cricket | tech | arts
  kind: { type: String, default: 'arts' },
});
</script>

<style scoped>
.art {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
