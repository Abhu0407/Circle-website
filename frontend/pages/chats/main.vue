<!--
  Entry point for the Chats page: Django mounts this file (see
  ChatsPageView in backend/apps/chat/views.py). The props from
  get_page_props() fall through to <Chats /> automatically.
-->
<template>
  <Chats />
</template>

<script setup>
import Chats from './Chats.vue';
</script>
