<!--
  Entry point for the sign in / sign up page: Django mounts this file (see
  AuthPageView in backend/apps/accounts/views.py). The props from
  get_page_props() fall through to <Auth /> automatically. The page UI lives
  in Auth.vue.
-->
<template>
  <Auth />
</template>

<script setup>
import Auth from './Auth.vue';
</script>
