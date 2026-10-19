<template>
  <BaseLayout
    :user="user"
    :active="active"
    :local-tabs="LOCAL_TABS"
    :home-url="homeUrl"
    :profile-url="profileUrl"
    :signout-api="signoutApi"
    :signin-url="signinUrl"
    :people="people"
    :events="events"
    @navigate="go"
  >
    <template v-if="active === 'discover'">
      <h1 class="main__title">Discover People &amp; Activities</h1>

      <div class="filters">
        <label class="search">
          <Icon name="search" :size="18" />
          <input v-model="query" type="search" placeholder="Search" aria-label="Search people and activities" />
        </label>
        <div class="chips">
          <button
            v-for="c in CATEGORIES"
            :key="c"
            type="button"
            class="chip"
            :class="{ 'chip--on': categories.has(c) }"
            :aria-pressed="categories.has(c)"
            @click="toggle(categories, c)"
          >{{ c }}</button>
          <button
            type="button"
            class="chip"
            :class="{ 'chip--on': nearby }"
            :aria-pressed="nearby"
            @click="nearby = !nearby"
          >Within 10km</button>
        </div>
      </div>

      <div v-if="feed.length" class="grid">
        <template v-for="item in feed" :key="item.id">
          <!-- Person card -->
          <article v-if="item.type === 'person'" class="card">
            <div class="card__media person" :style="{ '--a': item.colors[0], '--b': item.colors[1] }">
              <span class="person__initial">{{ item.name[0] }}</span>
              <span class="distance"><Icon name="pin" :size="12" /> {{ item.distanceKm }} km</span>
            </div>
            <div class="card__body">
              <h2 class="card__title">{{ item.name }}, {{ item.age }}</h2>
              <p class="card__text">{{ item.bio }}</p>
              <div class="tags">
                <span v-for="t in item.tags" :key="t">#{{ t }}</span>
              </div>
              <ActionButton
                class="card__action"
                :icon="connected.has(item.id) ? 'check' : 'userPlus'"
                :label="connected.has(item.id) ? 'Requested' : 'Connect'"
                @click="toggle(connected, item.id)"
              />
            </div>
          </article>

          <!-- Community card -->
          <article v-else class="card">
            <div class="card__media">
              <ActivityArt :kind="item.art" />
              <span class="distance"><Icon name="pin" :size="12" /> {{ item.distanceKm }} km</span>
            </div>
            <div class="card__body">
              <h2 class="card__title card__title--lg">{{ item.title }}</h2>
              <div class="members">
                <span class="avatar avatar--sm" style="--a: #f59f00; --b: #e8590c">A</span>
                <span class="avatar avatar--sm" style="--a: #be4bdb; --b: #7048e8">P</span>
                <span class="avatar avatar--sm avatar--count">+{{ item.members - 2 }}</span>
                <span class="members__count">{{ item.members + (joined.has(item.id) ? 1 : 0) }} members</span>
              </div>
              <ActionButton
                class="card__action"
                :icon="joined.has(item.id) ? 'check' : 'users'"
                :label="joined.has(item.id) ? 'Joined' : 'Join Group'"
                @click="toggle(joined, item.id)"
              />
            </div>
          </article>
        </template>
      </div>

      <div v-else-if="allItems.length" class="empty">
        <p>No people or activities match your filters.</p>
        <ActionButton icon="close" label="Clear filters" @click="clearFilters" />
      </div>

      <div v-else class="empty">
        <Icon name="compass" :size="36" />
        <p>No people or activities near you yet.</p>
        <ActionButton icon="plus" label="Create a community" @click="go('create')" />
      </div>
    </template>

    <section v-else class="placeholder">
      <h1 class="main__title">{{ activeLabel }}</h1>
      <div class="empty">
        <Icon :name="activeIcon" :size="36" />
        <p>{{ activeLabel }} is coming soon.</p>
        <ActionButton icon="back" label="Back to Discover" @click="go('discover')" />
      </div>
    </section>
  </BaseLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import ActionButton from '../../components/ActionButton.vue';
import ActivityArt from '../../components/ActivityArt.vue';
import BaseLayout from '../../components/BaseLayout.vue';
import Icon from '../../components/Icon.vue';
// Props come from HomePageView.get_page_props() in Django.
// people:  [{ id, name, age, bio, category, tags: [], distanceKm, colors: [a, b], map: { x, y } }]
// groups:  [{ id, title, category, art, members, distanceKm }]
// events:  [{ id, title, time, color }]
const props = defineProps({
  user: { type: Object, required: true },
  tab: { type: String, default: 'discover' },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  people: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
});

// Sections of this page; switching between them doesn't reload.
const TABS = {
  communities: { label: 'My Communities', icon: 'users' },
  chats: { label: 'Chats', icon: 'chat' },
  create: { label: 'Create Community', icon: 'plus' },
};
const LOCAL_TABS = ['discover', ...Object.keys(TABS)];
const CATEGORIES = ['Sports', 'Tech', 'Arts'];

const active = ref(props.tab);

const query = ref('');
const categories = ref(new Set());
const nearby = ref(false);
const connected = ref(new Set());
const joined = ref(new Set());

const activeLabel = computed(() => (TABS[active.value] || {}).label);
const activeIcon = computed(() => (TABS[active.value] || {}).icon);

// Switch section and keep the address bar in step (/?tab=chats can be bookmarked).
function go(tab) {
  active.value = tab;
  const url = tab === 'discover' ? props.homeUrl : `${props.homeUrl}?tab=${tab}`;
  if (url !== window.location.pathname + window.location.search) history.pushState({ tab }, '', url);
}

function onPopState() {
  const tab = new URLSearchParams(window.location.search).get('tab');
  active.value = TABS[tab] ? tab : 'discover';
}

onMounted(() => window.addEventListener('popstate', onPopState));
onBeforeUnmount(() => window.removeEventListener('popstate', onPopState));

// People and communities interleaved, then filtered by search + chips.
const allItems = computed(() => {
  const { people, groups } = props;
  const out = [];
  const len = Math.max(people.length, groups.length);
  for (let i = 0; i < len; i++) {
    if (people[i]) out.push({ ...people[i], type: 'person' });
    if (groups[i]) out.push({ ...groups[i], type: 'group' });
  }
  return out;
});

const feed = computed(() => {
  const q = query.value.trim().toLowerCase();
  return allItems.value.filter((item) => {
    if (categories.value.size && !categories.value.has(item.category)) return false;
    if (nearby.value && item.distanceKm > 10) return false;
    if (!q) return true;
    const haystack = [item.name, item.title, item.bio, item.category, ...(item.tags || [])]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

function toggle(set, value) {
  if (set.has(value)) set.delete(value);
  else set.add(value);
}

function clearFilters() {
  query.value = '';
  categories.value.clear();
  nearby.value = false;
}
</script>

<style scoped>
button {
  font: inherit;
  cursor: pointer;
}

.main__title {
  margin: 0 0 16px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--night-text);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--night-border);
  border-radius: 14px;
}

.search {
  display: flex;
  flex: 1 1 200px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  color: var(--night-muted);
}

.search input {
  width: 100%;
  height: 36px;
  font: inherit;
  color: var(--night-text);
  background: none;
  border: 0;
  outline: none;
}

.search input::placeholder {
  color: var(--night-muted);
}

.search:focus-within {
  color: var(--night-text);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--night-text);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 9px;
  transition: background 0.15s, border-color 0.15s;
}

.chip:hover {
  background: rgba(255, 255, 255, 0.12);
}

.chip--on {
  color: var(--night-900);
  background: var(--night-text);
  border-color: var(--night-text);
}

.chip--on:hover {
  background: #fff;
}

/* ---------- cards ---------- */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.card {
  display: flex;
  flex-direction: column;
  padding: 10px;
  background: var(--surface);
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(8, 19, 31, 0.14);
  transition: transform 0.15s, box-shadow 0.15s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(8, 19, 31, 0.18);
}

.card__media {
  position: relative;
  height: 150px;
  overflow: hidden;
  border-radius: 12px;
}

.person {
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.35), transparent 55%),
    linear-gradient(135deg, var(--a), var(--b));
}

.person__initial {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  font-size: 38px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
  border: 3px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%;
}

.distance {
  position: absolute;
  top: 8px;
  right: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(8, 19, 31, 0.55);
  border-radius: 999px;
}

.card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
  padding: 14px 6px 4px;
}

.card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.25;
}

.card__title--lg {
  font-size: 19px;
}

.card__text {
  margin: -4px 0 0;
  font-size: 14px;
  line-height: 1.4;
  color: var(--muted);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tags span {
  padding: 2px 9px;
  font-size: 12px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 7px;
}

/* Keep the card's button at the bottom, on the left. */
.card__action {
  align-self: flex-start;
  margin-top: auto;
}

.members {
  display: flex;
  align-items: center;
}

.members__count {
  margin-left: 18px;
  font-size: 14px;
  color: var(--muted);
}

/* ---------- empty / placeholder ---------- */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 48px 24px;
  text-align: center;
  color: var(--muted);
  background: var(--surface);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.empty p {
  margin: 0;
}

/* ---------- avatars (community cards) ---------- */
.avatar {
  display: grid;
  flex: none;
  place-items: center;
  width: 38px;
  height: 38px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--a), var(--b));
  border-radius: 50%;
}

.avatar--sm {
  width: 28px;
  height: 28px;
  margin-right: -8px;
  font-size: 11px;
  border: 2px solid var(--surface);
}

.avatar--count {
  font-size: 10px;
  color: var(--muted);
  background: var(--surface-muted);
}
</style>
