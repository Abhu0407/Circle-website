<!--
  Entry point for this page: Django mounts this file (see PostPageView in
  backend/apps/posts/views.py). The props from get_page_props() fall
  through to <Post /> automatically. The page UI lives in Post.vue.
-->
<template>
  <Post />
</template>

<script setup>
import Post from './Post.vue';
</script>
