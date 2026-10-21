<!--
  The For You page (/): posts picked for the user from every community, with
  communities to join in between. The other menu items are their own pages
  (pages/discover, pages/my-communities, pages/chats, pages/create).
-->
<template>
  <BaseLayout
    :user="me"
    active="foryou"
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
    <PageSheet title="For You">
      <ForYouFeed
        :feed-api="feedApi"
        :suggestions-api="suggestionsApi"
        :posts-api="postsApi"
        :communities-api="communitiesApi"
        :user="me"
        @joined="onJoined"
        @navigate="go"
      />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import { ref } from 'vue';
import BaseLayout from '../../components/BaseLayout.vue';
import ForYouFeed from '../../components/ForYouFeed.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from HomePageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  feedApi: { type: String, required: true },
  suggestionsApi: { type: String, required: true },
  postsApi: { type: String, required: true },
  communitiesApi: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});

// The signed-in user; joining a suggested community adds to `join_community`.
const me = ref(props.user);

// Buttons inside the feed ask for another page by its menu id.
function go(id) {
  window.circleNavigate(props.navUrls[id]);
}

function onJoined(community) {
  const joined = me.value.join_community || [];
  if (joined.some((c) => c.id === community.id)) return;
  me.value = { ...me.value, join_community: [...joined, community].sort((a, b) => a.name.localeCompare(b.name)) };
}
</script>
