<!--
  Entry point for the Profile page: Django mounts this file (see
  ProfilePageView in backend/apps/accounts/views.py). The props from
  get_page_props() fall through to <Profile /> automatically.
-->
<template>
  <Profile />
</template>

<script setup>
import Profile from './Profile.vue';
</script>
