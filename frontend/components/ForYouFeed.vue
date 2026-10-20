<!--
  Home's For You tab (inside the page's PageSheet): posts from every
  community, shuffled with a lean towards the user's interests and activity
  (see backend/apps/posts/feed.py), loading more while scrolling. Rows of
  suggested communities the user hasn't joined sit between the posts.
  Emits `joined` with a community joined from a suggestion, and `navigate`
  (tab id) for the empty-state buttons.
  Usage: <ForYouFeed :feed-api="feedApi" :suggestions-api="suggestionsApi" :posts-api="postsApi"
                     :communities-api="communitiesApi" :user="me" @joined="..." @navigate="go" />
-->
<template>
  <div class="foryou">
    <div class="toolbar">
      <p class="toolbar__label">Picked for you from <strong>all communities</strong></p>
      <ActionButton icon="sparkle" label="Shuffle" size="sm" variant="secondary" :disabled="loading" @click="shuffle" />
    </div>

    <template v-for="item in items" :key="item.key">
      <PostCard v-if="item.post" :post="item.post" :posts-api="postsApi" :user="user" @deleted="onDeleted" />
      <SuggestedCommunities
        v-else
        :communities="item.communities"
        :communities-api="communitiesApi"
        @joined="$emit('joined', $event)"
      />
    </template>

    <p v-if="loading" class="foryou__note">Loading posts…</p>
    <EmptyState v-else-if="error" icon="close" :text="error">
      <ActionButton icon="back" label="Try again" @click="load(!posts.length)" />
    </EmptyState>
    <EmptyState v-else-if="!posts.length" icon="chat" text="No posts yet. Find a community and start the conversation.">
      <ActionButton icon="compass" label="Discover communities" @click="$emit('navigate', 'discover')" />
      <ActionButton icon="plus" label="Create a community" variant="secondary" @click="$emit('navigate', 'create')" />
    </EmptyState>
    <p v-else-if="!next" class="foryou__note">You're all caught up.</p>

    <!-- Coming into view loads the next page. -->
    <div ref="sentinel" class="foryou__sentinel" aria-hidden="true"></div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { apiGet } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import EmptyState from './EmptyState.vue';
import PostCard from './PostCard.vue';
import SuggestedCommunities from './SuggestedCommunities.vue';

// The first suggestion row comes after this many posts, then one every GAP posts.
const FIRST_AT = 3;
const GAP = 6;
// Communities per row.
const PER_ROW = 4;

const props = defineProps({
  feedApi: { type: String, required: true },
  suggestionsApi: { type: String, required: true },
  postsApi: { type: String, required: true },
  communitiesApi: { type: String, required: true },
  user: { type: Object, required: true },
});
defineEmits(['joined', 'navigate']);

const posts = ref([]);
const suggestions = ref([]);
// URL of the next page, from the API.
const next = ref(null);
const loading = ref(false);
const error = ref('');
const sentinel = ref(null);

// The order of the feed; a new seed reshuffles it.
const newSeed = () => Math.random().toString(36).slice(2, 10);
let seed = newSeed();
// Ignore answers to requests made before a shuffle.
let request = 0;
let observer = null;

// Posts with suggestion rows slotted in; leftover rows go at the end
// (only the first one if there are few posts).
const items = computed(() => {
  const rows = [];
  for (let i = 0; i < suggestions.value.length; i += PER_ROW) rows.push(suggestions.value.slice(i, i + PER_ROW));
  const out = [];
  let row = 0;
  posts.value.forEach((post, i) => {
    out.push({ key: `p${post.id}`, post });
    const n = i + 1;
    if (row < rows.length && (n === FIRST_AT || (n > FIRST_AT && (n - FIRST_AT) % GAP === 0))) {
      out.push({ key: `s${row}`, communities: rows[row++] });
    }
  });
  if (!loading.value && !next.value && row === 0 && rows.length) out.push({ key: 's0', communities: rows[0] });
  return out;
});

async function load(reset) {
  if (loading.value && !reset) return;
  const id = ++request;
  loading.value = true;
  error.value = '';
  try {
    const page = reset ? await apiGet(props.feedApi, { seed }) : await apiGet(next.value);
    if (id !== request) return;
    // Liking things while scrolling can shift the order a little; skip repeats.
    const seen = new Set(reset ? [] : posts.value.map((p) => p.id));
    const fresh = page.results.filter((p) => !seen.has(p.id));
    posts.value = reset ? fresh : [...posts.value, ...fresh];
    next.value = page.next;
    // The observer only fires on a change, so keep going while the end is still in view.
    await nextTick();
    if (id === request && next.value && sentinel.value
        && sentinel.value.getBoundingClientRect().top < window.innerHeight + 600) {
      loading.value = false;
      load(false);
    }
  } catch {
    if (id === request) error.value = 'Could not load posts.';
  } finally {
    if (id === request) loading.value = false;
  }
}

async function loadSuggestions() {
  try {
    suggestions.value = await apiGet(props.suggestionsApi);
  } catch {
    suggestions.value = []; // the feed works without them
  }
}

function shuffle() {
  seed = newSeed();
  posts.value = [];
  next.value = null;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  load(true);
  loadSuggestions();
}

function onDeleted(id) {
  posts.value = posts.value.filter((p) => p.id !== id);
}

onMounted(() => {
  load(true);
  loadSuggestions();
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && next.value && !error.value) load(false);
    },
    { rootMargin: '600px 0px' }
  );
  observer.observe(sentinel.value);
});

onBeforeUnmount(() => observer && observer.disconnect());
</script>

<style scoped>
.foryou {
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
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.toolbar__label strong {
  color: var(--text);
}

.foryou__note {
  margin: 0;
  padding: 12px;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
}

.foryou__sentinel {
  height: 1px;
}
</style>
