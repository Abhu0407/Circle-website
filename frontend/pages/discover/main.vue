<!--
  Entry point for the Discover page: Django mounts this file (see
  DiscoverPageView in backend/apps/communities/views.py). The props from
  get_page_props() fall through to <Discover /> automatically.
-->
<template>
  <Discover />
</template>

<script setup>
import Discover from './Discover.vue';
</script>
