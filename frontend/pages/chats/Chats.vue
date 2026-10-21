<!--
  The Chats page (/chats/): your communities' chats; /chats/?community=3
  opens that chat. Opening a chat and going back don't reload the page.
-->
<template>
  <BaseLayout
    :user="user"
    active="chats"
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
    <PageSheet title="Chats">
      <ChatRoom v-if="chatId" :key="chatId" :community-id="chatId" :user="user" @back="openChat(null)" />
      <ChatList v-else :user="user" @open="openChat" @navigate="go" />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import BaseLayout from '../../components/BaseLayout.vue';
import ChatList from '../../components/ChatList.vue';
import ChatRoom from '../../components/ChatRoom.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from ChatsPageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});

// The community whose chat is open, or null for the list.
const chatIdFromUrl = () => Number(new URLSearchParams(window.location.search).get('community')) || null;
const chatId = ref(chatIdFromUrl());

function go(id) {
  window.circleNavigate(props.navUrls[id]);
}

// Open a chat (or the list, with null) and keep the address bar in step.
function openChat(id) {
  chatId.value = id;
  const url = id ? `${props.navUrls.chats}?community=${id}` : props.navUrls.chats;
  if (url !== window.location.pathname + window.location.search) history.pushState({}, '', url);
}

// Back/forward between the list and a chat stay on this page (see main.js).
function onPopState() {
  chatId.value = chatIdFromUrl();
}

onMounted(() => window.addEventListener('popstate', onPopState));
onBeforeUnmount(() => window.removeEventListener('popstate', onPopState));
</script>
