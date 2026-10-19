<!--
  Entry point for this page: Django mounts this file (see VuePageView in
  backend/apps/accounts/views.py). The props from get_page_props() fall
  through to <Home /> automatically. The page UI lives in Home.vue.
-->
<template>
  <Home />
</template>

<script setup>
import Home from './Home.vue';
</script>
