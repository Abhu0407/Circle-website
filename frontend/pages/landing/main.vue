<!--
  Entry point for the landing page shown at / before signing in: Django mounts
  this file (see LandingPageView in backend/apps/accounts/views.py). The props
  from get_page_props() fall through to <Landing /> automatically. The page UI
  lives in Landing.vue.
-->
<template>
  <Landing />
</template>

<script setup>
import Landing from './Landing.vue';
</script>
