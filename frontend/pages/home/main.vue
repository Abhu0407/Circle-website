<!--
  Entry point for the For You page: Django mounts this file (see
  HomePageView in backend/apps/accounts/views.py). The props from
  get_page_props() fall through to <Home /> automatically.
-->
<template>
  <Home />
</template>

<script setup>
import Home from './Home.vue';
</script>
