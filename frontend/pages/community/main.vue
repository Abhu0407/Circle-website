<!--
  Entry point for this page: Django mounts this file (see CommunityPageView
  in backend/apps/communities/views.py). The props from get_page_props()
  fall through to <Community /> automatically. The page UI lives in Community.vue.
-->
<template>
  <Community />
</template>

<script setup>
import Community from './Community.vue';
</script>
