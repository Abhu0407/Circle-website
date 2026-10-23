<!--
  Entry point for the private special page: Django mounts this file (see
  SpecialPageView in backend/apps/special/views.py). The props from
  get_page_props() fall through to <Special /> automatically.
-->
<template>
  <Special />
</template>

<script setup>
import Special from './Special.vue';
</script>
