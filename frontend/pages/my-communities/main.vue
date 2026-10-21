<!--
  Entry point for the My Communities page: Django mounts this file (see
  MyCommunitiesPageView in backend/apps/communities/views.py). The props from
  get_page_props() fall through to <MyCommunities /> automatically.
-->
<template>
  <MyCommunitiesPage />
</template>

<script setup>
import MyCommunitiesPage from './MyCommunities.vue';
</script>
