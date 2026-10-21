<!-- The Create Community page (/create/): the form to start a new community. -->
<template>
  <BaseLayout
    :user="user"
    active="create"
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
    <PageSheet title="Create a Community">
      <CommunityForm
        :communities-api="communitiesApi"
        :categories="communityCategories"
        :covers="communityCovers"
        :user="user"
        :map-tile-url="mapTileUrl"
        :map-search-api="mapSearchApi"
        :map-reverse-api="mapReverseApi"
      />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import BaseLayout from '../../components/BaseLayout.vue';
import CommunityForm from '../../components/CommunityForm.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from CreateCommunityPageView.get_page_props() in Django.
defineProps({
  user: { type: Object, required: true },
  navUrls: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  communitiesApi: { type: String, required: true },
  communityCategories: { type: Array, default: () => [] },
  // { category: [{ value, label, url }] }: pictures a community can pick.
  communityCovers: { type: Object, default: () => ({}) },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  notificationsUnread: { type: Number, default: 0 },
});
</script>
