<!-- The My Communities page (/communities/): the communities you joined and their posts. -->
<template>
  <BaseLayout
    :user="user"
    active="communities"
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
    <PageSheet title="My Communities">
      <MyCommunities :posts-api="postsApi" :user="user" @navigate="go" />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import BaseLayout from '../../components/BaseLayout.vue';
import MyCommunities from '../../components/MyCommunities.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from MyCommunitiesPageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  postsApi: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});

function go(id) {
  window.circleNavigate(props.navUrls[id]);
}
</script>
