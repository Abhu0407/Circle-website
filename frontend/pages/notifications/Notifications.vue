<!--
  The Notifications page (/notifications/): every post uploaded and every
  community created by other people, newest first.
-->
<template>
  <BaseLayout
    :user="user"
    active="notifications"
    :nav-urls="navUrls"
    :home-url="homeUrl"
    :profile-url="profileUrl"
    :signout-api="signoutApi"
    :signin-url="signinUrl"
    :map-tile-url="mapTileUrl"
    :chats-api="chatsApi"
    :chat-socket-path="chatSocketPath"
    :chat-max-file-mb="chatMaxFileMb"
    :map-people="mapPeople"
    :notifications-unread="notificationsUnread"
  >
    <PageSheet title="Notifications">
      <NotificationList :notifications-api="notificationsApi" :seen-at="seenAt" />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import BaseLayout from '../../components/BaseLayout.vue';
import NotificationList from '../../components/NotificationList.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from NotificationsPageView.get_page_props() in Django.
defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  notificationsApi: { type: String, required: true },
  seenAt: { type: String, default: '' },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});
</script>
