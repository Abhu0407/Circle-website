<!--
  Entry point for the Notifications page: Django mounts this file (see
  NotificationsPageView in backend/apps/notifications/views.py). The props
  from get_page_props() fall through to <Notifications /> automatically.
-->
<template>
  <Notifications />
</template>

<script setup>
import Notifications from './Notifications.vue';
</script>
