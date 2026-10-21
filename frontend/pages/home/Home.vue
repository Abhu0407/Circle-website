<template>
  <BaseLayout
    :user="me"
    :active="active"
    :local-tabs="LOCAL_TABS"
    :home-url="homeUrl"
    :profile-url="profileUrl"
    :signout-api="signoutApi"
    :signin-url="signinUrl"
    :map-tile-url="mapTileUrl"
    :chats-api="chatsApi"
    :chat-socket-path="chatSocketPath"
    :chat-max-file-mb="chatMaxFileMb"
    :map-people="mapPeople"
    :events="events"
    @navigate="go"
  >
    <PageSheet v-if="active === 'foryou'" title="For You">
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

    <PageSheet v-else-if="active === 'discover'" title="Discover Communities">
      <DiscoverCommunities
        :communities-api="communitiesApi"
        :categories="communityCategories"
        :user="me"
        :profile-url="profileUrl"
        @joined="onJoined"
        @create="go('create')"
      />
    </PageSheet>

    <PageSheet v-else-if="active === 'communities'" title="My Communities">
      <MyCommunities :posts-api="postsApi" :user="me" @navigate="go" />
    </PageSheet>

    <PageSheet v-else-if="active === 'chats'" title="Chats">
      <ChatRoom v-if="chatId" :key="chatId" :community-id="chatId" :user="me" @back="go('chats')" />
      <ChatList v-else :user="me" @open="openChat" @navigate="go" />
    </PageSheet>

    <PageSheet v-else-if="active === 'create'" title="Create a Community">
      <CommunityForm
        :communities-api="communitiesApi"
        :categories="communityCategories"
        :covers="communityCovers"
        :user="me"
        :map-tile-url="mapTileUrl"
        :map-search-api="mapSearchApi"
        :map-reverse-api="mapReverseApi"
      />
    </PageSheet>

    <PageSheet v-else :title="activeLabel">
      <EmptyState :icon="activeIcon" :text="`${activeLabel} is coming soon.`">
        <ActionButton icon="back" label="Back to For You" @click="go('foryou')" />
      </EmptyState>
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import ActionButton from '../../components/ActionButton.vue';
import BaseLayout from '../../components/BaseLayout.vue';
import ChatList from '../../components/ChatList.vue';
import ChatRoom from '../../components/ChatRoom.vue';
import CommunityForm from '../../components/CommunityForm.vue';
import DiscoverCommunities from '../../components/DiscoverCommunities.vue';
import EmptyState from '../../components/EmptyState.vue';
import ForYouFeed from '../../components/ForYouFeed.vue';
import MyCommunities from '../../components/MyCommunities.vue';
import PageSheet from '../../components/PageSheet.vue';

// Props come from HomePageView.get_page_props() in Django.
// events: [{ id, title, time, color }]
const props = defineProps({
  user: { type: Object, required: true },
  tab: { type: String, default: 'foryou' },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  feedApi: { type: String, required: true },
  suggestionsApi: { type: String, required: true },
  postsApi: { type: String, required: true },
  communitiesApi: { type: String, required: true },
  communityCategories: { type: Array, default: () => [] },
  communityCovers: { type: Object, default: () => ({}) },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapPeople: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
});

// Sections of this page; switching between them doesn't reload.
const TABS = {
  discover: { label: 'Discover', icon: 'compass' },
  communities: { label: 'My Communities', icon: 'users' },
  chats: { label: 'Chats', icon: 'chat' },
  create: { label: 'Create Community', icon: 'plus' },
};
const LOCAL_TABS = ['foryou', ...Object.keys(TABS)];

const active = ref(props.tab);
// Chats tab: the community whose chat is open (/?tab=chats&community=3), or null for the list.
const chatIdFromUrl = () => Number(new URLSearchParams(window.location.search).get('community')) || null;
const chatId = ref(props.tab === 'chats' ? chatIdFromUrl() : null);
// The signed-in user; joining from Discover adds to `join_community` here,
// so My Communities shows it without a reload.
const me = ref(props.user);

const activeLabel = computed(() => (TABS[active.value] || {}).label);
const activeIcon = computed(() => (TABS[active.value] || {}).icon);

// Switch section and keep the address bar in step (/?tab=chats can be bookmarked).
function go(tab) {
  active.value = tab;
  chatId.value = null;
  const url = tab === 'foryou' ? props.homeUrl : `${props.homeUrl}?tab=${tab}`;
  if (url !== window.location.pathname + window.location.search) history.pushState({ tab }, '', url);
}

function openChat(id) {
  chatId.value = id;
  history.pushState({ tab: 'chats' }, '', `${props.homeUrl}?tab=chats&community=${id}`);
}

function onPopState() {
  const tab = new URLSearchParams(window.location.search).get('tab');
  active.value = TABS[tab] ? tab : 'foryou';
  chatId.value = active.value === 'chats' ? chatIdFromUrl() : null;
}

onMounted(() => window.addEventListener('popstate', onPopState));
onBeforeUnmount(() => window.removeEventListener('popstate', onPopState));

function onJoined(community) {
  const joined = me.value.join_community || [];
  if (joined.some((c) => c.id === community.id)) return;
  me.value = { ...me.value, join_community: [...joined, community].sort((a, b) => a.name.localeCompare(b.name)) };
}
</script>
