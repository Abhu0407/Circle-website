<!-- The Discover page (/discover/): browse and search every community, and join. -->
<template>
  <BaseLayout
    :user="me"
    active="discover"
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
    <PageSheet title="Discover Communities">
      <DiscoverCommunities
        :communities-api="communitiesApi"
        :categories="communityCategories"
        :user="me"
        :profile-url="profileUrl"
        @joined="onJoined"
        @create="go('create')"
      />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import { ref } from 'vue';
import BaseLayout from '../../components/BaseLayout.vue';
import DiscoverCommunities from '../../components/DiscoverCommunities.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from DiscoverPageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  communitiesApi: { type: String, required: true },
  communityCategories: { type: Array, default: () => [] },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});

// The signed-in user; joining a community adds to `join_community`.
const me = ref(props.user);

function go(id) {
  window.circleNavigate(props.navUrls[id]);
}

function onJoined(community) {
  const joined = me.value.join_community || [];
  if (joined.some((c) => c.id === community.id)) return;
  me.value = { ...me.value, join_community: [...joined, community].sort((a, b) => a.name.localeCompare(b.name)) };
}
</script>
