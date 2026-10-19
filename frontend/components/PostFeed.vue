<!--
  Posts from the communities the user joined (newest first), with a
  Filters button to show one community and a composer to post. Used on Home's My Communities tab.
  Given a `community`, shows only that community's posts instead, and the
  composer only while `canPost` (the user is a member).
  Emits `created` (post) and `deleted` (id) so a page can keep counts.
  Usage: <PostFeed :posts-api="postsApi" :user="user" />
         <PostFeed :posts-api="postsApi" :user="user" :community="c" :can-post="c.is_member" />
-->
<template>
  <div class="feed">
    <div v-if="!community && communities.length > 1" class="toolbar">
      <p class="toolbar__label">
        Showing posts from
        <button v-if="communityId" type="button" class="pill" aria-label="Show all communities again" @click="show(null)">
          {{ shownName }} <Icon name="close" :size="12" />
        </button>
        <strong v-else>all your communities</strong>
      </p>
      <FilterMenu :count="communityId ? 1 : 0" @clear="show(null)">
        <FilterGroup label="Community" hint="pick one">
          <FilterChip
            v-for="c in communities"
            :key="c.id"
            :on="communityId === c.id"
            @click="show(communityId === c.id ? null : c.id)"
          >{{ c.name }}</FilterChip>
        </FilterGroup>
      </FilterMenu>
    </div>

    <template v-if="community || communities.length">
      <PostComposer
        v-if="community ? canPost : true"
        :communities="community ? [community] : communities"
        :posts-api="postsApi"
        :user="user"
        :default-community="communityId"
        @created="onCreated"
      />

      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        :posts-api="postsApi"
        :user="user"
        @deleted="onDeleted"
      />

      <p v-if="loading" class="feed__note">Loading posts…</p>
      <EmptyState v-else-if="error" icon="close" :text="error">
        <ActionButton icon="back" label="Try again" @click="load(true)" />
      </EmptyState>
      <EmptyState
        v-else-if="!posts.length"
        icon="chat"
        :text="community && !canPost ? 'No posts yet. Join to start the conversation.' : 'No posts yet. Be the first to share something.'"
      />
      <div v-else-if="next" class="feed__more">
        <ActionButton icon="chevron" label="Load more" variant="secondary" @click="load(false)" />
      </div>
    </template>

    <EmptyState v-else icon="users" text="Join a community to see its posts and start posting.">
      <ActionButton icon="compass" label="Discover communities" @click="$emit('discover')" />
    </EmptyState>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { apiGet } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import EmptyState from './EmptyState.vue';
import FilterChip from './FilterChip.vue';
import FilterGroup from './FilterGroup.vue';
import FilterMenu from './FilterMenu.vue';
import Icon from './Icon.vue';
import PostCard from './PostCard.vue';
import PostComposer from './PostComposer.vue';

const props = defineProps({
  postsApi: { type: String, required: true },
  user: { type: Object, required: true },
  // { id, name }: show only this community's posts.
  community: { type: Object, default: null },
  canPost: { type: Boolean, default: true },
});
const emit = defineEmits(['discover', 'created', 'deleted']);

const communities = computed(() => props.user.join_community || []);

const posts = ref([]);
// Cursor URL of the next page, from the API.
const next = ref(null);
const communityId = ref(props.community ? props.community.id : null);
const shownName = computed(() => (communities.value.find((c) => c.id === communityId.value) || {}).name);
const loading = ref(false);
const error = ref('');
// Ignore answers to requests made before the filter changed.
let request = 0;

async function load(reset) {
  const id = ++request;
  loading.value = true;
  error.value = '';
  try {
    const params = communityId.value ? { community: communityId.value } : {};
    const page = reset ? await apiGet(props.postsApi, params) : await apiGet(next.value);
    if (id !== request) return;
    posts.value = reset ? page.results : [...posts.value, ...page.results];
    next.value = page.next;
  } catch {
    if (id === request) error.value = 'Could not load posts.';
  } finally {
    if (id === request) loading.value = false;
  }
}

function show(id) {
  if (communityId.value === id) return;
  communityId.value = id;
  posts.value = [];
  load(true);
}

function onCreated(post) {
  if (!communityId.value || communityId.value === post.community.id) posts.value.unshift(post);
  emit('created', post);
}

function onDeleted(id) {
  posts.value = posts.value.filter((p) => p.id !== id);
  emit('deleted', id);
}

onMounted(() => {
  if (props.community || communities.value.length) load(true);
});
</script>

<style scoped>
.feed {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toolbar__label {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.toolbar__label strong {
  color: var(--text);
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-soft);
  border: 1px solid #c9dafa;
  border-radius: 999px;
  cursor: pointer;
}

.pill:hover {
  border-color: var(--primary);
}

.feed__note {
  margin: 0;
  padding: 12px;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
}

.feed__more {
  display: flex;
  justify-content: center;
}
</style>
