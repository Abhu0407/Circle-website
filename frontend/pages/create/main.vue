<!--
  Entry point for the Create Community page: Django mounts this file (see
  CreateCommunityPageView in backend/apps/communities/views.py). The props
  from get_page_props() fall through to <Create /> automatically.
-->
<template>
  <Create />
</template>

<script setup>
import Create from './Create.vue';
</script>
